# Fix for BM25Retriever import error

# 1. First, install the required package:
# pip install llama-index-retrievers-bm25

# 2. Update the import in your retrieve_nodes.py file:
# Change this line:
# from llama_index.core.retrievers.bm25 import BM25Retriever

# To this:
from llama_index.retrievers.bm25 import BM25Retriever

# The rest of your code remains the same
# BM25Retriever is now in a separate package but the API is the same

# Example of the corrected imports section:
import chromadb
import os
import torch
from typing import List, Any
from pydantic import SkipValidation
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from utils.common_utils import load_articles, build_doubao_embedding

# Updated imports
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import Settings, StorageContext, VectorStoreIndex
from llama_index.core.retrievers import BaseRetriever, VectorIndexRetriever
from llama_index.core.schema import NodeWithScore
from llama_index.core import QueryBundle
from llama_index.retrievers.bm25 import BM25Retriever  # <-- Updated import path
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.query_engine import RetrieverQueryEngine