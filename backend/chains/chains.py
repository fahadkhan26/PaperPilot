from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from core import llm
from retrievers import build_history_aware_retriever


def formatter(docs):
    """Formats retrieved documents into a single string with separators."""
    return "\n---\n new document \n---\n".join(doc.page_content for doc in docs)


def get_input(x):
    """Extracts the user input from the chain's dictionary payload."""
    return x["input"]


def get_history(x):
    """Extracts the chat history from the chain's dictionary payload."""
    return x["chat_history"]


parser = StrOutputParser()

# The main Strict RAG QA Prompt
qa_prompt = ChatPromptTemplate.from_messages([
    ("system", 
     "You are a strict RAG assistant. You must NEVER use outside knowledge. "
     "If the context lacks the answer, you must output EXACTLY: "
     "'The given document does not contain context to this query.'"),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", 
     "<context>\n{context}\n</context>\n\n"
     "Question: {input}\n\n"
     "STRICT INSTRUCTIONS:\n"
     "1. Answer ONLY using the facts in <context> above.\n"
     "2. If the context is empty or does not explicitly answer the question, reply EXACTLY with:\n"
     "   'The given document does not contain context to this query.'\n"
     "3. Do NOT use outside knowledge or make assumptions.\n"
     "4. Do NOT explain your reasoning. Provide the final answer immediately and concisely.")
])


ai_response_summary_prompt = ChatPromptTemplate.from_template(
    "Condense the following text into a brief, single-sentence summary of the core facts. \n"
    "CRITICAL RULES:\n"
    "1. Do NOT add outside knowledge.\n"
    "2. Do NOT add intro or outro.\n"
    "3. If the text is a short list or under 2 sentences, return it exactly as is.\n\n"
    "Text to summarize:\n{response}"
)


def build_summary_chain():
    """Builds the chain responsible for summarizing long AI responses."""
    return ai_response_summary_prompt | llm | parser


def build_rag_chain(documents):
    """
    Builds the main conversational RAG chain.
    Requires the in-memory documents to initialize the underlying BM25 retriever.
    """
    history_aware_retriever = build_history_aware_retriever(documents)
    
    chain = {
        "context": history_aware_retriever | formatter,
        "chat_history": get_history,
        "input": get_input
    } | qa_prompt | llm | parser
    
    return chain