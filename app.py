from tkinter import *
from tkinter import filedialog, messagebox, font
import tkinter as tk
from PIL import Image, ImageTk, ImageOps
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
import sys
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    from handle_image.detection import find_line_groups, crop_and_save_lines, draw_debug_boxes
    from handle_image.recognition import recognize_text_from_folder
    from utils.clean_folder import clean_folder
except ImportError as e:
    messagebox.showerror("Lỗi Import", f"Không thể import module xử lý ảnh: {e}\nKiểm tra cấu trúc thư mục và file __init__.py.")

root = Tk()
font_path = os.path.join(os.path.dirname(__file__), "dejavu-sans-ttf-2.37", "dejavu-sans-ttf-2.37", "ttf", "DejaVuSans.ttf")
font_path = os.path.abspath(font_path)
pdfmetrics.registerFont(TTFont('DejaVu', font_path, subfontIndex=0))
default_font = font.nametofont("TkDefaultFont")
default_font.config(family="Segoe Script", size=10)
root.config(bg='#F7FFF7')
root.title('Read text from image')
root.minsize(width=1500, height=800)
dark_photo = None
saved_image = None
angle_var = DoubleVar(value=0)
flip_x = BooleanVar(value=False)
flip_y = BooleanVar(value=False)
drag_edge = None
drag_start = None
max_size = 600
scale_factor = 1

original_img = None
working_img = None 
display_img = None
tk_img = None
crop_box = None 

def get_canvas_size():
    root.update_idletasks()
    return image_label.winfo_width(), image_label.winfo_height()

def scale_image(img, canvas_width, canvas_height):
    img_width, img_height = img.size
    scale_x = canvas_width / img_width
    scale_y = canvas_height / img_height
    scale = min(scale_x, scale_y)
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
            
            convert_button.config(state=tk.NORMAL)
        except Exception as e:
            print(f"Error loading image: {e}")

def toggle_fullscreen(event=None):
    is_fullscreen = root.attributes('-fullscreen')
    root.attributes('-fullscreen', not is_fullscreen)

def generate_pdf_from_text(text_content, file_path):
    c = canvas.Canvas(file_path, pagesize=letter)
    textobject = c.beginText()
    textobject.setTextOrigin(50, 750)
    textobject.setFont("DejaVu", 13)

    for line in text_content.splitlines():
        try:
            # Convert an toàn sang str và encode/decode UTF-8
            if isinstance(line, bytes):
                line = line.decode('utf-8', errors='ignore')
            else:
                line = str(line).encode('utf-8', errors='ignore').decode('utf-8')
            textobject.textLine(line)
        except Exception as e:
            print("Lỗi dòng:", line, e)

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
    global tk_img, rotated_display, crop_box, scale_factor, canvas_width, canvas_height, x_offset, y_offset
    temp = working_img.copy()
    if flip_x.get():
        temp = ImageOps.mirror(temp)
    if flip_y.get():
        temp = ImageOps.flip(temp)
    angle = angle_var.get()
    rotated_display = temp.rotate(-angle, expand=False)
    
    canvas_width, canvas_height = get_canvas_size()
    scaled, scale_factor = scale_image(rotated_display, canvas_width, canvas_height)
    
    tk_img = ImageTk.PhotoImage(scaled)
    image_label.img_ref = tk_img
    image_label.delete("all")
    
    image_label.create_image(canvas_width // 2, canvas_height // 2, image=tk_img, anchor='center')
    
    scaled_width, scaled_height = scaled.size
    x_offset = (canvas_width - scaled_width) // 2
    y_offset = (canvas_height - scaled_height) // 2
    
    x0, y0, x1, y1 = [coord * scale_factor for coord in crop_box]
    image_label.create_rectangle(x0 + x_offset, y0 + y_offset, x1 + x_offset, y1 + y_offset, outline="#E8998D", width=2)

def detect_edge(event):
    global crop_box, x_offset, y_offset
    scaled_crop = [coord * scale_factor for coord in crop_box]
    x1, y1, x2, y2 = [coord + offset for coord, offset in zip(scaled_crop, [x_offset, y_offset, x_offset, y_offset])]
    x, y = event.x, event.y
    margin = 8

    if abs(x - x1) < margin and abs(y - y1) < margin:
        return "top-left"
    elif abs(x - x2) < margin and abs(y - y1) < margin:
        return "top-right"
    elif abs(x - x1) < margin and abs(y - y2) < margin:
        return "bottom-left"
    elif abs(x - x2) < margin and abs(y - y2) < margin:
        return "bottom-right"
    
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
    global crop_box, drag_start, x_offset, y_offset
    if drag_edge is None or drag_start is None:
        return
    dx = (event.x - x_offset - drag_start[0]) / scale_factor
    dy = (event.y - y_offset - drag_start[1]) / scale_factor
    x1, y1, x2, y2 = crop_box
    
    if drag_edge == "left":
        x1 = max(0, min(x1 + dx, x2 - 10))
    elif drag_edge == "right":
        x2 = min(working_img.width, max(x2 + dx, x1 + 10))
    elif drag_edge == "top":
        y1 = max(0, min(y1 + dy, y2 - 10))
    elif drag_edge == "bottom":
        y2 = min(working_img.height, max(y2 + dy, y1 + 10))
    elif drag_edge == "top-left":
        x1 = max(0, min(x1 + dx, x2 - 10))
        y1 = max(0, min(y1 + dy, y2 - 10))
    elif drag_edge == "top-right":
        x2 = min(working_img.width, max(x2 + dx, x1 + 10))
        y1 = max(0, min(y1 + dy, y2 - 10))
    elif drag_edge == "bottom-left":
        x1 = max(0, min(x1 + dx, x2 - 10))
        y2 = min(working_img.height, max(y2 + dy, y1 + 10))
    elif drag_edge == "bottom-right":
        x2 = min(working_img.width, max(x2 + dx, x1 + 10))
        y2 = min(working_img.height, max(y2 + dy, y1 + 10))
    
    crop_box = [x1, y1, x2, y2]
    drag_start = (event.x - x_offset, event.y - y_offset)
    draw_all()

def start_drag(event):
    global drag_edge, drag_start, x_offset, y_offset
    drag_edge = detect_edge(event)
    drag_start = (event.x - x_offset, event.y - y_offset)


def end_drag(event):
    global drag_edge, drag_start
    drag_edge = None
    drag_start = None

def confirm_crop():
    global working_img, display_img, crop_box, tk_img
    if working_img is None or crop_box is None: return
    try:
        temp = working_img.copy()
        if flip_x.get(): temp = ImageOps.mirror(temp)
        if flip_y.get(): temp = ImageOps.flip(temp)
        angle = angle_var.get() % 360
        if angle in [90, 270]:
            temp = temp.transpose(Image.ROTATE_270 if angle == 90 else Image.ROTATE_90)
        elif angle != 0:
            temp = temp.rotate(-angle, expand=False)
        
        x1, y1, x2, y2 = crop_box
        cropped = temp.crop((x1, y1, x2, y2))
        
        working_img = cropped.convert("RGBA")
        crop_box = [0, 0, working_img.width, working_img.height] 
        
        angle_var.set(0)
        flip_x.set(False)
        flip_y.set(False)
        
        draw_all()
        messagebox.showinfo("Image Edited", "The image has been edited and loaded.")

    except Exception as e:
        messagebox.showerror("Lỗi Crop", f"Không thể cắt ảnh: {e}")


def rotate_fixed(deg):
    global working_img, crop_box
    working_img = working_img.rotate(deg, expand=True)
    crop_box = [0, 0, working_img.width, working_img.height]
    angle_var.set(0) 
    draw_all()
    
def gtc():
    global content
    content = text_widget.get("1.0", "end-1c")
    print(pdfmetrics.getFont("DejaVu"))
    root.clipboard_clear()
    root.clipboard_append(content)
    status_label.config(text="Text copied to clipboard ٩(ˊᗜˋ*)و ♡")
    
def run_ocr_pipeline_from_gui():
    global working_img, text_widget, status_label, root

    if working_img is None:
        messagebox.showwarning("Thiếu ảnh", "Vui lòng tải hoặc cắt ảnh trước khi Convert.")
        return
    temp_image_path = "temp_gui_image_for_ocr.png"
    try:
        img_to_save = working_img.convert("RGBA")
        img_to_save.save(temp_image_path, "PNG")
        print(f"Đã lưu ảnh tạm thời tại: {temp_image_path}")
    except Exception as e:
        messagebox.showerror("Lỗi Lưu Ảnh Tạm", f"Không thể lưu ảnh tạm: {e}")
        return

    TEMP_CROP_FOLDER = 'temp_gui_cropped_lines'
    RESULT_FILE_GUI = 'result_gui.txt'     
    DEBUG_IMAGE_OUTPUT = 'debug_bounding_boxes.png'    

    Y_THRESHOLD_RATIO = 0.7 
    PADDING_RATIO = 0.17
    TARGET_OCR_HEIGHT = 64

    clean_folder(TEMP_CROP_FOLDER)

    status_label.config(text="Detecting lines... 𐔌՞. .՞𐦯")
    root.update_idletasks()

    grouped_boxes = None
    avg_h = 0
    cropped_files = None
    final_text_result = None

    try:
        grouped_boxes, avg_h = find_line_groups(
            temp_image_path, 
            y_threshold_ratio=Y_THRESHOLD_RATIO
        )

        if not grouped_boxes:
            status_label.config(text="Error: Text not found.ᐟ.ᐟ")
            return
        
        draw_debug_boxes(temp_image_path, grouped_boxes, DEBUG_IMAGE_OUTPUT,
                             avg_height=avg_h, padding_ratio=PADDING_RATIO)

        status_label.config(text=f"Found {len(grouped_boxes)} lines. Cropping...")
        root.update_idletasks()

        cropped_files = crop_and_save_lines(
            temp_image_path,
            grouped_boxes,
            TEMP_CROP_FOLDER,
            avg_height=avg_h,
            padding_ratio=PADDING_RATIO,
            target_ocr_height=TARGET_OCR_HEIGHT
        )

        if not cropped_files:
            status_label.config(text="Error: Cropping failed.")
            return

        status_label.config(text="Cropping successfully. Identifying...")
        root.update_idletasks()

        final_text_result = recognize_text_from_folder(TEMP_CROP_FOLDER, RESULT_FILE_GUI)

        if final_text_result is not None:
            text_widget.delete("1.0", tk.END)
            text_widget.insert(tk.END, final_text_result)
            status_label.config(text="Identifying successfully!")
        else:
            status_label.config(text="Error: Identifying failed.")

    except Exception as e:
        status_label.config(text=f"OCR process failed: {str(e)[:100]}...")
        messagebox.showerror("OCR error", f"An error occurred in the process.:\n{e}")
        import traceback
        traceback.print_exc()
    finally:
        if os.path.exists(temp_image_path):
            try:
                os.remove(temp_image_path)
                print(f"Đã xóa ảnh tạm: {temp_image_path}")
            except Exception as e:
                print(f"Lỗi khi xóa ảnh tạm: {e}")


status_label = Label(root, text="", fg="#6BA368", font=('Segoe Script', 10),bg='#F7FFF7')
status_label.place(anchor='n', relwidth=0.3, relx=0.8, rely=0.85)

text_widget = Text(highlightbackground='#E8998D', highlightthickness=3, relief="ridge")
text_widget.insert(END, "Your extracted text will appear here (˶˃ ᵕ ˂˶).ᐟ")
text_widget.place(anchor='s', relwidth=0.3, relheight=0.5, relx=0.8, rely=0.65)

esc = Label(text="Press Esc to exit full screen.", font=("Segoe Script", 8), fg="#83564F", bg='#F7FFF7')
esc.place(anchor='center', relx=0.5, rely=0.98) 

Label(text='Upload your image to extract text ₍^. .^₎Ⳋ', font=('Segoe Script', 18, "bold"), fg="#83564F", bg='#F7FFF7').place(anchor='center', relx=0.5, rely=0.05)  

convert_button = Button(text='Convert', fg="#83564F", relief='flat', bg="#FAD4CE",
                         command=run_ocr_pipeline_from_gui, state=tk.DISABLED)
convert_button.place(anchor='n', relwidth=0.3, relx=0.8, rely=0.7)

Button(text='Copy', fg="#83564F", command=lambda: gtc(), relief='flat', bg="#FAD4CE").place(anchor='n', relwidth=0.3, relx=0.8, rely=0.75) 

Button(text='Download as PDF', fg="#83564F", width=25, command=lambda: save_to_file(), relief='flat', bg="#FAD4CE").place(anchor='n', relwidth=0.3, relx=0.8, rely=0.8)  

button_frame = Frame(root, bg='#F7FFF7')
button_frame.place(anchor='center', relheight=0.05, relx=0.32, rely=0.93) 
Button(button_frame, text="Upload", command=lambda: upload_image(), relief='flat', fg="#83564F", bg="#FAD4CE").pack(side='left', padx=5)
Label(button_frame, text="Rotate (°):", fg="#83564F", font=('Segoe Script', 10), bg='#F7FFF7').pack(side='left', padx=5)
Scale(button_frame, bg='#F7FFF7', fg="#83564F", highlightthickness=0, relief='flat', from_=-90, to=90, orient=HORIZONTAL, length=150, variable=angle_var, command=lambda e: draw_all()).pack(side='left', padx=5)
Button(button_frame, text="⟲ Left", fg="#83564F", command=lambda: rotate_fixed(90), relief='flat', bg="#FAD4CE").pack(side='left', padx=5)
Button(button_frame, text="⟳ Right", fg="#83564F", command=lambda: rotate_fixed(-90), relief='flat', bg="#FAD4CE").pack(side='left', padx=5)
Button(button_frame, text="⇋ Horizontal Flip", fg="#83564F", command=lambda: [flip_x.set(not flip_x.get()), draw_all()], relief='flat', bg="#FAD4CE").pack(side='left', padx=5)
Button(button_frame, text="⇅ Vertical Flip", fg="#83564F", command=lambda: [flip_y.set(not flip_y.get()), draw_all()], relief='flat', bg="#FAD4CE").pack(side='left', padx=5)
Button(button_frame, text="✅", fg="#83564F", command=confirm_crop, relief='flat', bg="#FAD4CE").pack(side='left', padx=5)
image_label = Canvas(bg='white', highlightbackground='#E8998D', highlightthickness=3, relief="ridge")
image_label.place(relwidth=0.55, relheight=0.8, anchor='e', relx=0.6, rely=0.5) 
image_label.bind("<ButtonPress-1>", start_drag)
image_label.bind("<B1-Motion>", do_drag)
image_label.bind("<ButtonRelease-1>", end_drag)
root.bind('<Escape>', toggle_fullscreen)
root.mainloop()

