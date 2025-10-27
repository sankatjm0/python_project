import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageOps
import math

MAX_SIZE = 500

class ImageEditor:
    def __init__(self, root, image_path):
        self.root = root
        self.root.title("Chỉnh sửa ảnh (xoay, lật, crop như iPhone)")

        # Ảnh gốc
        self.original = Image.open(image_path).convert("RGBA")
        self.angle = 0
        self.flipped_h = False
        self.flipped_v = False

        # Resize ảnh về khung
        self.image = self.resize_to_fit(self.original)
        self.tk_image = ImageTk.PhotoImage(self.image)

        # Canvas
        self.canvas = tk.Canvas(root, width=MAX_SIZE, height=MAX_SIZE, bg="black")
        self.canvas.pack()

        self.image_on_canvas = self.canvas.create_image(MAX_SIZE//2, MAX_SIZE//2, anchor="center", image=self.tk_image)

        # Khung crop (mặc định full ảnh)
        self.crop_rect = [0, 0, MAX_SIZE, MAX_SIZE]
        self.crop_box = self.canvas.create_rectangle(*self.crop_rect, outline="yellow", width=2)

        # Thanh trượt xoay
        self.angle_scale = tk.Scale(root, from_=-180, to=180, orient="horizontal", label="Xoay (°)",
                                    command=self.update_rotation)
        self.angle_scale.pack(fill="x")

        # Nút điều khiển
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="⟲ Trái", command=lambda: self.rotate_fixed(-90)).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="⟳ Phải", command=lambda: self.rotate_fixed(90)).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="⇋ Lật ngang", command=self.flip_horizontal).grid(row=0, column=2, padx=5)
        tk.Button(btn_frame, text="⇅ Lật dọc", command=self.flip_vertical).grid(row=0, column=3, padx=5)
        tk.Button(btn_frame, text="✅ Xác nhận", command=self.save_crop).grid(row=0, column=4, padx=5)

        self.draw_all()

    # Giữ tỉ lệ ảnh trong khung
    def resize_to_fit(self, img):
        ratio = min(MAX_SIZE / img.width, MAX_SIZE / img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        return img.resize(new_size, Image.LANCZOS)

    def update_rotation(self, val):
        self.angle = int(val)
        self.draw_all()

    def rotate_fixed(self, deg):
        # Xoay từ ảnh gốc, không tích lũy lỗi
        self.angle = (self.angle + deg) % 360
        self.angle_scale.set(self.angle)
        self.draw_all()

    def flip_horizontal(self):
        self.flipped_h = not self.flipped_h
        self.draw_all()

    def flip_vertical(self):
        self.flipped_v = not self.flipped_v
        self.draw_all()

    def draw_all(self):
        img = self.original.copy()

        # Lật
        if self.flipped_h:
            img = ImageOps.mirror(img)
        if self.flipped_v:
            img = ImageOps.flip(img)

        # Xoay không expand (nằm trong khung cố định)
        img = img.rotate(self.angle, expand=False, resample=Image.BICUBIC)

        # Zoom để loại bỏ vùng đen do xoay
        angle_rad = abs(math.radians(self.angle % 90))
        if angle_rad != 0:
            scale_factor = 1 / (math.cos(angle_rad) + math.sin(angle_rad))
            zoom_w = int(img.width * scale_factor)
            zoom_h = int(img.height * scale_factor)
            img = img.resize((zoom_w, zoom_h), Image.LANCZOS)

        # Giữ tỉ lệ hiển thị trong khung
        img = self.resize_to_fit(img)

        # Vẽ ra canvas
        self.tk_image = ImageTk.PhotoImage(img)
        self.canvas.itemconfig(self.image_on_canvas, image=self.tk_image)
        self.image = img

        # Cập nhật khung crop (full ảnh)
        w, h = img.width, img.height
        self.crop_rect = [0, 0, w, h]
        self.canvas.coords(self.crop_box, *self.crop_rect)

    def save_crop(self):
        x1, y1, x2, y2 = [int(v) for v in self.crop_rect]
        cropped = self.image.crop((x1, y1, x2, y2))
        save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if save_path:
            cropped.convert("RGB").save(save_path)
            messagebox.showinfo("Thành công", f"Ảnh đã được lưu tại:\n{save_path}")


# ---------- Chạy thử ----------
if __name__ == "__main__":
    root = tk.Tk()
    img_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg;*.png;*.jpeg")])
    if img_path:
        app = ImageEditor(root, img_path)
        root.mainloop()
