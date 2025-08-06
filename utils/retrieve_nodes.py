# 混合检索
import chromadb
import os
import torch
from typing import List, Any
from pydantic import SkipValidation
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from utils.common_utils import load_articles, build_doubao_embedding

# 更新后的导入路径
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import Settings, StorageContext, VectorStoreIndex
from llama_index.core.retrievers import BaseRetriever, VectorIndexRetriever
from llama_index.core.schema import NodeWithScore
from llama_index.core import QueryBundle
# 修复BM25Retriever的导入 - 在新版本中位置可能不同
try:
    from llama_index.core.retrievers.bm25 import BM25Retriever
except ImportError:
    try:
        from llama_index.retrievers.bm25 import BM25Retriever
    except ImportError:
        try:
            # 如果上述导入都失败，尝试从llama_index.legacy导入
            from llama_index.legacy.retrievers.bm25_retriever import BM25Retriever
        except ImportError:
            # 最后的备选方案，从llama_index.retrievers导入
            from llama_index.retrievers import BM25Retriever

from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.query_engine import RetrieverQueryEngine

# 4. 创建自定义的检索器
class CustomRetriever(BaseRetriever):
    """custom retriever that performs both vector and keyword table retrieval"""
    def __init__(self,
                 vector_retriever: VectorIndexRetriever,
                 bm25_retriever: BM25Retriever,
                 mode: str = "OR",
    ) -> None:
        self._vector_retriever = vector_retriever
        self._bm25_retriever = bm25_retriever
        if mode not in ["AND", "OR"]:
            raise ValueError("mode must be either AND or OR")
        self._mode = mode
        super().__init__()
    
    def _retrieve(self, query_bundle: QueryBundle|str) -> List[NodeWithScore]:
        """retrieve nodes given query"""
        print(f"Retrieving nodes for query: {query_bundle.query_str}")
        vector_nodes = self._vector_retriever.retrieve(query_bundle)
        bm25_nodes = self._bm25_retriever.retrieve(query_bundle)
        
        vector_ids = {node.node.node_id for node in vector_nodes}
        bm25_ids = {node.node.node_id for node in bm25_nodes}
        
        combined_dict = {node.node.node_id: node for node in vector_nodes}
        combined_dict.update({node.node.node_id: node for node in bm25_nodes})
        
        if self._mode == "AND":
            retrieve_ids = vector_ids.intersection(bm25_ids)
        if self._mode == "OR":
            retrieve_ids = vector_ids.union(bm25_ids)
        
        retrieve_nodes = [combined_dict[node_id] for node_id in retrieve_ids]
        print(f"{len(retrieve_nodes)} nodes retrieved")
        return retrieve_nodes

class DouBaoEmbedding(BaseEmbedding):
    emb_model: SkipValidation[Any] = None
    def __init__(self, model_name: str = "doubao-embedding-text-240715", emb_model: Any = None, **kwargs):
        super().__init__(**kwargs)
        self.model_name = model_name
        self.emb_model = emb_model
    
    def _get_embedding(self, texts: list[str] | str) -> List[float] | List[List[float]]:
        single_text = isinstance(texts, str)
        if single_text:
            texts = [texts]
        response = self.emb_model(
            model=self.model_name,
            input=texts
        )
        embeddings = [
            embedding_data.embedding for embedding_data in response.data
        ]
        if single_text:
            return embeddings[0]
        return embeddings

    async def _aget_embedding(self, text: str) -> List[float]:
        return self._get_embedding(text)

    def _get_text_embedding(self, text: list[str]) -> List[List[float]]:
        return self._get_embedding(text)

    def _get_query_embedding(self, query: str) -> List[float]:
        return self._get_embedding(query)
    
    async def _aget_text_embedding(self, text: list[str]) -> List[List[float]]:
        return self._get_text_embedding(text)
    
    async def _aget_query_embedding(self, query: str) -> List[float]:
        return self._get_query_embedding(query)

def get_doubao_embedding(model="doubao-embedding-text-240715"):
    emb_model = build_doubao_embedding()
    
    embedding_model = DouBaoEmbedding(
        model=model,
        emb_model=emb_model,
        api_key=os.environ.get("COMPLETION_OPENAI_API_KEY"),
        api_base=os.environ.get("COMPLETION_OPENAI_BASE_URL"),
    )
    return embedding_model

def get_retriever(
    docstore_path,
    chroma_db,
    storage_dir,
    similarity_top_k=10
):
    docstore = SimpleDocumentStore.from_persist_path(docstore_path)
    db = chromadb.PersistentClient(path=chroma_db)
    chroma_collection = db.get_or_create_collection(name="sc_collection")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(
        persist_dir=storage_dir,
        vector_store=vector_store, 
        docstore=docstore
    )

    doubao_embedding = get_doubao_embedding()
    vector_index = VectorStoreIndex.from_vector_store(
        vector_store,
        storage_context=storage_context,
        embed_model=doubao_embedding,
        show_progress=True,
    )
    vector_retriever = vector_index.as_retriever(
        similarity_top_k=similarity_top_k, 
        verbose=True
    )
    bm25_retriever = BM25Retriever.from_defaults(
        docstore=docstore,
        similarity_top_k=similarity_top_k,
    )
    
    custom_retriever = CustomRetriever(
        vector_retriever, 
        bm25_retriever, 
    )
    return custom_retriever

# 重排 - 模型配置
model_name = "/mnt/storage/models/bge-reranker-v2-m3"

# 全局变量，延迟加载
tokenizer = None
model = None
device = None

def load_reranker_model():
    """延迟加载重排序模型"""
    global tokenizer, model, device
    if model is None:
        try:
            # 检查本地路径是否存在
            import os
            if os.path.exists(model_name):
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModelForSequenceClassification.from_pretrained(model_name)
            else:
                # 如果本地路径不存在，使用默认的 HuggingFace 模型
                print(f"Local model path {model_name} not found, using BAAI/bge-reranker-v2-m3")
                tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-reranker-v2-m3")
                model = AutoModelForSequenceClassification.from_pretrained("BAAI/bge-reranker-v2-m3")
            
            # 检查是否有可用的GPU，如果有则将模型移动到GPU
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            print(f"device: {device}")
            model = model.to(device)
            print("Reranker model loaded successfully")
        except Exception as e:
            print(f"Warning: Could not load reranker model: {e}")
            # 创建占位符以避免后续错误
            tokenizer = None
            model = None
            device = torch.device("cpu")

def rerank_chunks(query, chunks):
    """
    对 chunks 进行重新排序
    """
    # 确保模型已加载
    load_reranker_model()
    
    # 如果模型加载失败，返回原始chunks
    if model is None or tokenizer is None:
        print("Warning: Reranker model not available, returning original chunks")
        return chunks
    
    # 准备模型输入
    features = tokenizer(
        [query]*len(chunks),
        [chunk["chunk"] for chunk in chunks],
        padding=True,
        truncation=True,
        return_tensors="pt",
    )
    # 将特征张量移动到与模型相同的设备
    features = {k: v.to(device) for k, v in features.items()}
    # 计算分数
    with torch.no_grad():
        scores = model(**features).logits.squeeze()
    # 将分数添加到每个 chunk 中
    for i, chunk in enumerate(chunks):
        chunk["score"] = float(scores[i].cpu())  # 确保将分数移回CPU
    # 降序排序
    sorted_chunks = sorted(chunks, key=lambda x: x["score"], reverse=True)
    return sorted_chunks

def get_query_engine():
    # 提供默认值
    docstore_path = os.getenv("docstore_path", "/default/docstore")
    chroma_db = os.getenv("chroma_db", "/default/chroma")
    storage_dir = os.getenv("storage_dir", "/default/storage")
    similarity_top_k = int(os.getenv("similarity_top_k", 10))
    
    retriever = get_retriever(
        docstore_path=docstore_path, 
        chroma_db=chroma_db, 
        storage_dir=storage_dir, 
        similarity_top_k=similarity_top_k
    )
    Settings.llm = None
    query_engine = RetrieverQueryEngine.from_args(
        llm=None,
        response_mode="no_text",
        retriever=retriever, 
        node_postprocessors=[]
    )
    return query_engine

def get_reranked_nodes(query, query_engine):
    response = query_engine.query(query)
    nodes = response.source_nodes
    
    # 将节点转换为适合 rerank_chunks 的格式
    chunks = [{
        "chunk": node.node.text,
        "score": node.score,
        "metadata": node.node.metadata
    } for node in nodes]
    
    # 使用自定义重排函数
    reranked_chunks = rerank_chunks(query, chunks)
    
    return reranked_chunks