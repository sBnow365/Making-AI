import cv2
import numpy as np
import pytesseract
#pytesseract: A Python wrapper for Tesseract, an OCR (Optical Character Recognition) engine that extracts text from images.
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

#optical character recognition ocr works better on grayscale
def preprocess_image(image_path):
    image = cv2.imread(image_path)
    if image is None:
        print("Could not load the image. Check the path!")
        return None, None

    # i need the grayscale image to later extract features
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    #contrast ko better karna hai via  CLAHE (Contrast Limited Adaptive Histogram Equalization)
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
    #hamhe configurations tessaract ko provide karni hai hence--->oem->ocr engine mode
    # page segmentation mode
    # preserve spaces between the word
    try:
        text = pytesseract.image_to_string(image, config=custom_config)
        return text.strip()
    except Exception as e:
        print("Error during OCR:", e)
        return ""

def process_and_extract(image_path):
    gray, processed, original = preprocess_image(image_path)
    if processed is not None:       #image type agar wrong hoga yaha check
        text = extract_text(processed)
        return gray, processed, original, text
    return None, None, None, None
