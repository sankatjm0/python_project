# File: handle_image/recognition.py
# (Hoặc bạn có thể đặt trực tiếp vào main.py nếu muốn)

from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg
from PIL import Image
import os
import time

def recognize_text_from_folder(input_folder, output_file="result.txt"):
    """
    HÀM NHẬN DẠNG:
    Đọc tất cả ảnh dòng đã cắt trong thư mục input_folder,
    nhận dạng bằng VietOCR (batch mode), và lưu kết quả ra file.
    """
    
    print("\n[Recognition] Đang khởi tạo mô hình VietOCR...")
    try:
        # Sử dụng mô hình vgg_transformer (hoặc vgg_seq2seq nếu bạn muốn thử)
        config = Cfg.load_config_from_name('vgg_transformer')
        config['device'] = 'cpu' # Chạy trên CPU
        predictor = Predictor(config)
        print("[Recognition] Khởi tạo VietOCR thành công.")
    except Exception as e:
        print(f"[Recognition] Lỗi khởi tạo VietOCR: {e}")
        print("Vui lòng đảm bảo bạn đã cài đặt: pip install vietocr")
        return None # Trả về None nếu không khởi tạo được

    images_to_predict = []
    image_filenames = [] 
    recognized_full_text = ""

    print(f"[Recognition] Đang tải ảnh từ thư mục '{input_folder}'...")

    # 1. Tải ảnh vào danh sách
    try:
        # Sắp xếp file để đảm bảo thứ tự dòng đúng (line_1, line_2, ...)
        file_list = sorted(os.listdir(input_folder)) 
        
        for filename in file_list:
            if filename.lower().endswith((".png")):
                file_path = os.path.join(input_folder, filename)
                try:
                    # Mở ảnh và thêm vào danh sách
                    img = Image.open(file_path)
                    images_to_predict.append(img)
                    image_filenames.append(filename)
                except Exception as e:
                    print(f"Lỗi khi tải ảnh '{file_path}': {e}")
                    
    except FileNotFoundError:
         print(f"Lỗi: Không tìm thấy thư mục '{input_folder}' chứa ảnh đã cắt.")
         return None

    # 2. Thực hiện Nhận dạng Hàng loạt (Batch Prediction)
    if images_to_predict:
        print(f"[Recognition] Đã tải {len(images_to_predict)} ảnh. Bắt đầu nhận dạng hàng loạt...")
        start_time = time.time() # Bắt đầu đếm giờ

        try:
            # Gọi predict_batch CHỈ 1 LẦN
            recognized_texts = predictor.predict_batch(images_to_predict)
            
            end_time = time.time()
            print(f"Hoàn tất nhận dạng! (Thời gian: {end_time - start_time:.2f} giây)")

            # 3. Xử lý và Lưu kết quả
            print("\n--- KẾT QUẢ NHẬN DẠNG ---")
            for i in range(len(recognized_texts)):
                filename = image_filenames[i]
                text = recognized_texts[i]
                
                print(f"  - '{filename}': {text}")
                recognized_full_text += text + "\n" # Nối text và thêm ký tự xuống dòng
            
            # Lưu ra file
            try:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(recognized_full_text)
                print(f"\nĐã lưu toàn bộ kết quả vào file: '{output_file}'")
            except Exception as e:
                print(f"Lỗi khi lưu file '{output_file}': {e}")
                
            return recognized_full_text # Trả về chuỗi text cuối cùng
            
        except Exception as e:
            print(f"Lỗi nghiêm trọng khi chạy predict_batch: {e}")
            return None # Trả về None nếu có lỗi

    else:
        print("[Recognition] Không tìm thấy ảnh nào hợp lệ trong thư mục để nhận dạng.")
        return "" # Trả về chuỗi rỗng nếu không có ảnh

# # --- CÁCH SỬ DỤNG (Ví dụ trong main.py) ---
# if __name__ == "__main__":
#     # Giả sử bạn đã chạy code crop và có thư mục này
#     folder_with_cropped_lines = 'final_cropped_lines_v4' 
#     final_result_file = 'result.txt'
    
#     # Gọi hàm nhận dạng
#     final_text = recognize_text_from_folder(folder_with_cropped_lines, final_result_file)
    
#     if final_text is not None:
#          print("\n--- TOÀN BỘ VĂN BẢN (TRONG MAIN) ---")
#          print(final_text)
#     else:
#         print("\nQuy trình nhận dạng thất bại.")