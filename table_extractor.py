import cv2
import pytesseract
import numpy as np
import pandas as pd

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_tables_from_image(image_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(~gray, 150, 255, cv2.THRESH_BINARY)

    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))

    detect_horizontal = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    detect_vertical = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel, iterations=2)

    table_mask = cv2.add(detect_horizontal, detect_vertical)

    contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cells_data = []

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w < 50 or h < 20:
            continue

        cell_img = image[y:y+h, x:x+w]
        cell_gray = cv2.cvtColor(cell_img, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(cell_gray, config='--psm 6').strip()
        cells_data.append(((x, y), text))

    return image, cells_data

def cells_to_csv(cells_data, output_csv="table.csv"):
    cells_data.sort(key=lambda k: (k[0][1], k[0][0]))
    rows = []
    current_row = []
    last_y = None

    for (x, y), text in cells_data:
        if last_y is None or abs(y - last_y) < 20:
            current_row.append(text)
        else:
            rows.append(current_row)
            current_row = [text]
        last_y = y
    rows.append(current_row)

    df = pd.DataFrame(rows)
    df.to_csv(output_csv, index=False)
