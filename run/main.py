import sys
import os

try:
    from handle_image.detection import *
    from handle_image.recognition import recognize_text_from_folder
    # Giả sử hàm clean_folder nằm trong utils hoặc bạn có thể copy vào đây
    from utils.clean_folder import clean_folder
except ImportError:
    print("Lỗi: Không thể import các module từ thư mục")
    sys.exit(1)

# CONFIG
INPUT_IMAGE = 'data/images/anh_print_text_2.jpg'
OUTPUT_FOLDER = 'data/cropped_lines_processed' # Thư mục chứa ảnh đã cắt, xử lý, resize
DEBUG_IMAGE_OUTPUT = 'lines_drawn.jpg'
RESULT_FILE = 'result.txt'

# --- ĐIỀU CHỈNH THAM SỐ ---
Y_THRESHOLD_RATIO = 0.7 # Tỷ lệ ngưỡng Y (so với chiều cao TB)
PADDING_RATIO = 0.17    # Tỷ lệ padding (so với chiều cao TB)
TARGET_OCR_HEIGHT = 64  # Chiều cao ảnh cuối cùng cho VietOCR
# -------------------------

# --- CHỌN HÀNH ĐỘNG ---
RUN_DETECTION = True
DRAW_DEBUG_IMAGE = False # Tắt vẽ debug khi chạy chính thức
RUN_CROPPING = True
RUN_RECOGNITION = True
# ----------------------s

if __name__ == "__main__":
    print(f"--- BẮT ĐẦU QUY TRÌNH ---")
    if not os.path.exists(INPUT_IMAGE): sys.exit(1)

    # Dọn dẹp thư mục cũ
    clean_folder(OUTPUT_FOLDER)

    grouped_boxes = None; avg_h = 0
    cropped_files = None; final_text_result = None

    try:
        # === BƯỚC 1: TÌM NHÓM DÒNG ===
        if RUN_DETECTION:
            grouped_boxes, avg_h = find_line_groups(
                INPUT_IMAGE, y_threshold_ratio=Y_THRESHOLD_RATIO
            )
        if not grouped_boxes: sys.exit(0)

        # === BƯỚC 2 (TÙY CHỌN): VẼ ẢNH DEBUG ===
        if DRAW_DEBUG_IMAGE:
            draw_debug_boxes(INPUT_IMAGE, grouped_boxes, DEBUG_IMAGE_OUTPUT,
                             avg_height=avg_h, padding_ratio=PADDING_RATIO)

        # === BƯỚC 3: CẮT, XỬ LÝ VÀ LƯU ẢNH ===
        if RUN_CROPPING:
            cropped_files = crop_and_save_lines(
                INPUT_IMAGE, grouped_boxes, OUTPUT_FOLDER,
                avg_height=avg_h, padding_ratio=PADDING_RATIO,
                target_ocr_height=TARGET_OCR_HEIGHT # Truyền chiều cao vào
            )

        # === BƯỚC 4: RECOGNIZE VÀ XUẤT KẾT QUẢ ===
        if RUN_RECOGNITION and cropped_files: # Chỉ chạy nếu đã cắt thành công
            print("\n--- Bắt đầu nhận dạng ---")
            final_text_result = recognize_text_from_folder(OUTPUT_FOLDER, RESULT_FILE)
            if final_text_result is not None:
                print("\n--- HOÀN TẤT TOÀN BỘ QUY TRÌNH ---")
            else:
                print("\nNhận dạng thất bại.")
        elif RUN_RECOGNITION and not cropped_files:
             print("\nBỏ qua nhận dạng vì bước cắt ảnh thất bại.")


        print("\n--- QUY TRÌNH KẾT THÚC ---")

    except Exception as e:
        print(f"\n!!! LỖI NGHIÊM TRỌNG KHI CHẠY: {e}")
        import traceback; traceback.print_exc()