from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from .config import LLM_MODEL, EMBEDDING_MODEL, RERANKER_MODEL

llm = ChatOllama(
    model=LLM_MODEL
)

embeddings = OllamaEmbeddings(
    model=EMBEDDING_MODEL
)

hf_cross_encoder_model = HuggingFaceCrossEncoder(
    model_name=RERANKER_MODEL
)