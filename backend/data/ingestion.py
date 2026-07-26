import pymupdf4llm
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language, MarkdownHeaderTextSplitter
from langchain_chroma import Chroma
from core import embeddings, CHROMA_DB_PATH
from typing import List



def load_pdf_as_markdown(file_path: str) -> List[Document]:
    """
    Converts a single PDF to Markdown and structures it into LangChain Documents,
    preserving the page number metadata. 
    """
    md_text = pymupdf4llm.to_markdown(file_path, page_chunks=True)
    
    documents = []
    for page in md_text:
        doc = Document(
            metadata={"page": page["metadata"]["page_number"]},
            page_content=page["text"]
        )
        documents.append(doc)
        
    return documents


def split_by_markdown_headers(documents: List[Document]) -> List[Document]:
    """
    Splits the markdown documents by headers while retaining the original page metadata.
    """
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
        ("####", "Header 4"),
    ]
    
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False
    )
    
    header_docs = []
    for doc in documents:
        splits = markdown_splitter.split_text(doc.page_content)
        for s in splits:
            # Reattach the page number metadata to each split
            s.metadata.update(doc.metadata)
            header_docs.append(s)
            
    return header_docs



def split_into_final_chunks(header_docs: List[Document]) -> List[Document]:
    """
    Applies a secondary split to ensure chunks fit within token limits using Markdown rules.
    (Ref: image_2bc731.png)
    """
    text_splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.MARKDOWN,
        chunk_size=1600,
        chunk_overlap=300
    )
    return text_splitter.split_documents(header_docs)



def process_and_ingest_pdf(file_path: str) -> Chroma:
    """
    The main orchestrator: takes a single PDF path from the frontend, runs the 
    markdown splitting pipeline, and saves the vectors to ChromaDB.
    """
    print(f"Loading and converting {file_path} to Markdown...")
    docs = load_pdf_as_markdown(file_path)
    
    print("Splitting documents by Markdown headers...")
    header_docs = split_by_markdown_headers(docs)
    
    print("Applying final recursive character chunking...")
    final_chunks = split_into_final_chunks(header_docs)
    
    print(f"Embedding and persisting {len(final_chunks)} chunks to Chroma...")
    vector_store = Chroma.from_documents(
        documents=final_chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DB_PATH
    )
    
    print("Ingestion complete!")
    return vector_store