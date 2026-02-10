from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from agents.llm import get_llm
from lightrag_api import query_lightrag

def prerequisite_finder_agent(query: str):
    rag_response = query_lightrag(f"What are prerequisites for: {query}?", mode="local")
    
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template("""
    Bạn là Prerequisite Finder Agent.
    Nhiệm vụ: Xác định các kiến thức nền tảng cần thiết trước khi học chủ đề này dựa trên dữ liệu graph.
        - Chỉ giữ lại các ý chính, bỏ qua chi tiết rườm rà.
        - Giới hạn độ dài dưới 300 từ.
    Nếu không thấy dữ liệu, hãy trả về chuỗi rỗng.
    Graph Data:
    {rag_data}
    """)
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"rag_data": rag_response})