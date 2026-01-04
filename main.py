import os
import glob
import time
import asyncio
import numpy as np
from lightrag import LightRAG, QueryParam
from lightrag.utils import EmbeddingFunc
from openai import AsyncOpenAI

# --- CẤU HÌNH ---
WORKING_DIR = "./output"
INPUT_DIR = "./input"             
OLLAMA_BASE_URL = "http://127.0.0.1:1234/v1"
LLM_MODEL = "qwen/qwen2.5-vl-7b"          
EMBEDDING_MODEL = "gaianet/text-embedding-nomic-embed-text-v1.5-embedding" 
EMBEDDING_DIM = 768 

# Tạo folder output nếu chưa có
if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)

# --- HÀM WRAPPER CHO LM-STUDIO (LLM) ---
async def llm_model_func(prompt, system_prompt=None, history_messages=[], keyword_extraction=False, **kwargs):
    client = AsyncOpenAI(base_url=OLLAMA_BASE_URL, api_key="lm-studio")
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if history_messages:
        messages.extend(history_messages)
    messages.append({"role": "user", "content": prompt})
    
    response = await client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=kwargs.get("temperature", 0),
        top_p=kwargs.get("top_p", 1),
        n=kwargs.get("n", 1),
        max_tokens=kwargs.get("max_tokens", 4096),
    )
    return response.choices[0].message.content

# --- HÀM WRAPPER CHO LM-STUDIO (EMBEDDING) ---
async def embedding_func(texts: list[str]) -> np.ndarray:
    client = AsyncOpenAI(base_url=OLLAMA_BASE_URL, api_key="lm-studio")
    response = await client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts
    )
    return np.array([item.embedding for item in response.data])

# --- HÀM ĐỌC DỮ LIỆU TỪ FOLDER ---
def load_data_from_folder(folder_path):
    if not os.path.exists(folder_path):
        print(f"⚠️ Folder '{folder_path}' chưa tồn tại.")
        return ""

    files = glob.glob(os.path.join(folder_path, "*.txt"))
    if not files:
        print(f"⚠️ Không tìm thấy file .txt nào trong '{folder_path}'")
        return ""

    print(f"📂 Tìm thấy {len(files)} file trong '{folder_path}'. Đang đọc...")
    all_content = []
    
    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    file_name = os.path.basename(file_path)
                    formatted_content = f"--- Tài liệu: {file_name} ---\n{content}"
                    all_content.append(formatted_content)
        except Exception as e:
            print(f"❌ Lỗi đọc file {file_path}: {e}")

    return "\n\n".join(all_content)

# --- HÀM INSERT VỚI RETRY LOGIC (SỬA LẠI THÀNH SYNC) ---
def insert_text(rag, folder_path):
    # 1. Đọc dữ liệu
    full_text = load_data_from_folder(folder_path)
    if not full_text:
        print("⚠️ Không có dữ liệu để insert.")
        return

    # 2. Thực hiện Insert với cơ chế Retry
    retries = 0
    max_retries = 3
    while retries < max_retries:
        try:
            print(f"⚙️ Đang Index dữ liệu (Lần thử {retries + 1})...")
            
            # SỬA LỖI Ở ĐÂY: Dùng .insert() thay vì .async_insert()
            # Và KHÔNG dùng await
            rag.insert(full_text)
            
            print("✅ Index hoàn tất!")
            break
        except Exception as e:
            retries += 1
            print(f"❌ Insert thất bại, đang thử lại ({retries}/{max_retries}), lỗi: {e}")
            time.sleep(10)
            
    if retries == max_retries:
        print("❌ Insert thất bại sau khi đã thử hết số lần tối đa.")

# --- HÀM KHỞI TẠO RAG (ASYNC) ---
async def initialize_rag():
    print(f"🚀 Khởi tạo LightRAG với LM Studio (Model: {LLM_MODEL})...")
    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=llm_model_func,
        llm_model_max_async=2,  # Giảm số lượng request song song để tránh quá tải local LLM
        default_llm_timeout=600, # Tăng timeout lên 10 phút
        embedding_func=EmbeddingFunc(
            embedding_dim=EMBEDDING_DIM, 
            max_token_size=8192,
            func=embedding_func
        )
    )
    await rag.initialize_storages() 
    return rag

# --- MAIN FLOW (TÁCH BIỆT) ---
def main():
    # Bước 1: Khởi tạo RAG (Chạy trong môi trường Async để setup storage)
    rag = asyncio.run(initialize_rag())
    
    # Bước 2: Insert Data (Chạy Sync ở ngoài để tránh lỗi loop)
    # Hàm rag.insert bên trong tự quản lý loop để gọi các hàm async LLM
    insert_text(rag, INPUT_DIR)



if __name__ == "__main__":
    main()