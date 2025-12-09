import os
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()

# Configuration
CHROMA_PATH = "chroma_db"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # 384 dimensions

def save_to_chroma(chunks):
    """
    Save document chunks to ChromaDB vector database.
    """
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    
    # Add documents to ChromaDB
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH
    )
    
    return len(chunks)

def process_document(uploaded_file):
    """
    Process uploaded document based on file type.
    """
    temp_file = f"./temp_{uploaded_file.name}"
    with open(temp_file, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    try:
        file_ext = uploaded_file.name.split('.')[-1].lower()
        
        # Unstructured Data (PDF, TXT, MD) -> ChromaDB
        if file_ext == 'pdf':
            loader = PyPDFLoader(temp_file)
        elif file_ext in ['txt', 'md']:
            loader = TextLoader(temp_file)
        else:
            return "❌ Unsupported file type. Only PDF, TXT, and MD from main app supported."
            
        docs = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            add_start_index=True,
        )
        chunks = text_splitter.split_documents(docs)
        
        # Add metadata about source
        for chunk in chunks:
            chunk.metadata['source'] = uploaded_file.name
            
        count = save_to_chroma(chunks)
        return f"Added {count} chunks to Document DB."
            
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

def main():
    st.set_page_config(page_title="RAG Ingestion Tool", page_icon="📚")
    st.title("📚 Knowledge Base Ingestion")
    st.write("Upload PDF/TXT/MD documents to add them to the persistent knowledge base.")
    
    uploaded_files = st.file_uploader(
        "Upload Files", 
        type=["pdf", "txt", "md"], 
        accept_multiple_files=True
    )

    if uploaded_files:
        if st.button("Ingest Documents"):
            with st.spinner("Processing documents..."):
                results = []
                for file in uploaded_files:
                    st.write(f"Processing {file.name}...")
                    result = process_document(file)
                    results.append(f"**{file.name}**: {result}")
                    st.success(f"✅ {file.name}: Done")
                
                st.write("---")
                st.subheader("Summary")
                for res in results:
                    st.write(res)
                    
if __name__ == "__main__":
    main()
