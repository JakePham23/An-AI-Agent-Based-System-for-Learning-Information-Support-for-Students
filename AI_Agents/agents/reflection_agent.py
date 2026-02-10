from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from agents.llm import get_llm

def reflection_agent(original_query: str, final_response: str):
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template("""
    Bạn là Reflection Agent (Kiểm soát viên).
    Câu hỏi gốc: {query}
    Câu trả lời của hệ thống: {response}
    
    Hãy đánh giá xem câu trả lời có giải quyết đúng intent không? Có thiếu thông tin quan trọng (như môn tiên quyết) không?
    
    Output JSON:
    {{
        "is_satisfactory": true/false,
        "critique": "Nhận xét nếu chưa đạt (hoặc 'Good' nếu đạt)",
        "missing_entities": []
    }}
    """)
    chain = prompt | llm | JsonOutputParser()
    return chain.invoke({"query": original_query, "response": final_response})