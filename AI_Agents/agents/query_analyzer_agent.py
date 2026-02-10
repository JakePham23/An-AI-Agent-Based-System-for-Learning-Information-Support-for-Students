from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from agents.llm import get_llm

def query_analyzer_agent(text: str):
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template("""
    Bạn là chuyên gia phân tích yêu cầu học thuật. Hãy phân tích câu hỏi: "{text}"
    
    
    Trả về định dạng JSON thuần túy (không markdown) gồm:
    {{
        "category": Chọn 1 trong 3 nhóm sau:
            - "ACADEMIC": Hỏi về môn học, tín chỉ, lộ trình, kiến thức CNTT, quy chế trường.
            - "SOCIAL": Chào hỏi, cảm ơn, tạm biệt, khen chê xã giao.
            - "OFF_TOPIC": Hỏi về nấu ăn, chính trị, giải trí, hoặc các vấn đề không liên quan đến học tập/trường lớp.
        "intent": "knowledge_lookup" hoặc "learning_path" hoặc "schedule_request",
        "complexity": 1-5,
        "keywords": ["từ khóa 1", "từ khóa 2"],
        "status": "VALID" hoặc "NEED_CLARIFICATION",
        "missing_info": "những gì cần hỏi thêm nếu thiếu"
    }}
    """)
    chain = prompt | llm | JsonOutputParser()
    return chain.invoke({"text": text})