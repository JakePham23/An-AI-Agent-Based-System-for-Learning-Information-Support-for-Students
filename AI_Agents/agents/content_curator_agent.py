from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from agents.llm import get_llm
from lightrag_api import query_lightrag

def content_curator_agent(keywords: list):
    query = " ".join(keywords)
    rag_data = query_lightrag(query, mode="mix")
    
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template("""
    Dựa trên dữ liệu thô từ LightRAG: {rag_data}
    Hãy tóm tắt nội dung cốt lõi của môn học/chủ đề này.
    Nhiệm vụ: Tóm tắt nội dung môn học này một cách CÔ ĐỌNG (Concise).
        - Chỉ giữ lại các ý chính, bỏ qua chi tiết rườm rà.
        - Giới hạn độ dài dưới 300 từ.
    """)
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"rag_data": rag_data})