# File: handle_image/detection.py - Chỉ Resize (Không Grayscale/CLAHE)

import easyocr
import cv2
import numpy as np
import os

_easyocr_reader = None

def get_easyocr_reader():
    """Khởi tạo EasyOCR reader một lần duy nhất."""
    global _easyocr_reader
    if _easyocr_reader is None:
        print("[Detection] Đang khởi tạo EasyOCR...")
        _easyocr_reader = easyocr.Reader(['en', 'vi'], gpu=False)
    return _easyocr_reader

# --- HÀM RESIZE ---
def resize_line_image(img_array, target_height=64):
    """
    CHỈ Resize ảnh (màu) về chiều cao mong muốn, giữ tỷ lệ khung hình.
    """
    if img_array is None or img_array.size == 0:
        print("[Resize] Lỗi: Ảnh đầu vào rỗng.")
        return None

    try:
        # Lấy kích thước gốc
        original_height, original_width = img_array.shape[:2]

        if original_height == target_height:
            resized_img = img_array # Giữ nguyên nếu đã đúng chiều cao
            print(f"[Resize] Ảnh đã có chiều cao {target_height}px.")
        else:
            # Tính tỷ lệ và chiều rộng mới
            scale_ratio = target_height / original_height
            new_width = int(original_width * scale_ratio)
            new_width = max(1, new_width) # Đảm bảo > 0

            # Thực hiện Resize
            interpolation_method = cv2.INTER_AREA if target_height < original_height else cv2.INTER_LINEAR
            resized_img = cv2.resize(img_array, (new_width, target_height), interpolation=interpolation_method)
            print(f"[Resize] Đã resize từ {original_width}x{original_height} -> {new_width}x{target_height}")

        return resized_img # Trả về ảnh MÀU đã resize

    except Exception as e:
        print(f"[Resize] Lỗi trong quá trình resize: {e}")
        return None
# ----------------------------------------

def find_line_groups(image_path, y_threshold_ratio=0.7):
    """
    HÀM 1: CHẠY EASYOCR VÀ GỘP DÒNG
    (Hàm này không thay đổi)
    """
    reader = get_easyocr_reader()

    print("[Detection] Đang chạy EasyOCR...")
    # Chạy trên ảnh gốc
    result = reader.readtext(
        image_path,
        detail=1,
        paragraph=False,
        low_text=0.2,
        text_threshold=0.3
    )

    # ... (Phần còn lại của hàm find_line_groups giữ nguyên) ...
    if not result: return [], 0
    boxes_with_info = []
    total_height = 0; valid_boxes_count = 0
    for (bbox, text, prob) in result:
        (tl, tr, br, bl) = bbox
        y_min = min(tl[1], tr[1]); y_max = max(bl[1], br[1])
        height = y_max - y_min
        if height > 0:
            y_center = (y_min + y_max) / 2
            boxes_with_info.append({'bbox': bbox, 'y_center': y_center, 'height': height})
            total_height += height; valid_boxes_count += 1
    if not boxes_with_info: return [], 0
    avg_height = total_height / valid_boxes_count if valid_boxes_count > 0 else 30
    actual_y_threshold = avg_height * y_threshold_ratio
    print(f"[Detection] Chiều cao TB: {avg_height:.2f}px, Ngưỡng Y: {actual_y_threshold:.2f}px")
    boxes_with_info.sort(key=lambda b: b['y_center'])
    lines_of_boxes = []
    if not boxes_with_info: return [], avg_height
    current_line_boxes = [boxes_with_info[0]]
    current_line_anchor_y = boxes_with_info[0]['y_center']
    for box_info in boxes_with_info[1:]:
        y_center = box_info['y_center']
        if abs(y_center - current_line_anchor_y) < actual_y_threshold:
            current_line_boxes.append(box_info)
        else:
            current_line_boxes.sort(key=lambda b: b['bbox'][0][0])
            lines_of_boxes.append(current_line_boxes)
            current_line_boxes = [box_info]
            current_line_anchor_y = y_center
    current_line_boxes.sort(key=lambda b: b['bbox'][0][0])
    lines_of_boxes.append(current_line_boxes)
    print(f"[Detection] Đã gộp thành {len(lines_of_boxes)} nhóm dòng.")
    return lines_of_boxes, avg_height


# ---------------------------------------------------------------------
# HÀM VẼ DEBUG (Không thay đổi)
# ---------------------------------------------------------------------
def draw_debug_boxes(image_path, lines_of_boxes, output_path, avg_height, padding_ratio=0.3):
    """
    HÀM 2: VẼ HỘP LỚN (CHIỀU CAO DỰA TRÊN AVG_HEIGHT) - ĐÃ SỬA LỖI
    """
    img = cv2.imread(image_path) # Đọc ảnh gốc
    if img is None:
        print(f"[Debug Draw] Lỗi: Không thể đọc ảnh {image_path} để vẽ.")
        return False

    # === SỬA LỖI: Tạo bản sao để vẽ ===
    img_with_boxes = img.copy()
    # =================================

    print(f"[Debug Draw] Đang vẽ {len(lines_of_boxes)} hộp dòng...")

    actual_padding_y = int(avg_height * padding_ratio)
    actual_padding_x = actual_padding_y

    for i, line_boxes in enumerate(lines_of_boxes):
        if not line_boxes: continue

        all_x_coords = []
        all_y_centers = []

        for box_info in line_boxes:
            bbox = box_info['bbox']
            (tl, tr, br, bl) = bbox
            all_x_coords.extend([tl[0], tr[0], br[0], bl[0]])
            y_min_box = min(tl[1], tr[1]); y_max_box = max(bl[1], br[1])
            if y_max_box > y_min_box: # Check height > 0
                all_y_centers.append((y_min_box + y_max_box) / 2)

        if not all_x_coords or not all_y_centers: continue

        # Tính toán hộp bao
        line_avg_y_center = sum(all_y_centers) / len(all_y_centers)
        half_avg_height_padded = (avg_height / 2) + actual_padding_y
        y_min_calc = line_avg_y_center - half_avg_height_padded
        y_max_calc = line_avg_y_center + half_avg_height_padded
        x_min_calc = min(all_x_coords) - actual_padding_x
        x_max_calc = max(all_x_coords) + actual_padding_x

        x_min = int(max(0, x_min_calc))
        y_min = int(max(0, y_min_calc))
        x_max = int(min(img.shape[1], x_max_calc))
        y_max = int(min(img.shape[0], y_max_calc))

        # === SỬA LỖI: Vẽ lên img_with_boxes ===
        cv2.rectangle(img_with_boxes, (x_min, y_min), (x_max, y_max), color=(0, 0, 255), thickness=2)
        cv2.putText(img_with_boxes, f"Line {i+1}", (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        # =====================================

    try:
        # === SỬA LỖI: Lưu ảnh đã vẽ ===
        cv2.imwrite(output_path, img_with_boxes)
        # =============================
        print(f"--- Đã lưu ảnh debug tại: {output_path} ---")
        return True
    except Exception as e:
        print(f"[Debug Draw] Lỗi khi lưu ảnh debug: {e}")
        return False

# ---------------------------------------------------------------------
# === HÀM CẮT (ĐÃ CẬP NHẬT ĐỂ GỌI HÀM RESIZE MỚI) ===
# ---------------------------------------------------------------------
def crop_and_save_lines(image_path, lines_of_boxes, output_folder, avg_height, padding_ratio=0.3, target_ocr_height=64):
    """
    HÀM 3: CẮT, CHỈ RESIZE, VÀ LƯU ẢNH (MÀU)
    """
    img = cv2.imread(image_path) # Đọc ảnh gốc để cắt
    if img is None: return []
    if not os.path.exists(output_folder): os.makedirs(output_folder)

    print("[Cropping] Bắt đầu cắt, resize và lưu ảnh...")

    actual_padding_y = int(avg_height * padding_ratio)
    actual_padding_x = actual_padding_y

    cropped_image_paths = []
    for i, line_boxes in enumerate(lines_of_boxes):
        if not line_boxes: continue

        # --- Tính toán hộp bao (giữ nguyên) ---
        all_x_coords = []; all_y_centers = []
        for box_info in line_boxes:
            bbox = box_info['bbox']; (tl, tr, br, bl) = bbox
            all_x_coords.extend([tl[0], tr[0], br[0], bl[0]])
            all_y_centers.append(box_info['y_center'])
        if not all_x_coords or not all_y_centers: continue
        line_avg_y_center = sum(all_y_centers) / len(all_y_centers)
        half_avg_height_padded = (avg_height / 2) + actual_padding_y
        y_min_calc = line_avg_y_center - half_avg_height_padded
        y_max_calc = line_avg_y_center + half_avg_height_padded
        x_min_calc = min(all_x_coords) - actual_padding_x
        x_max_calc = max(all_x_coords) + actual_padding_x
        x_min = int(max(0, x_min_calc)); y_min = int(max(0, y_min_calc))
        x_max = int(min(img.shape[1], x_max_calc)); y_max = int(min(img.shape[0], y_max_calc))
        # -------------------------------------

        # 1. Cắt ảnh dòng từ ảnh gốc (ảnh màu)
        cropped_line_img = img[y_min:y_max, x_min:x_max]

        # 2. CHỈ RESIZE ẢNH ĐÃ CẮT
        resized_img = resize_line_image(cropped_line_img, target_height=target_ocr_height)

        # 3. Lưu ảnh ĐÃ RESIZE (nếu thành công)
        if resized_img is not None:
            filename_base = os.path.splitext(os.path.basename(image_path))[0]
            # Lưu ảnh PNG đã resize
            output_line_path = os.path.join(output_folder, f"{filename_base}_line_{i+1}_resized.png")
            try:
                cv2.imwrite(output_line_path, resized_img)
                cropped_image_paths.append(output_line_path)
                print(f"  - Đã CẮT, RESIZE dòng {i+1} và lưu tại: {output_line_path}")
            except Exception as e:
                 print(f"[Cropping] Lỗi khi lưu ảnh dòng {i+1}: {e}")
        else:
            print(f"  - Bỏ qua dòng {i+1} do lỗi resize.")

    return cropped_image_paths