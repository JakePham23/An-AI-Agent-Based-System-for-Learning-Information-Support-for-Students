import json
import os
import shutil
from datetime import datetime, timezone

# --- CẤU HÌNH ---
# Folder chứa file json status (thường là working_dir)
RAG_STORAGE_DIR = "./rag_storage" 
# File json cụ thể (Dựa trên tên file bạn cung cấp trong prompt)
STATUS_FILE_NAME = "kv_store_doc_status.json"

# Folder chứa các file .txt gốc để copy đi
INPUT_DIR = "./input/__enqueued__"

# Folder đích để chứa các file lọc được
DEST_DIR = "./filtered_docs_240pm"

# --- CẤU HÌNH THỜI GIAN MỐC (2:40 PM ngày 30/12/2025) ---
TARGET_YEAR = 2025
TARGET_MONTH = 12
TARGET_DAY = 30
TARGET_HOUR = 14  # 14 giờ (2 PM)
TARGET_MINUTE = 40
TARGET_SECOND = 0

def main():
    status_path = os.path.join(RAG_STORAGE_DIR, STATUS_FILE_NAME)
    
    # Kiểm tra file json tồn tại
    if not os.path.exists(status_path):
        print(f"❌ LỖI: Không tìm thấy file tại {status_path}")
        print("   -> Hãy kiểm tra lại tên folder RAG_STORAGE_DIR.")
        return

    # Tạo folder đích nếu chưa có
    if not os.path.exists(DEST_DIR):
        os.makedirs(DEST_DIR)

    # 1. TẠO MỐC THỜI GIAN (TIMESTAMP) ĐỂ SO SÁNH
    # Giả sử giờ hệ thống của bạn là Local Time (Việt Nam?), ta tạo timestamp từ mốc này
    target_dt = datetime(TARGET_YEAR, TARGET_MONTH, TARGET_DAY, TARGET_HOUR, TARGET_MINUTE, TARGET_SECOND)
    target_timestamp = target_dt.timestamp()
    
    print(f"🎯 Đang lọc các file xử lý sau: {target_dt} (Timestamp: {target_timestamp})")
    print(f"📂 Đọc dữ liệu từ: {status_path}")

    try:
        with open(status_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Lỗi đọc JSON: {e}")
        return

    count = 0
    missing_files = 0

    print("-" * 90)
    print(f"{'TÊN FILE':<35} | {'THỜI GIAN XỬ LÝ (Local)':<25} | {'TRẠNG THÁI'}")
    print("-" * 90)

    for doc_id, info in data.items():
        # 2. LẤY THÔNG TIN TỪ JSON
        file_name = info.get("file_path") # Lấy tên file chính xác từ JSON (VD: CSC16110.txt)
        
        # Lấy thời gian xử lý. Ưu tiên dùng processing_start_time trong metadata (dạng số Unix)
        # Nếu không có thì dùng created_at (dạng chuỗi ISO)
        metadata = info.get("metadata", {})
        proc_start_time = metadata.get("processing_start_time")
        
        if proc_start_time is None:
            # Fallback nếu không có metadata, thử parse created_at
            # (Phần này xử lý thêm nếu cần, nhưng mẫu bạn đưa có metadata)
            continue

        # 3. SO SÁNH THỜI GIAN
        # Nếu thời gian file này >= thời gian mốc
        if proc_start_time >= target_timestamp:
            count += 1
            
            # Format thời gian để in ra cho đẹp
            human_time = datetime.fromtimestamp(proc_start_time).strftime('%Y-%m-%d %H:%M:%S')
            
            # 4. THỰC HIỆN COPY
            if file_name:
                src_file = os.path.join(INPUT_DIR, file_name)
                dst_file = os.path.join(DEST_DIR, file_name)
                
                if os.path.exists(src_file):
                    shutil.copy2(src_file, dst_file)
                    status = "✅ Đã Copy"
                else:
                    status = "⚠️ File gốc không thấy"
                    missing_files += 1
            else:
                status = "⚠️ Không có tên file"
                file_name = "Unknown"

            print(f"{file_name:<35} | {human_time:<25} | {status}")

    print("-" * 90)
    print(f"🎉 HOÀN TẤT!")
    print(f"📊 Tổng file thỏa điều kiện: {count}")
    print(f"📂 Các file đã được copy vào: {DEST_DIR}")
    if missing_files > 0:
        print(f"⚠️ Lưu ý: Có {missing_files} file có trong danh sách nhưng không tìm thấy file gốc trong '{INPUT_DIR}' để copy.")

if __name__ == "__main__":
    main()