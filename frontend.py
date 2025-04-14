import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import cv2
import backend
from table_extractor import extract_tables_from_image, cells_to_csv
from table_extractor import extract_tables_from_image, cells_to_csv
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

class OCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OCR Document Scanner")
        self.root.geometry("1000x750")
        self.root.geometry("1000x750")
        self.root.configure(bg="white")

        self.image_path = None
        self.processed_image = None
        self.gray_image = None

        # Sidebar Frame
        sidebar_frame = tk.Frame(root, bg="white", width=200, height=750)
        sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.upload_btn = tk.Button(sidebar_frame, text="📂 Upload Image", command=self.upload_image)
        self.upload_btn.pack(pady=5, fill=tk.X)

        self.process_btn = tk.Button(sidebar_frame, text="🛠 Process Image", command=self.process_image, state=tk.DISABLED)
        self.process_btn.pack(pady=5, fill=tk.X)

        self.handwriting_btn = tk.Button(sidebar_frame, text="📝 Read Handwriting", command=self.process_handwriting_image, state=tk.DISABLED)
        self.handwriting_btn.pack(pady=5, fill=tk.X)

        self.extract_table_btn = tk.Button(sidebar_frame, text="🧾 Extract Table", command=self.extract_table, state=tk.DISABLED)
        self.extract_table_btn.pack(pady=5, fill=tk.X)

        # Main Frame for image and text display
        main_frame = tk.Frame(root, bg="white")
        main_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Image Display Frame
        img_frame = tk.Frame(main_frame, bg="white")
        img_frame.pack(pady=20, fill=tk.X)

        self.orig_label = tk.Label(img_frame, text="Original Image", fg="black", font=("Arial", 12, "bold"))
        self.orig_label.grid(row=0, column=0, padx=20)

        self.proc_label = tk.Label(img_frame, text="Processed Image", fg="black", font=("Arial", 12, "bold"))
        self.proc_label.grid(row=0, column=1, padx=20)

        self.orig_img_display = tk.Label(img_frame, bg="white")
        self.orig_img_display.grid(row=1, column=0, padx=20)

        self.proc_img_display = tk.Label(img_frame, bg="white")
        self.proc_img_display.grid(row=1, column=1, padx=20)

        # Text Area for extracted text
        self.text_area = scrolledtext.ScrolledText(main_frame, height=10, width=80, wrap=tk.WORD)
        self.text_area.pack(pady=20)

        # Save and Copy Buttons
        save_button_frame = tk.Frame(main_frame, bg="white")
        save_button_frame.pack(pady=10)

        self.save_text_btn = tk.Button(save_button_frame, text="💾 Save Text", command=self.save_text, state=tk.DISABLED)
        self.save_text_btn.grid(row=0, column=0, padx=5)

        self.copy_text_btn = tk.Button(save_button_frame, text="📋 Copy Text", command=self.copy_text, state=tk.DISABLED)
        self.copy_text_btn.grid(row=0, column=1, padx=5)

        self.save_img_btn = tk.Button(save_button_frame, text="💾 Save Image", command=self.save_image, state=tk.DISABLED)
        self.save_img_btn.grid(row=0, column=2, padx=5)

        self.save_pdf_btn = tk.Button(save_button_frame, text="📄 Save as PDF", command=self.save_as_pdf, state=tk.DISABLED)
        self.save_pdf_btn.grid(row=0, column=3, padx=5)

    def upload_image(self):
        # Upload and display the original image
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if not file_path:
            return
        
        self.image_path = file_path
        self.display_image(file_path, self.orig_img_display)

        self.process_btn.config(state=tk.NORMAL)
        self.handwriting_btn.config(state=tk.NORMAL)
        self.extract_table_btn.config(state=tk.NORMAL)

    def process_handwriting_image(self):
        if not self.image_path:
            return

        result = backend.handle_user_choice(self.image_path, 'handwritten')
        text = result['text']
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert(tk.END, text)

        self.save_text_btn.config(state=tk.NORMAL)
        self.copy_text_btn.config(state=tk.NORMAL)
        self.save_img_btn.config(state=tk.DISABLED)  # No processed image for handwritten
        self.save_pdf_btn.config(state=tk.NORMAL)

    def extract_table(self):
        if not self.image_path:
            messagebox.showerror("Error", "No image to extract table from.")
            return

        output_img, table_cells = extract_tables_from_image(self.image_path)

        if not table_cells:
            messagebox.showinfo("Info", "No tables detected.")
            return

        # Table Viewer Window
        table_window = tk.Toplevel(self.root)
        table_window.title("Extracted Table Text")

        table_text = tk.Text(table_window, wrap=tk.WORD, width=80, height=25)
        table_text.pack(padx=10, pady=10)

        sorted_cells = sorted(table_cells, key=lambda item: (item[0][1], item[0][0]))
        last_y = -1000
        for ((x, y), text) in sorted_cells:
            if abs(y - last_y) > 15:
                table_text.insert(tk.END, "\n")
            table_text.insert(tk.END, text + "\t")
            last_y = y

        save_csv = messagebox.askyesno("Save Table", "Do you want to save the table as CSV?")
        if save_csv:
            from datetime import datetime
            filename = f"table_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            cells_to_csv(table_cells, filename)
            messagebox.showinfo("Saved", f"Table saved as {filename}")

    def process_image(self):
        # General image preprocessing (for normal OCR)
        if not self.image_path:
            return


        gray, processed, _, text = backend.process_and_extract(self.image_path)

        if processed is not None:
            self.gray_image = gray
            self.processed_image = processed

            cv2.imwrite("processed_output.png", processed)
            self.display_image("processed_output.png", self.proc_img_display)

            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, text)

            self.save_text_btn.config(state=tk.NORMAL)
            self.copy_text_btn.config(state=tk.NORMAL)
            self.save_img_btn.config(state=tk.NORMAL)
            self.save_pdf_btn.config(state=tk.NORMAL)
            self.save_text_btn.config(state=tk.NORMAL)
            self.copy_text_btn.config(state=tk.NORMAL)
            self.save_img_btn.config(state=tk.NORMAL)
            self.save_pdf_btn.config(state=tk.NORMAL)
        else:
            messagebox.showerror("Error", "Could not process the image.")

    def display_image(self, path, label):
        # Display an image in a Tkinter label
        img = Image.open(path)
        img.thumbnail((400, 400))
        img = ImageTk.PhotoImage(img)
        label.config(image=img)
        label.image = img  # Keep a reference

    def save_text(self):
        # Save extracted text to a file
        file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 filetypes=[("Text files", "*.txt")])
        if not file_path:
            return
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.text_area.get("1.0", tk.END))

    def copy_text(self):
        # Copy text to clipboard
        text = self.text_area.get("1.0", tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()

    def save_image(self):
        # Save the processed image
        if self.processed_image is None:
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if file_path:
            cv2.imwrite(file_path, self.processed_image)

    def save_as_pdf(self):
        # Save extracted text as a PDF
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if not file_path:
            return
        c = canvas.Canvas(file_path, pagesize=letter)
        text = self.text_area.get("1.0", tk.END)
        lines = text.strip().split('\n')
        y = 750
        for line in lines:
            c.drawString(30, y, line)
            y -= 15
            if y < 50:
                c.showPage()
                y = 750
        c.save()


if __name__ == "__main__":
    root = tk.Tk()
    app = OCRApp(root)
    root.mainloop()
