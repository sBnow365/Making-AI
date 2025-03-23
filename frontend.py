import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import cv2
import backend
import os

class OCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OCR Document Scanner")
        self.root.geometry("1000x700")
        self.root.configure(bg="white")

        self.image_path = None
        self.processed_image = None
        self.gray_image = None

        #for actions with image and extracted text
        button_frame = tk.Frame(root, bg="white")
        button_frame.pack(pady=10)

        self.upload_btn = tk.Button(button_frame, text="📂 Upload Image", command=self.upload_image)
        self.upload_btn.grid(row=0, column=0, padx=5)

        self.process_btn = tk.Button(button_frame, text="🛠 Process Image", command=self.process_image, state=tk.DISABLED)
        self.process_btn.grid(row=0, column=1, padx=5)

        #display images
        img_frame = tk.Frame(root, bg="white")
        img_frame.pack()

        self.orig_label = tk.Label(img_frame, text="Original Image", fg="black", font=("Arial", 12, "bold"))
        self.orig_label.grid(row=0, column=0, padx=20)

        self.proc_label = tk.Label(img_frame, text="Processed Image", fg="black", font=("Arial", 12, "bold"))
        self.proc_label.grid(row=0, column=1, padx=20)

        self.orig_img_display = tk.Label(img_frame, bg="white")
        self.orig_img_display.grid(row=1, column=0, padx=20)

        self.proc_img_display = tk.Label(img_frame, bg="white")
        self.proc_img_display.grid(row=1, column=1, padx=20)

        # text area
        self.text_area = scrolledtext.ScrolledText(root, height=20, width=90, wrap=tk.WORD)
        self.text_area.pack(pady=20)

    #this opens a dialog and asks the user to enter file form their system
    def upload_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        #the allowed extensions 
        if not file_path:
            return
        
        self.image_path = file_path
        self.display_image(file_path, self.orig_img_display)

        self.process_btn.config(state=tk.NORMAL)

    def process_image(self):
        if not self.image_path:
            return
        
        #using method from backend imported
        gray, processed, _, text = backend.process_and_extract(self.image_path)

        if processed is not None:
            self.gray_image = gray
            self.processed_image = processed

            cv2.imwrite("processed_output.png", processed)
            self.display_image("processed_output.png", self.proc_img_display)

            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, text)

        else:
            messagebox.showerror("Error", "Could not process image.")

    def display_image(self, file_path, widget):
        image = Image.open(file_path)
        image = image.resize((300, 200))
        img = ImageTk.PhotoImage(image)

        widget.config(image=img, text="")
        widget.image = img  

if __name__ == "__main__":
    root = tk.Tk()
    app = OCRApp(root)
    root.mainloop()
