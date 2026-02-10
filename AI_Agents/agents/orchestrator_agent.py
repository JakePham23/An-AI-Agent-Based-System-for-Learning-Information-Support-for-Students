from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from agents.llm import get_llm

def orchestrator_agent(analysis_result: dict):
    llm = get_llm()
    
    system_prompt = """
    Bạn là Orchestrate Agent, trung tâm điều phối hệ thống hỗ trợ học tập.
    Nhiệm vụ của bạn là điều hướng, không được tự ý trả lời kiến thức chuyên môn.
    
    Dựa trên bản phân tích từ Analyzer Agent: {analysis}
    
    QUY TẮC ĐIỀU HƯỚNG:
        1. Nếu category là "SOCIAL" (Chào hỏi/Cảm ơn) -> Kích hoạt ["explainer"]. (Không cần tra cứu).
        2. Nếu category là "OFF_TOPIC" (Nấu ăn, việc riêng) -> Kích hoạt ["explainer"]. (Để từ chối khéo).
        3. Nếu category là "ACADEMIC":
            - Nếu cần thông tin môn học/lộ trình -> Kích hoạt ["curator"].
            - Nếu chỉ hỏi đơn giản không cần dữ liệu sâu -> Kích hoạt ["curator"].
    
    Output JSON duy nhất:
    {{
        "next_agents": ["tên_agent_1", "tên_agent_2"],
        "reasoning": "Lý do điều hướng ngắn gọn"
    }}
    Lưu ý: Tên agent hợp lệ chỉ gồm: "curator", "prerequisite", "planner", "explainer".
    """
    
    prompt = ChatPromptTemplate.from_template(system_prompt)
    chain = prompt | llm | JsonOutputParser()
    
    return chain.invoke({"analysis": analysis_result})