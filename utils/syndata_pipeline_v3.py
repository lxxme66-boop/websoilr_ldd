#!/usr/bin/env python3

from utils.topic_concepts import trans_chunk4
from utils.retrieve_nodes import get_query_engine, get_reranked_nodes

def main():
    """
    Main pipeline function
    """
    print("Starting syndata pipeline v3...")
    
    # Initialize query engine
    try:
        query_engine = get_query_engine()
        print("Query engine initialized successfully")
    except Exception as e:
        print(f"Error initializing query engine: {e}")
        return
    
    # Example usage
    test_query = "sample query"
    try:
        reranked_nodes = get_reranked_nodes(test_query, query_engine)
        print(f"Retrieved {len(reranked_nodes)} reranked nodes")
    except Exception as e:
        print(f"Error retrieving nodes: {e}")
    
    print("Pipeline completed")

if __name__ == "__main__":
    main()