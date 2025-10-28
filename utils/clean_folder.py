import os
import glob   # <-- Thư viện để tìm file

def clean_folder(folder_path):
    print(f"\n[Setup] Dọn dẹp thư mục: {folder_path}")
    if not os.path.exists(folder_path):
        print(f"  - Thư mục chưa tồn tại, không cần dọn.")
        return # Không cần làm gì nếu thư mục chưa có

    files_to_delete = glob.glob(os.path.join(folder_path, '*.jpg')) + \
                      glob.glob(os.path.join(folder_path, '*.png')) + \
                      glob.glob(os.path.join(folder_path, '*.jpeg'))
                      
    if not files_to_delete:
        print("  - Thư mục trống, không có file nào để xóa.")
        return

    deleted_count = 0
    for f in files_to_delete:
        try:
            os.remove(f)
            deleted_count += 1
        except Exception as e:
            print(f"  - Lỗi khi xóa file '{f}': {e}")
            
    print(f"  - Đã xóa {deleted_count} file ảnh cũ.")