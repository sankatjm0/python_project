# File: find_vietocr_model_path.py

from vietocr.tool.config import Cfg
from vietocr.tool.predictor import Predictor # Import Predictor để kích hoạt tải model
import os

try:
    # 1. Tải cấu hình model bạn muốn tìm
    model_name = 'vgg_transformer' # Hoặc 'vgg_seq2seq', etc.
    config = Cfg.load_config_from_name(model_name)
    
    # 2. Lấy đường dẫn weights mặc định TỪ CẤU HÌNH
    #   Hàm load_config_from_name thường đã tự xác định đường dẫn này
    #   và lưu trong config['weights'].
    #   Nó cũng có thể đã kiểm tra và tải model về nếu cần.
    
    #   Để chắc chắn model được tải về, ta thử khởi tạo Predictor
    print(f"Đang thử khởi tạo Predictor với model '{model_name}' để đảm bảo model được tải...")
    config['device'] = 'cpu' # Chỉ cần CPU để kiểm tra đường dẫn
    try:
         # Việc khởi tạo này sẽ kích hoạt download nếu file chưa có
        predictor_temp = Predictor(config) 
        print("Khởi tạo thành công.")
    except Exception as init_err:
        print(f"Lỗi khi khởi tạo Predictor (có thể do lỗi tải model): {init_err}")
        # Dù lỗi, config['weights'] vẫn có thể chứa đường dẫn dự kiến
        pass # Tiếp tục để kiểm tra đường dẫn trong config

    # 3. In ra đường dẫn trong config
    if 'weights' in config and config['weights']:
        model_path = config['weights']
        print(f"\nĐường dẫn model '{model_name}.pth' được cấu hình là:")
        print(model_path)
        
        # 4. Kiểm tra xem file có thực sự tồn tại ở đó không
        if os.path.exists(model_path):
            print("\n=> File model ĐÃ TỒN TẠI tại đường dẫn trên.")
            print("Bạn cần copy file này vào project và thêm vào 'datas' của PyInstaller.")
        else:
            print("\n=> CẢNH BÁO: File model KHÔNG TỒN TẠI tại đường dẫn trên.")
            print("   - Hãy thử chạy code VietOCR chính của bạn một lần để nó tải model về.")
            print(f"   - Hoặc kiểm tra các thư mục cache như ~/.cache/vietocr")
            
    else:
        print(f"\nKhông tìm thấy đường dẫn 'weights' trong config cho model '{model_name}'.")

except Exception as e:
    print(f"Đã xảy ra lỗi: {e}")