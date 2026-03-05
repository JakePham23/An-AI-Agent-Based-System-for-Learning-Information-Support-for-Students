from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid
import uvicorn

# Import graph từ file logic
from main import app 

server = FastAPI(
    title="HCMUS Academic Agent API",
    description="API cung cấp lộ trình học tập dựa trên LangGraph"
)

class QueryRequest(BaseModel):
    query: str
    # thread_id giúp định danh phiên chat của người dùng (ví dụ: Nam_Session_01)
    thread_id: Optional[str] = None 

class QueryResponse(BaseModel):
    thread_id: str
    answer: str
    analysis: Optional[dict] = None
    reflection: Optional[dict] = None

@server.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    # 1. Tạo hoặc lấy thread_id
    thread_id = request.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    try:
        # 2. Sử dụng ainvoke (Async Invoke)
        inputs = {"query": request.query}
        result = await app.ainvoke(inputs, config=config)
        
        # 3. Trả kết quả về cho Client
        return QueryResponse(
            thread_id=thread_id,
            answer=result.get("final_response", "Xin lỗi, mình không tìm được câu trả lời."),
            analysis=result.get("analysis"),
            reflection=result.get("reflection")
        )
        
    except Exception as e:
        # Log lỗi chi tiết ở đây nếu cần
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống Agent: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("api:server", host="0.0.0.0", port=8000, reload=True)