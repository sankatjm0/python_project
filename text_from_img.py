from tkinter import *
from tkinter import filedialog, Toplevel, messagebox
from PIL import Image, ImageTk, ImageEnhance, ImageOps
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

root = Tk()
root.title('Read text from image')
root.minsize(width=1200, height=800)
dark_photo = None
saved_image = None
angle_var = DoubleVar(value=0)
flip_x = BooleanVar(value=False)
flip_y = BooleanVar(value=False)
drag_edge = None
drag_start = None
max_size = 600
scale_factor = 1

def get_canvas_size():
    """Lấy kích thước thực tế của canvas (cần gọi sau khi canvas đã render)"""
    root.update_idletasks()  # Đảm bảo canvas đã được layout
    return image_label.winfo_width(), image_label.winfo_height()

def scale_image(img, canvas_width, canvas_height):
    """Scale ảnh để vừa khít canvas, giữ aspect ratio, zoom lớn nhất"""
    img_width, img_height = img.size
    scale_x = canvas_width / img_width
    scale_y = canvas_height / img_height
    scale = min(scale_x, scale_y)  # Chọn scale nhỏ hơn để vừa khít (không bị cắt)
    new_width = int(img_width * scale)
    new_height = int(img_height * scale)
    return img.resize((new_width, new_height), Image.LANCZOS), scale

def upload_image():
    f_types = [('Image Files', '*.jpg *.png *.webp *.jpeg')] 
    filename = filedialog.askopenfilename(filetypes=f_types)
    if filename:
        try:
            global original_img, working_img, display_img, crop_box, scale_factor
            original_img = Image.open(filename).convert("RGBA")
            working_img = original_img.copy()
            crop_box = [0, 0, working_img.width, working_img.height]
            scale_factor = 1
            draw_all()
        except Exception as e:
            print(f"Error loading image: {e}")

def toggle_fullscreen(event=None):
    is_fullscreen = root.attributes('-fullscreen')
    root.attributes('-fullscreen', not is_fullscreen)

def generate_pdf_from_text(text_content, file_path):
    c = image_label.Canvas(file_path, pagesize=letter)
    textobject = c.beginText()
    textobject.setTextOrigin(50, 750)
    textobject.setFont("Helvetica", 12)

    for line in text_content.splitlines():
        textobject.textLine(line)

    c.drawText(textobject)
    c.save()

def save_to_file():
    file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")], title="Save PDF File")
    if file_path:
        try:
            content = text_widget.get("1.0", "end-1c")
            generate_pdf_from_text(content, file_path)
            status_label.config(text="Download successfully!")
        except Exception as e:
            status_label.config(text=f"Error saving file: {str(e)}")

def draw_all():
    global tk_img, rotated_display, crop_box, scale_factor, canvas_width, canvas_height
    temp = working_img.copy()
    if flip_x.get():
        temp = ImageOps.mirror(temp)
    if flip_y.get():
        temp = ImageOps.flip(temp)
    angle = angle_var.get()
    rotated_display = temp.rotate(-angle, expand=False)
    
    # Lấy kích thước canvas và scale ảnh
    canvas_width, canvas_height = get_canvas_size()
    scaled, scale_factor = scale_image(rotated_display, canvas_width, canvas_height)
    
    tk_img = ImageTk.PhotoImage(scaled)
    image_label.img_ref = tk_img
    image_label.delete("all")
    
    # Căn giữa ảnh trên canvas
    image_label.create_image(canvas_width // 2, canvas_height // 2, image=tk_img, anchor='center')
    
    # Scale crop_box để vẽ trên ảnh scaled
    x0, y0, x1, y1 = [coord * scale_factor for coord in crop_box]
    image_label.create_rectangle(x0, y0, x1, y1, outline="red", width=2)

def detect_edge(event):
    global crop_box
    canvas_width, canvas_height = get_canvas_size()
    scaled_crop = [coord * scale_factor for coord in crop_box]
    x, y = event.x, event.y
    x1, y1, x2, y2 = scaled_crop
    margin = 8
    if abs(x - x1) < margin and y1 < y < y2:
        return "left"
    elif abs(x - x2) < margin and y1 < y < y2:
        return "right"
    elif abs(y - y1) < margin and x1 < x < x2:
        return "top"
    elif abs(y - y2) < margin and x1 < x < x2:
        return "bottom"
    else:
        return None

def do_drag(event):
    global crop_box, drag_start
    if drag_edge is None or drag_start is None:
        return
    dx = (event.x - drag_start[0]) / scale_factor  # Chia scale_factor để chuyển về tọa độ gốc
    dy = (event.y - drag_start[1]) / scale_factor
    x1, y1, x2, y2 = crop_box
    if drag_edge == "left":
        x1 = max(0, min(x1 + dx, x2 - 10))
    elif drag_edge == "right":
        x2 = min(working_img.width, max(x2 + dx, x1 + 10))
    elif drag_edge == "top":
        y1 = max(0, min(y1 + dy, y2 - 10))
    elif drag_edge == "bottom":
        y2 = min(working_img.height, max(y2 + dy, y1 + 10))
    crop_box = [x1, y1, x2, y2]
    drag_start = (event.x, event.y)
    draw_all()

def start_drag(event):
    global drag_edge, drag_start
    drag_edge = detect_edge(event)
    drag_start = (event.x, event.y)

def end_drag(event):
    global drag_edge, drag_start
    drag_edge = None
    drag_start = None

def confirm_crop():
    global working_img, display_img, crop_box
    # Dùng working_img (đã tích lũy chỉnh sửa) thay vì original_img
    temp = working_img.copy()
    
    # Áp dụng thêm flip/xoay từ slider (nếu có, vì working_img đã có từ nút)
    if flip_x.get():
        temp = ImageOps.mirror(temp)
    if flip_y.get():
        temp = ImageOps.flip(temp)
    angle = int(angle_var.get()) % 360
    if angle in [90, 270]:
        temp = temp.transpose(Image.ROTATE_270 if angle == 90 else Image.ROTATE_90)
    elif angle != 0:
        temp = temp.rotate(-angle, expand=False)
    
    # Crop trực tiếp từ temp (working_img đã chỉnh sửa)
    x1, y1, x2, y2 = crop_box
    cropped = temp.crop((x1, y1, x2, y2))
    
    # Cập nhật working_img với ảnh đã crop
    working_img = cropped.convert("RGBA")
    crop_box = [0, 0, working_img.width, working_img.height]  # Reset crop_box
    
    # Reset các biến chỉnh sửa để tránh chồng chéo
    angle_var.set(0)
    flip_x.set(False)
    flip_y.set(False)
    
    draw_all()
    messagebox.showinfo("Image Edited", "The image has been edited and loaded.")

def rotate_fixed(deg):
    global working_img
    working_img = working_img.rotate(deg, expand=True)
    angle_var.set(0)  # Reset slider
    draw_all()
    
def gtc():
    global content
    content = text_widget.get("1.0", "end-1c")
    root.clipboard_clear()
    root.clipboard_append(content)
    status_label.config(text="Text copied to clipboard!")

upload_text = Label(text="Upload Image", font=('Arial', 10))
status_label = Label(root, text="", fg="green", font=('Arial', 10))
status_label.place(anchor='n', relwidth=0.3, relx=0.8, rely=0.85)
text_widget = Text()
text_widget.insert(END, "Your extracted text will appear here.")
text_widget.place(anchor='s', relwidth=0.3, relheight=0.5, relx=0.8, rely=0.65)
esc = Label(text="Press Esc to exit full screen.", font=("Arial", 10))
esc.place(anchor='center', relx=0.5, rely=0.97) 
Label(text='Upload your image to extract text', font=('Arial', 14)).place(anchor='center', relx=0.5, rely=0.05)  
Button(text='Convert').place(anchor='n', relwidth=0.3, relx=0.8, rely=0.7) 
Button(text='Copy', command=lambda: gtc()).place(anchor='n', relwidth=0.3, relx=0.8, rely=0.75) 
Button(text='Download as PDF', width=25, command=lambda: save_to_file()).place(anchor='n', relwidth=0.3, relx=0.8, rely=0.8)  
Button(text="Upload", command=lambda: upload_image()).place(anchor='sw', relx=0.05, rely=0.1)
Label(text="Rotate (°):").place(anchor='nw', relx=0.1, rely=0.9)
Scale(from_=-90, to=90, orient=HORIZONTAL, length=250,
        variable=angle_var, command=lambda e: draw_all()).place(anchor='nw', relx=0.15, rely=0.88)
Button(text="⟲ Left", command=lambda: rotate_fixed(90)).place(anchor='nw', relx=0.37, rely=0.9)
Button(text="⟳ Right", command=lambda: rotate_fixed(-90)).place(anchor='nw', relx=0.41, rely=0.9)
Button(text="⇋ Horizontal Flip", command=lambda: [flip_x.set(not flip_x.get()), draw_all()]).place(anchor='nw', relx=0.457, rely=0.9)
Button(text="⇅ Vertical Flip", command=lambda: [flip_y.set(not flip_y.get()), draw_all()]).place(anchor='nw', relx=0.543, rely=0.9)
Button(text="Submit", command=confirm_crop).place(anchor='nw', relx=0.6, rely=0.9)


image_label = Canvas(bg=None, border=5, borderwidth=2, relief="ridge")
image_label.place(relwidth=0.55, relheight=0.8, anchor='e', relx=0.6, rely=0.5) 
image_label.bind("<ButtonPress-1>", start_drag)
image_label.bind("<B1-Motion>", do_drag)
image_label.bind("<ButtonRelease-1>", end_drag)
root.bind('<Escape>', toggle_fullscreen)

root.mainloop()