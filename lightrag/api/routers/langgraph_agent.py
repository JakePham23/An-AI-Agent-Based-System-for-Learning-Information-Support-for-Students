import os
import logging
from typing import Annotated, Literal, TypedDict, List
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from lightrag import LightRAG, QueryParam
from simpleaichat import AIChat

logger = logging.getLogger(__name__)

# Shared Graph State
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def create_agent_app(rag_instance: LightRAG):
    """
    Creates and compiles a LangGraph agent application that uses the provided LightRAG instance as a tool.
    """
    
    # Define the tool that uses LightRAG
    @tool
    async def search_knowledge_base(query: str):
        """
        Use this tool to query the LightRAG knowledge base for information.
        Useful for answering questions based on the stored documents and graph data.
        """
        logger.info(f"Agent using LightRAG to search: {query}")
        try:
            # Use hybrid mode for balanced retrieval
            result = await rag_instance.aquery(query, param=QueryParam(mode="hybrid"))
            return result
        except Exception as e:
            logger.error(f"Error querying LightRAG: {e}")
            return f"Error querying knowledge base: {str(e)}"

    tools = [search_knowledge_base]

    # Initialize LLM
    # Strictly follow .env configuration as requested
    
    # 1. Get config from environment variables (standardized LightRAG env vars)
    base_url = os.environ.get("LLM_BINDING_HOST")
    api_key = os.environ.get("LLM_BINDING_API_KEY")
    model_name = os.environ.get("LLM_MODEL")

    # Fallback to defaults ONLY if env vars are missing (prevent crash), but priority is .env
    if not base_url:
        logger.warning("LLM_BINDING_HOST not found in .env, falling back to localhost default")
        base_url = "http://127.0.0.1:11434/v1"
        
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY", "lm-studio") # secondary fallback
        
    if not model_name:
        logger.warning("LLM_MODEL not found in .env, falling back to default")
        model_name = "qwen2.5-vl-7b-instruct"

    logger.info(f"Initializing LangGraph Agent with Model: {model_name}, BaseUrl: {base_url}")

    llm = ChatOpenAI(
        base_url=base_url,
        api_key=api_key,
        model=model_name,
        temperature=0,
    )
    
    llm_with_tools = llm.bind_tools(tools)

    # Node Definitions
    async def agent_node(state: AgentState):
        messages = state["messages"]
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    def should_continue(state: AgentState) -> Literal["tools", END]:
        messages = state["messages"]
        last_message = messages[-1]
        
        if last_message.tool_calls:
            return "tools"
        return END

    # Graph construction
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(tools))

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("tools", "agent")

    app = workflow.compile()
    return app
