from lightrag.lightrag import LightRAG
from lightrag.utils import EmbeddingFunc
import os
import asyncio

# Define a dummy embedding function since we only want to inspect the graph
async def dummy_embedding(texts):
    return [[0.0] * 384 for _ in texts]

async def inspect():
    rag = LightRAG(
        working_dir="./rag_storage",
        embedding_func=EmbeddingFunc(
            embedding_dim=384,
            max_token_size=8192,
            func=dummy_embedding
        )
    )

    # Dictionary to store findings
    findings = {
        "BAA00003": None,
        "CSC10001": None,
        "nodes_count": 0
    }

    try:
        # Load the graph
        graph = rag.chunk_entity_relation_graph
        findings["nodes_count"] = graph.number_of_nodes()
        
        # Search for specific course IDs
        print("--- Searching for specific nodes ---")
        for node in graph.nodes():
            if "BAA00003" in str(node) or "CSC10001" in str(node):
                print(f"Found node: {node}")
                print(f"Data: {graph.nodes[node]}")
            
            # Also check for "Môn học" generally
            if "Môn học" in str(node):
                pass 

    except Exception as e:
        print(f"Error inspecting graph: {e}")

if __name__ == "__main__":
    asyncio.run(inspect())
