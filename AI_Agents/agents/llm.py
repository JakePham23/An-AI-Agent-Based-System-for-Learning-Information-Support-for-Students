from langchain_ollama import ChatOllama

def get_llm():
    return ChatOllama(
        model="qwen3:4b",
        temperature=0,
        # --- Cấu hình tối ưu cho Qwen3:4b ---
        num_ctx=4096,
        num_thread=4,
    )