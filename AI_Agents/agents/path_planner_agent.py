from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from agents.llm import get_llm

def path_planner_agent(content: str, prerequisites: str):
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template("""
    Dựa trên:
    1. Nội dung: {content}
    2. Tiên quyết: {prerequisites}
    
    Hãy xây dựng lộ trình học tập logic từng bước (Step-by-step).
    """)
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"content": content, "prerequisites": prerequisites})