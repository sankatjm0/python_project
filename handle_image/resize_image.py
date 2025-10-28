import cv2
import os
import numpy as np

def resize_image_for_ocr(input_path, output_path, target_height=64):
    """
    Resize ảnh về chiều cao mong muốn (target_height), giữ nguyên tỷ lệ khung hình.

    Args:
        input_path (str): Đường dẫn đến ảnh đầu vào (ảnh dòng đã cắt).
        output_path (str): Đường dẫn để lưu ảnh đã resize.
        target_height (int): Chiều cao mong muốn (mặc định 64 pixel).

    Returns:
        bool: True nếu thành công, False nếu lỗi.
    """
    try:
        # 1. Đọc ảnh
        img = cv2.imread(input_path)
        if img is None:
            print(f"[Resize] Lỗi: Không thể đọc ảnh: {input_path}")
            return False

        # 2. Lấy kích thước gốc
        original_height, original_width = img.shape[:2]

        # 3. Tính toán tỷ lệ và chiều rộng mới
        # Nếu chiều cao gốc đã là target_height thì không cần resize
        if original_height == target_height:
            new_width = original_width
            resized_img = img # Giữ nguyên ảnh
            print(f"[Resize] Ảnh '{os.path.basename(input_path)}' đã có chiều cao {target_height}px.")
        else:
            # Tính tỷ lệ co giãn
            scale_ratio = target_height / original_height
            # Tính chiều rộng mới để giữ tỷ lệ
            new_width = int(original_width * scale_ratio)

            # Đảm bảo chiều rộng mới ít nhất là 1 pixel
            new_width = max(1, new_width)

            # 4. Thực hiện Resize
            # cv2.INTER_LINEAR là lựa chọn tốt cho việc thay đổi kích thước thông thường
            # cv2.INTER_AREA thường tốt hơn khi thu nhỏ ảnh
            interpolation_method = cv2.INTER_AREA if target_height < original_height else cv2.INTER_LINEAR
            resized_img = cv2.resize(img, (new_width, target_height), interpolation=interpolation_method)
            print(f"[Resize] Đã resize '{os.path.basename(input_path)}' từ {original_width}x{original_height} -> {new_width}x{target_height}")

        # 5. Lưu ảnh đã resize (nên lưu dạng PNG)
        # Tạo thư mục nếu chưa có
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Đảm bảo đuôi file là .png
        if not output_path.lower().endswith(".png"):
             output_path = os.path.splitext(output_path)[0] + ".png"

        success = cv2.imwrite(output_path, resized_img)
        if success:
            print(f"[Resize] Đã lưu ảnh resize tại: {output_path}")
            return True
        else:
            print(f"[Resize] Lỗi: Không thể lưu ảnh resize tại: {output_path}")
            return False

    except Exception as e:
        print(f"[Resize] Lỗi không xác định khi resize '{input_path}': {e}")
        return False

# --- CÁCH SỬ DỤNG (VÍ DỤ) ---
if __name__ == "__main__":
    # Thư mục chứa các ảnh dòng đã cắt (ví dụ: ảnh màu gốc)
    input_folder = 'data/cropped_lines' # <-- Đảm bảo tên đúng
    # Thư mục mới để lưu ảnh đã resize
    output_folder_resized = 'data/cropped_lines_resized'

    # Tạo thư mục output nếu chưa có
    if not os.path.exists(output_folder_resized):
        os.makedirs(output_folder_resized)

    print(f"\n--- Bắt đầu resize ảnh trong '{input_folder}' ---")
    resize_count = 0
    try:
        for filename in sorted(os.listdir(input_folder)):
            if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                input_file_path = os.path.join(input_folder, filename)
                # Tạo tên file output (luôn là .png)
                output_filename = os.path.splitext(filename)[0] + "_resized.png"
                output_file_path = os.path.join(output_folder_resized, output_filename)

                # Gọi hàm resize cho từng ảnh
                if resize_image_for_ocr(input_file_path, output_file_path, target_height=64):
                    resize_count += 1
                    
        print(f"\n--- Hoàn tất! Đã resize {resize_count} ảnh. ---")
        print(f"Ảnh đã resize được lưu trong thư mục: '{output_folder_resized}'")

    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy thư mục '{input_folder}'.")
    except Exception as e:
        print(f"Lỗi không mong muốn: {e}")