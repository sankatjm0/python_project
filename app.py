from tkinter import *
from tkinter import filedialog, Toplevel, messagebox
from PIL import Image, ImageTk, ImageEnhance, ImageOps
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

root = Tk()
root.title('Read text from image')
root.minsize(width=1200, height=800)
normal_photo = None
dark_photo = None

def toggle_fullscreen(event=None):
    is_fullscreen = root.attributes('-fullscreen')
    root.attributes('-fullscreen', not is_fullscreen)

def on_hover(event):
    if dark_photo:
        image_label.config(image=dark_photo)
    upload_text.lift()  
    upload_text.place(relx=0.28, rely=0.5) 

def on_leave(event):
    if normal_photo:
        image_label.config(image=normal_photo)
    upload_text.place_forget()

def generate_pdf_from_text(text_content, file_path):
    c = canvas.Canvas(file_path, pagesize=letter)
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

def open_editor(image_path):
    global current_image
    editor = Toplevel(root)
    editor.geometry("800x700")
    editor.resizable(False, False)
    editor.title("Edit photo - Rotate, Flip, Crop")

    original_img = Image.open(image_path).convert("RGBA")
    working_img = original_img.copy()

    angle_var = DoubleVar(value=0)
    flip_x = BooleanVar(value=False)
    flip_y = BooleanVar(value=False)

    drag_edge = None
    drag_start = None
    max_size = 600

    def scale_image(img):
        w, h = img.size
        scale = min(max_size / w, max_size / h, 1)
        return img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    display_img = scale_image(working_img)
    crop_box = [0, 0, display_img.width, display_img.height]

    canvas = Canvas(editor, bg=None, width=display_img.width, height=display_img.height, cursor="tcross")

    def draw_all():
        global tk_img, rotated_display

        temp = working_img.copy()
        if flip_x.get():
            temp = ImageOps.mirror(temp)
        if flip_y.get():
            temp = ImageOps.flip(temp)

        angle = angle_var.get()
        rotated_display = temp.rotate(-angle, expand=False)
        scaled = scale_image(rotated_display)

        tk_img = ImageTk.PhotoImage(scaled)
        canvas.img_ref = tk_img
        canvas.delete("all")

        canvas.config(width=scaled.width, height=scaled.height)
        canvas.create_image(0, 0, image=tk_img, anchor="nw")

        x0, y0, x1, y1 = crop_box
        canvas.create_rectangle(x0, y0, x1, y1, outline="red", width=2)

    def detect_edge(event):
        x, y = event.x, event.y
        x1, y1, x2, y2 = crop_box
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

    def start_drag(event):
        nonlocal drag_edge, drag_start
        drag_edge = detect_edge(event)
        drag_start = (event.x, event.y)

    def do_drag(event):
        nonlocal crop_box, drag_start
        if drag_edge is None or drag_start is None:
            return
        dx = event.x - drag_start[0]
        dy = event.y - drag_start[1]
        x1, y1, x2, y2 = crop_box
        if drag_edge == "left":
            x1 = max(0, min(x1 + dx, x2 - 10))
        elif drag_edge == "right":
            x2 = min(display_img.width, max(x2 + dx, x1 + 10))
        elif drag_edge == "top":
            y1 = max(0, min(y1 + dy, y2 - 10))
        elif drag_edge == "bottom":
            y2 = min(display_img.height, max(y2 + dy, y1 + 10))
        crop_box = [x1, y1, x2, y2]
        drag_start = (event.x, event.y)
        draw_all()

    def end_drag(event):
        nonlocal drag_edge, drag_start
        drag_edge = None
        drag_start = None

    def confirm_crop():
        nonlocal display_img

        scale_x = original_img.width / display_img.width
        scale_y = original_img.height / display_img.height

        temp = original_img.copy()
        if flip_x.get():
            temp = ImageOps.mirror(temp)
        if flip_y.get():
            temp = ImageOps.flip(temp)

        angle = int(angle_var.get()) % 360
        if angle in [90, 270]:
            temp = temp.transpose(Image.ROTATE_270 if angle == 90 else Image.ROTATE_90)
        elif angle != 0:
            temp = temp.rotate(-angle, expand=False)

        x1, y1, x2, y2 = crop_box
        rx1 = int(x1 * scale_x)
        ry1 = int(y1 * scale_y)
        rx2 = int(x2 * scale_x)
        ry2 = int(y2 * scale_y)

        rx1, ry1, rx2, ry2 = map(int, [rx1, ry1, rx2, ry2])
        cropped = temp.crop((rx1, ry1, rx2, ry2))

        display_img = cropped.convert("RGB")
        load_and_display_image_object(display_img)
        editor.destroy()
        messagebox.showinfo("Image Edited", "The image has been edited and loaded.")

    def rotate_fixed(deg):
        nonlocal working_img, display_img, crop_box
        working_img = working_img.rotate(deg, expand=True)
        draw_all()

    control = Frame(editor)
    control.pack(pady=5)
    Button(control, text="Browse", command=upload_image).pack(side="left", padx=5)
    Label(control, text="Rotate (°):").pack(side="left")
    Scale(control, from_=-90, to=90, orient=HORIZONTAL, length=250,
          variable=angle_var, command=lambda e: draw_all()).pack(side="left", padx=5)
    Button(control, text="⟲ Left", command=lambda: rotate_fixed(90)).pack(side="left", padx=5)
    Button(control, text="⟳ Right", command=lambda: rotate_fixed(-90)).pack(side="left", padx=5)
    Button(control, text="⇋ Horizontal Flip", command=lambda: [flip_x.set(not flip_x.get()), draw_all()]).pack(side="left", padx=5)
    Button(control, text="⇅ Vertical Flip", command=lambda: [flip_y.set(not flip_y.get()), draw_all()]).pack(side="left", padx=5)
    Button(control, text="Submit", command=confirm_crop).pack(side="left", padx=10)
    canvas.pack(padx=10, pady=10)

    canvas.bind("<ButtonPress-1>", start_drag)
    canvas.bind("<B1-Motion>", do_drag)
    canvas.bind("<ButtonRelease-1>", end_drag)

    draw_all()

def load_and_display(file_path):
    global normal_photo, dark_photo, current_image
    current_image = Image.open(file_path)
    load_and_display_image_object(current_image)

def load_and_display_image_object(img):
    global normal_photo, dark_photo

    img = img.copy()
    img.thumbnail((700, 700))
    normal_photo = ImageTk.PhotoImage(img)

    enhancer = ImageEnhance.Brightness(img)
    dark_img = enhancer.enhance(0.5)
    dark_photo = ImageTk.PhotoImage(dark_img)

    image_label.config(image=normal_photo)
    image_label.image = normal_photo
    
def gtc():
    global content
    content = text_widget.get("1.0", "end-1c")
    root.clipboard_clear()
    root.clipboard_append(content)
    status_label.config(text="Text copied to clipboard!")

def upload_image():
    f_types = [('Image Files', '*.jpg *.png *.webp *.jpeg')] 
    filename = filedialog.askopenfilename(filetypes=f_types)

    if filename:
        try:
            open_editor(filename)
        except Exception as e:
            print(f"Error loading image: {e}")

upload_text = Label(text="Upload Image", font=('Arial', 10))
status_label = Label(root, text="", fg="green", font=('Arial', 10))
status_label.place(anchor='n', relwidth=0.3, relx=0.8, rely=0.85)
text_widget = Text()
text_widget.insert(END, "Your extracted text will appear here.")
text_widget.place(anchor='s', relwidth=0.3, relheight=0.5, relx=0.8, rely=0.65)
esc = Label(text="Press Esc to exit full screen.", font=("Arial", 10))
esc.place(anchor='center', relx=0.5, rely=0.97) 
Label(text='Upload your image to extract text', font=('Arial', 14)).place(anchor='center', relx=0.5, rely=0.05)  
Button(text='Convert', command=lambda: gtc()).place(anchor='n', relwidth=0.3, relx=0.8, rely=0.7) 
Button(text='Copy', command=lambda: gtc()).place(anchor='n', relwidth=0.3, relx=0.8, rely=0.75) 
Button(text='Download as PDF', width=25, command=lambda: save_to_file()).place(anchor='n', relwidth=0.3, relx=0.8, rely=0.8)  


image_label = Button(relief='groove', command=upload_image)
image_label.place(relwidth=0.55, relheight=0.8, anchor='e', relx=0.6, rely=0.5) 
image_label.bind("<Enter>", on_hover)
image_label.bind("<Leave>", on_leave)
root.bind('<Escape>', toggle_fullscreen)

root.mainloop()