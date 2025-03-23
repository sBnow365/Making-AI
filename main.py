import cv2
import numpy as np
#pytesseract: A Python wrapper for Tesseract, an OCR (Optical Character Recognition) engine that extracts text from images.
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

#optical character recognition ocr works better on grayscale

def preprocess_image(image):
    #i need the grayscale image to later extract features
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    #contrast ko better karna hai via  CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)
    # Apply Otsu's thresholding
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # Optional: clean up small noise with a morphological opening -> which removes small noise by first eroding and then dilating the image.
    kernel = np.ones((1, 1), np.uint8)
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    
    return cleaned  #returning the cleaned image



if _name_ == "_main_":
    image_path = "pic1.png"
    processed, original = scan_document(image_path)
    if processed is not None:
        cv2.imwrite("processed_output.png", processed)
        print("Processed image saved as 'processed_output.png'.")
        
        text = extract_text(processed)
        with open("extracted_text.txt", "w", encoding="utf-8") as f:
            f.write(text)# saving the extracted text to extracted text.txt
        print("Extracted text saved to 'extracted_text.txt'.")
        
        print("\nOCR Text Extraction Result:")
        print(text)
        
        cv2.imshow("Original Document", original)
        cv2.imshow("Processed Document", processed)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

