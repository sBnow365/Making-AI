import cv2
import numpy as np
import pytesseract
from PIL import Image
import torch
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

# pytesseract: A Python wrapper for Tesseract, an OCR (Optical Character Recognition) engine that extracts text from images.
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# load TrOCR model and processor globally once (for handwritten OCR)
processor = TrOCRProcessor.from_pretrained('microsoft/trocr-small-handwritten')
model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-small-handwritten')

# optical character recognition ocr works better on grayscale
def preprocess_image(image_path):
    image = cv2.imread(image_path)
    if image is None:
        print("Could not load the image. Check the path!")
        return None, None, None

    # i need the grayscale image to later extract features
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # contrast ko better karna hai via CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)

    # Apply Otsu's thresholding
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Optional: clean up small noise with a morphological opening -> which removes small noise by first eroding and then dilating the image.
    kernel = np.ones((1, 1), np.uint8)
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

    # return the images 
    return gray, cleaned, image  

def extract_text(image):
    custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
    # hamhe configurations tessaract ko provide karni hai hence--->oem->ocr engine mode
    # page segmentation mode
    # preserve spaces between the word
    try:
        text = pytesseract.image_to_string(image, config=custom_config)
        return text.strip()
    except Exception as e:
        print("Error during OCR:", e)
        return ""

def extract_handwritten_text_by_line(image_path):
    try:
        print(f"[INFO] Loading image: {image_path}")
        image = cv2.imread(image_path)
        if image is None:
            print("[ERROR] Failed to load image.")
            return ""

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Dilate to connect characters into lines
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 5))
        dilated = cv2.dilate(thresh, kernel, iterations=2)

        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[1])

        print(f"[INFO] Found {len(contours)} line candidates")

        lines = []

        for i, cnt in enumerate(contours):
            x, y, w, h = cv2.boundingRect(cnt)
            if h < 15 or w < 50:
                continue

            print(f"[INFO] Processing line {i+1}: x={x}, y={y}, w={w}, h={h}")

            line_img = image[y:y+h, x:x+w]
            pil_img = Image.fromarray(cv2.cvtColor(line_img, cv2.COLOR_BGR2RGB)).resize((384, 384))

            pixel_values = processor(images=pil_img, return_tensors="pt").pixel_values
            generated_ids = model.generate(pixel_values)
            text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            lines.append(text.strip())

        if not lines:
            print("[WARN] No valid lines found.")
            return "No handwriting detected."

        return "\n".join(lines)

    except Exception as e:
        print(f"[ERROR] Exception in extract_handwritten_text_by_line: {e}")
        return "Error during handwriting OCR."

def process_and_extract(image_path):
    # ye function sirf printed text ke liye tha, ab bhi waisa hi kaam karega
    gray, processed, original = preprocess_image(image_path)
    if processed is not None:       # image type agar wrong hoga yaha check
        text = extract_text(processed)
        return gray, processed, original, text
    return None, None, None, None

def handle_user_choice(image_path, choice):
    """
    choice: 'printed' or 'handwritten'
    """
    if choice == 'printed':
        # printed text ke liye existing flow
        gray, processed, original, text = process_and_extract(image_path)
        return {'gray': gray, 'processed': processed, 'original': original, 'text': text}
    elif choice == 'handwritten':
        text = extract_handwritten_text_by_line(image_path)
        return {'gray': None, 'processed': None, 'original': cv2.imread(image_path), 'text': text}

    else:
        raise ValueError("Invalid choice. Must be 'printed' or 'handwritten'.")
