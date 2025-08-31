import argparse
import boto3
import os
from dotenv import load_dotenv
from typing import Iterable

from langchain_aws import BedrockEmbeddings
from langchain_aws import BedrockLLM as LLM
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores.faiss import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough


load_dotenv()


def require_env(var_name: str) -> str:
    """Return the value of an env var or raise with a clear message."""
    value = os.getenv(var_name)
    if not value:
        raise EnvironmentError(
            f"Missing required environment variable: {var_name}.\n"
            "Set it in your shell or a .env file."
        )
    return value


def build_bedrock() -> tuple[LLM, BedrockEmbeddings]:
    """Initialize Bedrock runtime client, LLM and Embeddings."""
    region = require_env("AWS_REGION")
    model_id = require_env("MODEL_ID")
    embed_model_id = require_env("EMBED_MODEL_ID")

    client = boto3.client(service_name="bedrock-runtime", region_name=region)
    llm = LLM(model_id=model_id, client=client)
    embeddings = BedrockEmbeddings(model_id=embed_model_id, client=client)
    return llm, embeddings


def load_ingestion() -> list[Document]:
    """Load and ingest the PDF file."""
    loader = PyPDFLoader("assets/books.pdf")
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(separators=[". \n"], chunk_size=200)
    docs = splitter.split_documents(docs)
    return docs


def build_vector_store(embeddings: BedrockEmbeddings) -> FAISS:
    """Create a FAISS vector store from the demo corpus."""
    docs = load_ingestion()
    return FAISS.from_documents(docs, embedding=embeddings)


def format_docs(docs: Iterable[Document]) -> str:
    """Join retrieved documents into a context string."""
    return "\n\n".join(doc.page_content for doc in docs)


def build_chain(llm: LLM, vectorstore: FAISS):
    """Wire a retriever -> prompt -> model -> parser LCEL chain."""
    retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a concise RAG assistant. Use the provided context to answer "
                "the question. If the answer is not in the context, say you don't know.",
            ),
            ("human", "Context:\n{context}\n\nQuestion: {question}"),
        ]
    )

    chain = (
        {
            "context": retriever | RunnableLambda(format_docs),
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain, retriever


def run(question: str) -> None:
    """Execute the RAG pipeline for a given question and print results."""
    llm, embeddings = build_bedrock()
    vectorstore = build_vector_store(embeddings)
    chain, retriever = build_chain(llm, vectorstore)

    answer = chain.invoke(question)
    retrieved_docs = retriever.invoke(question)

    print("Answer:\n" + answer)

    if retrieved_docs:
        print("\nSources:")
        for idx, doc in enumerate(retrieved_docs, start=1):
            source = doc.metadata.get("source", "unknown")
            snippet = doc.page_content[:100].rstrip()
            print(f'  {idx}. {source} — "{snippet}..."')

    try:
        matches = vectorstore.similarity_search_with_score(question, k=2)
        print("\nTop matches (vector similarity scores):")
        for idx, (doc, score) in enumerate(matches, start=1):
            src = doc.metadata.get("source", "unknown")
            print(f"  {idx}. score={score:.4f} source={src}")
    except Exception:
        # Not all vectorstores expose scores in the same way; ignore if unsupported.
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a simple Bedrock RAG example")
    parser.add_argument(
        "--question",
        default="What themes does Gone with the Wind explore?",
        help="User question to answer using RAG",
    )
    args = parser.parse_args()
    run(args.question)


if __name__ == "__main__":
    main()
