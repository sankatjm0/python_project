from PIL import Image
import os
from pillow_heif import register_heif_opener

# Đăng ký trình đọc file HEIC/HEIF
# Sau dòng này, Image.open() sẽ tự động "hiểu" được file .heic
register_heif_opener()
def convert_to_png(input_path, output_dir="data/images", extension=".png"):
    """
    Chuyển đổi bất kỳ file ảnh nào (bao gồm .heic, .jpg, .bmp, .webp...)
    sang định dạng PNG và lưu vào thư mục output_dir.
    """
    try:
        base_name = os.path.basename(input_path) 
        file_name_only = os.path.splitext(base_name)[0]
        output_path = os.path.join(output_dir, file_name_only + extension) 
        
        os.makedirs(output_dir, exist_ok=True)

        with Image.open(input_path) as img:
            img.save(output_path, extension.split(".")[-1].upper())
            print(f"Thành công! Đã chuyển đổi '{input_path}' thành '{output_path}'")
            
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file tại '{input_path}'")
    except Exception as e:
        print(f"Lỗi: Không thể chuyển đổi file. Lý do: {e}")
        print("Định dạng file có thể không được hỗ trợ hoặc file bị lỗi.")

def convert_all_folder_to_png(input_dir, output_dir="data/images", extension=".png"):
    if not os.path.isdir(input_dir):
        print(f"Lỗi: Không tìm thấy thư mục: {input_dir}")
        return

    allowed_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', 
                          '.webp', '.tiff', '.heic', '.heif')

    print(f"Đang quét thư mục: {input_dir}...")
    file_count = 0
    
    for file_name in os.listdir(input_dir):
        input_path = os.path.join(input_dir, file_name)
        if os.path.isfile(input_path) and file_name.lower().endswith(allowed_extensions):
            print(f"--- Đang xử lý: {file_name} ---")
            convert_to_png(input_path, output_dir, extension)
            file_count += 1
        else:
            pass

    print(f"\nHoàn tất! Đã chuyển đổi thành công {file_count} file ảnh.")                                      

# --- Cách sử dụng ---
IMG = "test/IMG_2271.HEIC"

# convert_to_png(IMG, "test/converted")
convert_all_folder_to_png("test", output_dir="test/converted", extension=".tiff")