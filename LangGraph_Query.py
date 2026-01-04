import os
import asyncio
import operator
from typing import Annotated, Literal, TypedDict

# Import từ thư viện LangChain/LangGraph
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages

# Import LightRAG (từ file main.py hoặc setup tương tự)
# Đảm bảo bạn copy các hàm wrapper Ollama/LM Studio vào đây hoặc import từ file cũ
from lightrag import LightRAG, QueryParam
from lightrag.utils import EmbeddingFunc
from openai import AsyncOpenAI
import numpy as np

# --- 1. CẤU HÌNH LIGHTRAG (Giống hệt bài trước) ---
WORKING_DIR = "./output"
OLLAMA_BASE_URL = "http://127.0.0.1:1234/v1" # Hoặc http://localhost:11434/v1
LLM_MODEL = "qwen/qwen2.5-vl-7b"
EMBEDDING_MODEL = "gaianet/text-embedding-nomic-embed-text-v1.5-embedding"
EMBEDDING_DIM = 768

# Hàm Wrapper (Copy lại để code chạy độc lập)
async def llm_model_func(prompt, system_prompt=None, history_messages=[], **kwargs):
    client = AsyncOpenAI(base_url=OLLAMA_BASE_URL, api_key="lm-studio")
    messages = []
    if system_prompt: messages.append({"role": "system", "content": system_prompt})
    if history_messages: messages.extend(history_messages)
    messages.append({"role": "user", "content": prompt})
    response = await client.chat.completions.create(
        model=LLM_MODEL, messages=messages, temperature=0
    )
    return response.choices[0].message.content

async def embedding_func(texts: list[str]) -> np.ndarray:
    client = AsyncOpenAI(base_url=OLLAMA_BASE_URL, api_key="lm-studio")
    tasks = [client.embeddings.create(model=EMBEDDING_MODEL, input=t) for t in texts]
    responses = await asyncio.gather(*tasks)
    return np.array([r.data[0].embedding for r in responses])

# Khởi tạo Global LightRAG Instance
rag_instance = LightRAG(
    working_dir=WORKING_DIR,
    llm_model_func=llm_model_func,
    embedding_func=EmbeddingFunc(embedding_dim=EMBEDDING_DIM, max_token_size=8192, func=embedding_func)
)

# --- 2. TẠO TOOL (CÔNG CỤ TRA CỨU) ---
# Đây là bước biến LightRAG thành một "Hàm" để Agent gọi

@tool
async def search_knowledge_base(query: str):
    """
    Sử dụng công cụ này để tra cứu thông tin về chương trình đào tạo, môn học, 
    hoặc các quy định học vụ. Đầu vào là câu hỏi cụ thể.
    """
    print(f"🕵️ Agent đang tra cứu LightRAG: '{query}'")
    
    # Gọi LightRAG chế độ Hybrid (mạnh nhất)
    # Lưu ý: LightRAG cần được initialize trước khi gọi
    result = await rag_instance.aquery(query, param=QueryParam(mode="hybrid"))
    return result

# Danh sách công cụ Agent được dùng
tools = [search_knowledge_base]

# --- 3. ĐỊNH NGHĨA STATE (TRẠNG THÁI) ---
class AgentState(TypedDict):
    # Lưu lịch sử chat, add_messages giúp tự động nối tin nhắn mới vào cũ
    messages: Annotated[list[BaseMessage], add_messages]

# --- 4. KHỞI TẠO LLM VÀ BIND TOOLS ---
# Agent cần một LLM thông minh để quyết định (Router)
llm = ChatOpenAI(
    base_url=OLLAMA_BASE_URL,
    api_key="lm-studio",
    model=LLM_MODEL,
    temperature=0
)

# "Dạy" LLM biết về các công cụ
llm_with_tools = llm.bind_tools(tools)

# --- 5. ĐỊNH NGHĨA CÁC NODE (BƯỚC XỬ LÝ) ---

# Node 1: Suy nghĩ (Agent quyết định làm gì)
async def agent_node(state: AgentState):
    print("🤔 Agent đang suy nghĩ...")
    messages = state["messages"]
    response = await llm_with_tools.ainvoke(messages)
    return {"messages": [response]}

# Node 2: Thực thi công cụ (ToolNode có sẵn của LangGraph)
tool_node = ToolNode(tools)

# Hàm điều kiện: Kiểm tra xem Agent có muốn dùng Tool không?
def should_continue(state: AgentState) -> Literal["tools", END]:
    messages = state["messages"]
    last_message = messages[-1]
    
    # Nếu LLM sinh ra yêu cầu gọi tool -> Chuyển sang node 'tools'
    if last_message.tool_calls:
        return "tools"
    # Nếu không (trả lời luôn) -> Kết thúc
    return END

# --- 6. XÂY DỰNG GRAPH (SƠ ĐỒ LUỒNG) ---
workflow = StateGraph(AgentState)

# Thêm các Node
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)

# Thêm các Edge (Đường đi)
workflow.add_edge(START, "agent") # Bắt đầu -> Vào Agent suy nghĩ

# Từ Agent -> Kiểm tra điều kiện
workflow.add_conditional_edges(
    "agent",
    should_continue,
)

# Từ Tools -> Quay lại Agent (Để Agent đọc kết quả tool và tổng hợp câu trả lời)
workflow.add_edge("tools", "agent")

# Compile thành ứng dụng chạy được
app = workflow.compile()

# --- 7. CHẠY ỨNG DỤNG ---
async def main():
    print("🚀 Đang khởi động Agentic RAG...")
    # Khởi tạo LightRAG storage (quan trọng)
    await rag_instance.initialize_storages()
    
    print("\n🤖 Sẵn sàng! (Gõ 'exit' để thoát)")
    
    while True:
        user_input = input("\n👤 Bạn: ")
        if user_input.lower() in ["exit", "quit"]:
            break
            
        # Gửi tin nhắn vào Graph
        # stream_mode="values" giúp ta thấy từng bước cập nhật của State
        inputs = {"messages": [HumanMessage(content=user_input)]}
        
        async for event in app.astream(inputs, stream_mode="values"):
            # In ra phản hồi cuối cùng từ AI
            message = event["messages"][-1]
            if isinstance(message, BaseMessage) and message.content:
                # Chỉ in khi có nội dung thực sự (bỏ qua các bước gọi tool ngầm)
                # Hack nhẹ để tránh in lặp, trong thực tế dùng UI sẽ đẹp hơn
                pass 
        
        # In kết quả cuối cùng
        final_state = await app.ainvoke(inputs)
        final_response = final_state["messages"][-1].content
        print(f"🤖 Agent: {final_response}")

if __name__ == "__main__":
    asyncio.run(main())