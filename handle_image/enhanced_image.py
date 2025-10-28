import cv2
import os
import numpy as np

# ----- RECROP AND BINARIZE LINES -----
def enhance_recrop_and_binarize_lines(input_folder, output_folder, final_padding=5):
    """
    Đọc ảnh dòng gốc (màu), tìm biên giới chữ,
    và CẮT LẠI sát chữ (vẫn giữ màu gốc).
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    print(f"\n[Recrop Original] Bắt đầu xử lý ảnh trong: '{input_folder}'")
    processed_files = []

    try:
        file_list = sorted(os.listdir(input_folder))
        for filename in file_list:
            # Ưu tiên xử lý file PNG nếu có, nếu không thì JPG
            if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                input_path = os.path.join(input_folder, filename)
                # Lưu kết quả dưới dạng PNG
                output_filename = os.path.splitext(filename)[0] + "_recropped.png"
                output_path = os.path.join(output_folder, output_filename)

                try:
                    # 1. Đọc ảnh GỐC (màu)
                    img = cv2.imread(input_path)
                    if img is None: continue

                    # 2. Chuyển sang ảnh xám (chỉ để tìm biên)
                    gray_for_bbox = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

                    # 3. Tạo ảnh nhị phân tạm thời (chỉ để tìm biên)
                    # Dùng Otsu trên ảnh xám gốc, đảo ngược để chữ là trắng
                    _, binary_for_bbox = cv2.threshold(gray_for_bbox, 0, 255,
                                                       cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

                    # 4. Tìm tọa độ biên giới chữ để cắt lại
                    rows_with_text = np.any(binary_for_bbox, axis=1)
                    cols_with_text = np.any(binary_for_bbox, axis=0)
                    y_indices = np.where(rows_with_text)[0]
                    x_indices = np.where(cols_with_text)[0]

                    final_image_to_save = None

                    if len(y_indices) > 0 and len(x_indices) > 0:
                        y_min_tight = y_indices[0]; y_max_tight = y_indices[-1]
                        x_min_tight = x_indices[0]; x_max_tight = x_indices[-1]

                        # Thêm padding nhỏ cuối cùng
                        y_min_final = max(0, y_min_tight - final_padding)
                        y_max_final = min(img.shape[0], y_max_tight + final_padding + 1) # +1 vì slicing
                        x_min_final = max(0, x_min_tight - final_padding)
                        x_max_final = min(img.shape[1], x_max_tight + final_padding + 1) # +1 vì slicing

                        # 5. CẮT LẠI ảnh GỐC (màu) theo tọa độ mới
                        final_cropped_color_img = img[y_min_final:y_max_final, x_min_final:x_max_final]

                        if final_cropped_color_img.size == 0:
                             print(f"  - CẢNH BÁO: Ảnh cắt lại bị rỗng cho '{filename}'. Lưu ảnh gốc.")
                             final_image_to_save = img # Dùng ảnh gốc chưa cắt lại
                        else:
                             final_image_to_save = final_cropped_color_img

                    else:
                        print(f"  - CẢNH BÁO: Không tìm thấy biên chữ để cắt lại '{filename}'. Lưu ảnh gốc.")
                        final_image_to_save = img # Dùng ảnh gốc chưa cắt lại

                    # 6. Lưu ảnh đã cắt lại (vẫn là ảnh màu)
                    if final_image_to_save is not None:
                        # Lưu dưới dạng PNG để đảm bảo chất lượng
                        cv2.imwrite(output_path, final_image_to_save)
                        processed_files.append(output_path)
                        print(f"  - Đã cắt lại (giữ màu) và lưu: {output_filename}")

                except Exception as e:
                    print(f"  - Lỗi khi xử lý '{filename}': {e}")

        print(f"\n[Recrop Original] Hoàn tất! Đã xử lý {len(processed_files)} ảnh.")
        return processed_files

    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy thư mục đầu vào '{input_folder}'.")
        return []


# ----- THICKEN STROKES (Closing) -----
def thicken_strokes_closing(input_folder, output_folder, kernel_size=2):
    """
    Đọc ảnh dòng đã cắt, chuyển sang đen/trắng, và làm đậm nét chữ
    bằng phép Đóng (Closing). Lưu kết quả đen/trắng.

    Args:
        input_folder (str): Thư mục chứa ảnh dòng gốc (màu hoặc xám).
        output_folder (str): Thư mục lưu ảnh đã làm đậm nét (đen/trắng).
        kernel_size (int): Kích thước kernel cho phép Đóng (thường là 2 hoặc 3).
                           Số lớn hơn làm đậm nhiều hơn nhưng dễ dính chữ.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    print(f"\n[Thicken] Bắt đầu làm đậm nét chữ trong: '{input_folder}'")
    processed_files = []

    try:
        file_list = sorted(os.listdir(input_folder))
        for filename in file_list:
            if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                input_path = os.path.join(input_folder, filename)
                # Đổi tên file đầu ra
                output_filename = os.path.splitext(filename)[0] + f"_thick_{kernel_size}x{kernel_size}.png"
                output_path = os.path.join(output_folder, output_filename)

                try:
                    # 1. Đọc ảnh (nên đọc ảnh xám nếu có, nếu không thì chuyển)
                    img = cv2.imread(input_path)
                    if img is None: continue

                    # Nếu ảnh là màu, chuyển sang xám
                    if len(img.shape) == 3:
                        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    else:
                        gray = img # Giả sử ảnh đã là xám

                    # 2. Chuyển sang ảnh nhị phân (Chữ trắng, Nền đen để Closing hoạt động)
                    # Dùng Otsu để tự động tìm ngưỡng
                    _, binary_inv = cv2.threshold(gray, 0, 255,
                                                  cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

                    # 3. Áp dụng Phép Đóng (Closing)
                    # Tạo kernel hình vuông
                    kernel = np.ones((kernel_size, kernel_size), np.uint8)
                    # Closing = Dilation -> Erosion
                    closing_img = cv2.morphologyEx(binary_inv, cv2.MORPH_CLOSE, kernel)

                    # 4. Đảo ngược lại để có Chữ đen, Nền trắng
                    final_image = cv2.bitwise_not(closing_img)

                    # 5. Lưu ảnh đen/trắng đã làm đậm nét
                    cv2.imwrite(output_path, final_image)
                    processed_files.append(output_path)
                    print(f"  - Đã làm đậm nét và lưu: {output_filename}")

                except Exception as e:
                    print(f"  - Lỗi khi xử lý '{filename}': {e}")

        print(f"\n[Thicken] Hoàn tất! Đã xử lý {len(processed_files)} ảnh.")
        return processed_files

    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy thư mục đầu vào '{input_folder}'.")
        return []
    
# ----- THICKEN STROKES (Closing) SINGLE IMAGE -----
def thicken_strokes_closing_single(img_array, kernel_size=2):
    """
    Làm đậm nét chữ trên một ảnh (Numpy array) đã cắt bằng phép Đóng (Closing).
    Trả về ảnh đen/trắng đã làm đậm nét.

    Args:
        img_array (numpy.ndarray): Ảnh đầu vào (có thể là màu hoặc xám).
        kernel_size (int): Kích thước kernel cho phép Đóng.

    Returns:
        numpy.ndarray: Ảnh đen/trắng đã làm đậm nét, hoặc None nếu lỗi.
    """
    if img_array is None or img_array.size == 0:
        print("[Thicken] Lỗi: Ảnh đầu vào rỗng.")
        return None

    try:
        # 1. Chuyển sang ảnh xám nếu cần
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
        else:
            gray = img_array # Giả sử đã là xám

        # 2. Chuyển sang ảnh nhị phân (Chữ trắng, Nền đen để Closing)
        _, binary_inv = cv2.threshold(gray, 0, 255,
                                      cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # 3. Áp dụng Phép Đóng (Closing)
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        closing_img = cv2.morphologyEx(binary_inv, cv2.MORPH_CLOSE, kernel)

        # 4. Đảo ngược lại để có Chữ đen, Nền trắng
        final_image = cv2.bitwise_not(closing_img)

        print("[Thicken] Đã áp dụng làm đậm nét.")
        return final_image

    except Exception as e:
        print(f"[Thicken] Lỗi khi làm đậm nét: {e}")
        return None