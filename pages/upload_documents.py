import os
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from config.settings import CHROMA_PATH, EMBEDDING_MODEL

st.markdown("### 📄 Upload Documents")
st.info("- **PDF, TXT, MD**: Added to Document Vector DB.")

uploaded_files = st.file_uploader(
    "Choose files", 
    type=["pdf", "txt", "md"], 
    accept_multiple_files=True
)

if uploaded_files:
    if st.button("🚀 Ingest Documents", type="primary"):
        with st.spinner("Ingesting..."):
            results = []
            for file in uploaded_files:
                try:
                    temp_file = f"./temp_{file.name}"
                    with open(temp_file, "wb") as f:
                        f.write(file.getbuffer())
                    
                    file_ext = file.name.split('.')[-1].lower()
                    
                    if file_ext == 'pdf':
                        loader = PyPDFLoader(temp_file)
                    elif file_ext in ['txt', 'md']:
                        loader = TextLoader(temp_file)
                    else:
                        continue

                    docs = loader.load()
                    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, add_start_index=True)
                    chunks = text_splitter.split_documents(docs)
                    for chunk in chunks:
                        chunk.metadata['source'] = file.name

                    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
                    Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=CHROMA_PATH)
                    results.append(f"✅ **{file.name}**: Added {len(chunks)} chunks to Document DB.")
                    
                except Exception as e:
                    results.append(f"❌ **{file.name}**: Error - {str(e)}")
                finally:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
            
            for res in results:
                st.write(res)
            if any("Added" in r for r in results):
                st.success("Ingestion complete!")
