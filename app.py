from tkinter import *
from tkinter import filedialog, messagebox, font
import tkinter as tk
from PIL import Image, ImageTk, ImageOps

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import os
import sys

try:
    # Điều chỉnh đường dẫn sys.path để Python tìm thấy thư mục handle_image
    # Lấy đường dẫn thư mục chứa file app.py này
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Lấy đường dẫn thư mục cha (VietNameseHandwrittenOCR)
    parent_dir = os.path.dirname(current_dir)
    # Thêm thư mục cha vào sys.path để có thể import handle_image
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)

    from handle_image.detection import find_line_groups, crop_and_save_lines
    from handle_image.recognition import recognize_text_from_folder
    from utils.clean_folder import clean_folder
except ImportError as e:
    messagebox.showerror("Lỗi Import", f"Không thể import module xử lý ảnh: {e}\nKiểm tra cấu trúc thư mục và file __init__.py.")
    # Có thể thoát chương trình ở đây nếu lỗi nghiêm trọng
    # sys.exit(1)

def resource_path(relative_path):
    """ Lấy đường dẫn tuyệt đối, hoạt động cho cả dev và PyInstaller """
    try:
        # PyInstaller tạo thư mục tạm _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Chạy bình thường, base_path là thư mục chứa app.py
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)




root = Tk()
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

# === BIẾN LƯU ẢNH (Quan trọng) ===
original_img = None # Ảnh gốc khi mở file
working_img = None  # Ảnh đang được chỉnh sửa (rotate, flip, crop)
display_img = None  # Ảnh đã resize để hiển thị trên canvas
tk_img = None       # Ảnh dạng Tkinter PhotoImage
crop_box = None     # Tọa độ crop hiện tại trên working_img
# ================================

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
            # original_img = Image.open(filename).convert("RGBA")
            original_img = Image.open(filename).convert("RGB")
            working_img = original_img.copy()
            crop_box = [0, 0, working_img.width, working_img.height]
            scale_factor = 1
            draw_all()
            
            # Kích hoạt nút Convert khi có ảnh
            convert_button.config(state=tk.NORMAL)
        except Exception as e:
            print(f"Error loading image: {e}")

def toggle_fullscreen(event=None):
    is_fullscreen = root.attributes('-fullscreen')
    root.attributes('-fullscreen', not is_fullscreen)

def generate_pdf_from_text(text_content, file_path, font_path="GUI/DejaVuSans.ttf"):
    try:
        c = canvas.Canvas(file_path, pagesize=letter)
        textobject = c.beginText()
        textobject.setTextOrigin(50, 750)
        textobject.setFont("Helvetica", 12)

        for line in text_content.splitlines():
            textobject.textLine(line)

        c.drawText(textobject)
        c.save()
    
    except FileNotFoundError as fnf_error:
        print(f"Lỗi Font: {fnf_error}")
        messagebox.showerror("Lỗi Font", f"{fnf_error}\nHãy tải font DejaVuSans.ttf và đặt vào cùng thư mục.")
        return False
    except Exception as e:
        print(f"Lỗi khi tạo PDF: {e}")
        messagebox.showerror("Lỗi Tạo PDF", f"Đã xảy ra lỗi: {e}")
        return False
    
    
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
    canvas_width, canvas_height = get_canvas_size()
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
    drag_start = (event.x - x_offset, event.y - y_offset)  # Cập nhật drag_start với offset đã trừ
    draw_all()

def start_drag(event):
    global drag_edge, drag_start, x_offset, y_offset
    drag_edge = detect_edge(event)
    drag_start = (event.x - x_offset, event.y - y_offset)


def end_drag(event):
    global drag_edge, drag_start
    drag_edge = None
    drag_start = None

# def confirm_crop():
#     global working_img, display_img, crop_box
#     temp = working_img.copy()
#     if flip_x.get():
#         temp = ImageOps.mirror(temp)
#     if flip_y.get():
#         temp = ImageOps.flip(temp)
#     angle = int(angle_var.get()) % 360
#     if angle in [90, 270]:
#         temp = temp.transpose(Image.ROTATE_270 if angle == 90 else Image.ROTATE_90)
#     elif angle != 0:
#         temp = temp.rotate(-angle, expand=False)
    
#     x1, y1, x2, y2 = crop_box
#     cropped = temp.crop((x1, y1, x2, y2))
    
#     working_img = cropped.convert("RGBA")
#     crop_box = [0, 0, working_img.width, working_img.height] 
    
#     angle_var.set(0)
#     flip_x.set(False)
#     flip_y.set(False)
    
#     draw_all()
#     messagebox.showinfo("Image Edited", "The image has been edited and loaded.")

def confirm_crop():
    global working_img, display_img, crop_box, tk_img # Thêm tk_img
    if working_img is None or crop_box is None: return

    try:
        # Cắt ảnh TẠM THỜI (đã rotate/flip nếu có)
        temp = working_img.copy()
        if flip_x.get(): temp = ImageOps.mirror(temp)
        if flip_y.get(): temp = ImageOps.flip(temp)
        angle = angle_var.get() % 360 # Lấy góc xoay hiện tại
        # Xoay ảnh tạm thời trước khi cắt
        temp_rotated = temp.rotate(-angle, expand=True) # expand=True để không mất góc

        # Tính toán lại tọa độ crop trên ảnh đã xoay (phức tạp, cách đơn giản hơn là crop trước rồi xoay)
        # Cách đơn giản: Áp dụng crop TRÊN working_img (chưa xoay/flip)
        x1, y1, x2, y2 = [int(c) for c in crop_box] # Chuyển sang int
        
        # Đảm bảo tọa độ hợp lệ
        x1 = max(0, x1); y1 = max(0, y1)
        x2 = min(working_img.width, x2); y2 = min(working_img.height, y2)
        
        if x1 >= x2 or y1 >= y2:
             messagebox.showwarning("Crop Lỗi", "Vùng chọn không hợp lệ.")
             return

        cropped = working_img.crop((x1, y1, x2, y2))

        # CẬP NHẬT working_img LÀ KẾT QUẢ ĐÃ CẮT
        working_img = cropped.copy()
        
        # Reset crop box về toàn bộ ảnh mới
        crop_box = [0, 0, working_img.width, working_img.height]

        # Reset các hiệu ứng (vì đã áp dụng crop)
        angle_var.set(0)
        flip_x.set(False)
        flip_y.set(False)

        # Vẽ lại giao diện với ảnh đã cắt
        draw_all()
        messagebox.showinfo("Thành Công", "Ảnh đã được cắt.")

    except Exception as e:
        messagebox.showerror("Lỗi Crop", f"Không thể cắt ảnh: {e}")


def rotate_fixed(deg):
    global working_img
    working_img = working_img.rotate(deg, expand=True)
    angle_var.set(0) 
    draw_all()
    
def gtc():
    global content
    content = text_widget.get("1.0", "end-1c")
    root.clipboard_clear()
    root.clipboard_append(content)
    status_label.config(text="Text copied to clipboard ٩(ˊᗜˋ*)و ♡")
    
def run_ocr_pipeline_from_gui():
    global working_img, text_widget, status_label, root # Thêm root để update GUI

    if working_img is None:
        messagebox.showwarning("Thiếu ảnh", "Vui lòng tải hoặc cắt ảnh trước khi Convert.")
        return

    # 1. Lưu ảnh hiện tại (working_img) ra file tạm PNG
    temp_image_path = "temp_gui_image_for_ocr.png"
    try:
        img_to_save = working_img.convert("RGB") # Đảm bảo là RGB
        img_to_save.save(temp_image_path, "PNG")
        print(f"Đã lưu ảnh tạm thời tại: {temp_image_path}")
    except Exception as e:
        messagebox.showerror("Lỗi Lưu Ảnh Tạm", f"Không thể lưu ảnh tạm: {e}")
        return

    # 2. Cấu hình cho quy trình OCR (Lấy từ main.py)
    TEMP_CROP_FOLDER = 'temp_gui_cropped_lines' # Thư mục tạm cho ảnh dòng
    RESULT_FILE_GUI = 'result_gui.txt'          # File lưu kết quả (tùy chọn)

    # --- SỬ DỤNG THAM SỐ TỶ LỆ ---
    Y_THRESHOLD_RATIO = 0.7 # Bạn có thể lấy từ Entry/Scale trong GUI nếu muốn
    PADDING_RATIO = 0.17    # Hoặc từ GUI
    TARGET_OCR_HEIGHT = 64  # Chiều cao chuẩn
    # -----------------------------

    # 3. Dọn dẹp thư mục tạm cũ
    clean_folder(TEMP_CROP_FOLDER)

    # 4. Chạy quy trình
    status_label.config(text="Đang phát hiện dòng...")
    root.update_idletasks() # Cập nhật giao diện ngay lập tức

    grouped_boxes = None
    avg_h = 0
    cropped_files = None
    final_text_result = None

    try:
        # === BƯỚC 1: TÌM NHÓM DÒNG ===
        # Hàm find_line_groups trả về nhóm hộp và chiều cao TB (avg_h)
        grouped_boxes, avg_h = find_line_groups(
            temp_image_path, # Dùng ảnh tạm
            y_threshold_ratio=Y_THRESHOLD_RATIO
        )

        if not grouped_boxes:
            status_label.config(text="Lỗi: Không tìm thấy dòng chữ.")
            # Không cần xóa file tạm ngay, sẽ xóa ở finally
            return

        status_label.config(text=f"Tìm thấy {len(grouped_boxes)} dòng. Đang cắt...")
        root.update_idletasks()

        # === BƯỚC 2: CẮT, XỬ LÝ (NẾU CÓ) VÀ LƯU ẢNH ===
        cropped_files = crop_and_save_lines(
            temp_image_path, # Dùng ảnh tạm
            grouped_boxes,
            TEMP_CROP_FOLDER,
            avg_height=avg_h,
            padding_ratio=PADDING_RATIO,
            target_ocr_height=TARGET_OCR_HEIGHT # Truyền chiều cao resize
        )

        if not cropped_files:
            status_label.config(text="Lỗi: Cắt ảnh thất bại.")
            # Không cần xóa file tạm ngay
            return

        status_label.config(text="Cắt thành công. Đang nhận dạng...")
        root.update_idletasks()

        # === BƯỚC 3: NHẬN DẠNG ===
        final_text_result = recognize_text_from_folder(TEMP_CROP_FOLDER, RESULT_FILE_GUI)

        # 5. Hiển thị kết quả và thông báo
        if final_text_result is not None:
            text_widget.delete("1.0", tk.END) # Xóa nội dung cũ
            text_widget.insert(tk.END, final_text_result) # Chèn kết quả mới
            status_label.config(text="Nhận dạng thành công!")
            # Tùy chọn: messagebox.showinfo("Hoàn tất", "Đã nhận dạng thành công!")
        else:
            status_label.config(text="Lỗi: Nhận dạng thất bại.")

    except Exception as e:
        status_label.config(text=f"Lỗi quy trình OCR: {str(e)[:100]}...") # Giới hạn độ dài lỗi
        messagebox.showerror("Lỗi OCR", f"Đã xảy ra lỗi trong quy trình:\n{e}")
        # In lỗi chi tiết ra console để debug
        import traceback
        traceback.print_exc()
    finally:
        # 6. Xóa file ảnh tạm (luôn thực hiện)
        if os.path.exists(temp_image_path):
            try:
                os.remove(temp_image_path)
                print(f"Đã xóa ảnh tạm: {temp_image_path}")
            except Exception as e:
                print(f"Lỗi khi xóa ảnh tạm: {e}")
        # (Tùy chọn) Xóa thư mục ảnh dòng tạm
        # import shutil
        # if os.path.exists(TEMP_CROP_FOLDER):
        #     shutil.rmtree(TEMP_CROP_FOLDER)


# --- Widgets (Giao diện người dùng) ---
status_label = Label(root, text="", fg="#6BA368", font=('Segoe Script', 10),bg='#F7FFF7')
status_label.place(anchor='n', relwidth=0.3, relx=0.8, rely=0.85)

text_widget = Text(highlightbackground='#E8998D', highlightthickness=3, relief="ridge")
text_widget.insert(END, "Your extracted text will appear here (˶˃ ᵕ ˂˶).ᐟ")
text_widget.place(anchor='s', relwidth=0.3, relheight=0.5, relx=0.8, rely=0.65)

esc = Label(text="Press Esc to exit full screen.", font=("Segoe Script", 8), fg="#83564F", bg='#F7FFF7')
esc.place(anchor='center', relx=0.5, rely=0.98) 

Label(text='Upload your image to extract text ₍^. .^₎Ⳋ', font=('Segoe Script', 18, "bold"), fg="#83564F", bg='#F7FFF7').place(anchor='center', relx=0.5, rely=0.05)  

# --- NÚT CONVERT ---
# Button(text='Convert', fg="#83564F", relief='flat', bg="#FAD4CE").place(anchor='n', relwidth=0.3, relx=0.8, rely=0.7) 
convert_button = Button(text='Convert', fg="#83564F", relief='flat', bg="#FAD4CE",
                         command=run_ocr_pipeline_from_gui, state=tk.DISABLED) # Thêm command, state=DISABLED ban đầu
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


