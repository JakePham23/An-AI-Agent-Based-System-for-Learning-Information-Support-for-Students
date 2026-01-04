import networkx as nx
import os

# Use absolute path to be safe, extracting from current context or using relative if expected to be run from src
# The previous file used an absolute path, so I'll try to stick to relative if possible for portability 
# but will check the pwd. user is in .../LightRAG/src
file_path = "rag_storage/graph_chunk_entity_relation.graphml"
output_file = "graph_data.txt"

if os.path.exists(file_path):
    print(f"Reading graph from {file_path}...")
    try:
        graph = nx.read_graphml(file_path)
        
        print(f"Graph loaded. Nodes: {graph.number_of_nodes()}, Edges: {graph.number_of_edges()}")
        print(f"Writing to {output_file}...")
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"Graph Data Export\n")
            f.write(f"=================\n")
            f.write(f"Source File: {file_path}\n")
            f.write(f"Total Nodes: {graph.number_of_nodes()}\n")
            f.write(f"Total Edges: {graph.number_of_edges()}\n\n")
            
            # Write Nodes
            f.write(f"--- NODES ---\n")
            for node, data in graph.nodes(data=True):
                f.write(f"ID: {node}\n")
                if data:
                    for key, value in data.items():
                        # Clean up newlines in values for better readability
                        val_str = str(value).replace('\n', ' ')
                        f.write(f"  - {key}: {val_str}\n")
                f.write("\n")
            
            f.write("\n" + "=" * 20 + "\n\n")
            
            # Write Edges
            f.write(f"--- EDGES ---\n")
            for source, target, data in graph.edges(data=True):
                f.write(f"Relation: {source} -> {target}\n")
                if data:
                    for key, value in data.items():
                        val_str = str(value).replace('\n', ' ')
                        f.write(f"  - {key}: {val_str}\n")
                f.write("\n")
                
        print(f"Done! Check {output_file}")
            
    except Exception as e:
        print(f"Error processing graph: {e}")
else:
    print(f"File not found: {file_path}")
    # Try absolute path just in case
    cwd = os.getcwd()
    print(f"Current working directory: {cwd}")
