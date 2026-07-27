from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.chains.history_aware_retriever import create_history_aware_retriever
from langchain_classic.retrievers.multi_query import MultiQueryRetriever
from core import embeddings, llm, reranker_model, CHROMA_DB_PATH
from typing import List


def get_vector_store() -> Chroma:
    """Connects to the existing Chroma database on disk."""
    return Chroma(
        embedding_function=embeddings,
        persist_directory=CHROMA_DB_PATH
    )


def build_hybrid_retriever(documents: List[Document]):
    """
    Combines Vector search, BM25, Multi-Query generation, 
    and a Cross-Encoder Reranker into a single retrieval pipeline.
    """
    # 1. Initialize Vector Retriever
    vector_store = get_vector_store()
    vector_retriever = vector_store.as_retriever(search_kwargs={"k": 25})
    
    # 2. Initialize BM25 Retriever
    bm25_retriever = BM25Retriever.from_documents(documents)
    bm25_retriever.k = 25
    
    # 3. Combine into Ensemble (Hybrid)
    ensemble_retriever = EnsembleRetriever(
        retrievers=[vector_retriever, bm25_retriever],
        weights=[0.5, 0.5]
    )
    
    # 4. Wrap with Multi-Query Generation
    mq_retriever = MultiQueryRetriever.from_llm(
        retriever=ensemble_retriever,
        llm=llm
    )
    
    # 5. Apply Cross-Encoder Reranking
    base_compressor = CrossEncoderReranker(
        model=reranker_model,
        top_n=10
    )
    final_hybrid_rerank_retriever = ContextualCompressionRetriever(
        base_compressor=base_compressor,
        base_retriever=mq_retriever
    )
    
    return final_hybrid_rerank_retriever


def build_history_aware_retriever(documents: List[Document]):
    """
    Makes the fully assembled reranked hybrid retriever aware of chat history.
    """
    base_retriever = build_hybrid_retriever(documents)
    
    context_rephrasing_prompt = ChatPromptTemplate.from_messages([
        ("system", "Given a chat history and the latest user question "
                   "which might reference context in the chat history, "
                   "formulate a standalone question which can be understood "
                   "without the chat history. Do NOT answer the question, "
                   "just reformulate it if needed and otherwise return it as is."),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}")
    ])
    
    history_aware_retriever = create_history_aware_retriever(
        llm=llm,
        retriever=base_retriever,
        prompt=context_rephrasing_prompt
    )
    
    return history_aware_retriever