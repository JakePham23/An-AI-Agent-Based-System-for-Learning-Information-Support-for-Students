from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import agents

# 1. ĐỊNH NGHĨA STATE (Bộ nhớ chung của quy trình)
class AgentState(TypedDict):
    query: str
    analysis: dict          # Chứa Intent, Keywords, Status
    orchestrator_decision: dict
    content_data: str       # Kết quả Curator
    prerequisites_data: str # Kết quả Prerequisite
    path_plan: str          # Kết quả Planner
    final_response: str     # Kết quả Explainer
    reflection: dict        # Kết quả Reflection

# 2. ĐỊNH NGHĨA CÁC NODES (Hành động)

def analyze_node(state: AgentState):
    print("--- [1] Analyzer: Đang phân tích câu hỏi... ---")
    analysis = agents.query_analyzer_agent(state["query"])
    return {"analysis": analysis}

def orchestrator_node(state: AgentState):
    print("--- [1.2] Orchestrator: Đang điều phối luồng xử lý... ---")
    decision = agents.orchestrator_agent(state["analysis"])
    print(f"-> Quyết định: {decision.get('next_agents')} | Lý do: {decision.get('reasoning')}")
    return {"orchestrator_decision": decision}

def curator_node(state: AgentState):
    print("--- [2a] Curator: Đang lấy nội dung môn học... ---")
    keywords = state["analysis"].get("keywords", [state["query"]])
    content = agents.content_curator_agent(keywords)
    return {"content_data": content}

def prerequisite_node(state: AgentState):
    print("--- [2b] Prerequisite: Đang tìm môn tiên quyết... ---")
    keywords = state["analysis"].get("keywords", [state["query"]])
    prereq = agents.prerequisite_finder_agent(keywords)
    return {"prerequisites_data": prereq}

def planner_node(state: AgentState):
    print("--- [3] Path Planner: Đang lên lộ trình... ---")
    plan = agents.path_planner_agent(
        content=state.get("content_data", ""),
        prerequisites=state.get("prerequisites_data", "")
    )
    return {"path_plan": plan}

def explainer_node(state: AgentState):
    print("--- [4] Explainer: Đang tổng hợp câu trả lời... ---")
    response = agents.explainer_agent(
        original_query=state["query"],
        content=state.get("content_data", ""),
        prerequisites=state.get("prerequisites_data", ""),
        plan=state.get("path_plan", "")
    )
    return {"final_response": response}

def reflection_node(state: AgentState):
    print("--- [5] Reflection: Kiểm tra chất lượng... ---")
    critique = agents.reflection_agent(
        original_query=state["query"],
        final_response=state["final_response"]
    )
    if not critique['is_satisfactory']:
        print(f"!!! CẢNH BÁO: {critique['critique']}")
    return {"reflection": critique}

# Đây là hàm điều hướng (Conditional Edge)
def router_logic(state: AgentState):
    decision = state["orchestrator_decision"]
    next_agents = decision.get("next_agents", [])
    
    # Trả về danh sách các node tiếp theo đúng như Agent quyết định
    # LangGraph sẽ tự động chạy song song nếu list có nhiều node
    return next_agents

# Đây là hàm quyết định xem có đánh giá kết quả (Conditional Edge)
def should_reflect(state: AgentState):
    """
    Quyết định xem có cần chạy Reflection không.
    - Nếu là ACADEMIC: Cần kiểm tra kỹ lưỡng -> Chạy Reflection.
    - Nếu là SOCIAL / OFF_TOPIC: Chỉ là xã giao -> Bỏ qua Reflection (END luôn).
    """
    analysis = state.get("analysis", {})
    category = analysis.get("category", "ACADEMIC") # Mặc định là Academic cho an toàn
    
    print(f"--- [Check Reflection] Category: {category} ---")

    if category in ["SOCIAL", "OFF_TOPIC"]:
        return END  # Kết thúc ngay lập tức
    
    return "reflection" # Chuyển sang bước kiểm định

# 3. XÂY DỰNG GRAPH

workflow = StateGraph(AgentState)

# Thêm Nodes
workflow.add_node("analyzer", analyze_node)
workflow.add_node("orchestrator", orchestrator_node)
workflow.add_node("curator", curator_node)
workflow.add_node("prerequisite", prerequisite_node)
workflow.add_node("planner", planner_node)
workflow.add_node("explainer", explainer_node)
workflow.add_node("reflection", reflection_node)

# Thiết lập Edges (Luồng đi)

# B1: Start -> Analyzer
workflow.set_entry_point("analyzer")

# Analyzer -> Orchestrator (Agent này chạy xong mới quyết định đi đâu)
workflow.add_edge("analyzer", "orchestrator")

# B2: Analyzer -> Orchestrator -> (Curator // Prerequisite)
# Sử dụng add_conditional_edges để Orchestrator quyết định đường đi
workflow.add_conditional_edges(
    "orchestrator",
    router_logic,
    {
        "curator": "curator",
        "prerequisite": "prerequisite",
        "planner": "planner",
        "explainer": "explainer"
    }
)

# B3: Gom kết quả (Fan-in) về Planner
# Lưu ý: Trong LangGraph, để Planner nhận kết quả từ cả 2 nhánh song song,
# cả 2 nhánh phải trỏ về Planner. Planner sẽ chạy khi các nhánh hoàn tất.
workflow.add_edge("curator", "prerequisite")
workflow.add_edge("prerequisite", "planner")

# B4: Planner -> Explainer -> Reflection -> END
workflow.add_edge("planner", "explainer")

workflow.add_conditional_edges(
    "explainer",       # Nguồn
    should_reflect,    # Hàm logic
    {
        "reflection": "reflection", # Nếu hàm trả về "reflection" -> đi tiếp
        END: END                    # Nếu hàm trả về END -> dừng luôn
    }
)

workflow.add_edge("reflection", END)

# Compile
checkpointer = MemorySaver()
app = workflow.compile(checkpointer=checkpointer)