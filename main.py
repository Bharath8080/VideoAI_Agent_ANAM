import os
import base64
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Samantha",
    page_icon="🌀",
    layout="centered"
)

# Title and description
st.markdown(
    """
    <h1 style='text-align:center'>
        <span style='color:#00b3ff;'>Ur's AI Assistant Samantha</span>
    </h1>
    """,
    unsafe_allow_html=True
)

# Define pages for navigation
pages = {
    "Main Menu": [
        st.Page("pages/chat.py", title="💬 Chat", default=True),
        st.Page("pages/upload_documents.py", title="📚 Upload Documents"),
        st.Page("pages/video_agent.py", title="🎥 Video Agent"),
    ],
}

# Create navigation with top position
pg = st.navigation(pages, position="top")

# Sidebar controls
with st.sidebar:
    # Display image at the top of sidebar
    with open("assets/anam.png", "rb") as img_file:
        img_data = base64.b64encode(img_file.read()).decode()
    
    st.markdown(
        f"""
        <div style='text-align:center; margin-bottom: 20px;'>
            <img src="data:image/png;base64,{img_data}" width="150">
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.header("ℹ️ About Samantha")
    st.markdown("""
    Your AI assistant with access to:
    - 🔍 **Web Search**
    - 📄 **Document Search** (PDF/Text)
    - 📈 **Stocks & Weather**
    """)
    st.divider()
    
    # Video Agent Controls (only show when Video Agent is selected)
    if pg.title == "🎥 Video Agent":
        st.header("🎥 Video Agent Settings")
        
        # Initialize session state for Anam
        if "anam_session_token" not in st.session_state:
            st.session_state.anam_session_token = None
        if "anam_session_id" not in st.session_state:
            st.session_state.anam_session_id = "default-session"
        
        session_name = st.text_input("Session Name", value=st.session_state.anam_session_id, key="anam_session_name")
        
        if st.button("🔄 New Session", type="secondary", use_container_width=True):
            st.session_state.anam_session_token = None
            st.session_state.anam_session_id = session_name
            st.success("Session reset!")
            st.rerun()
        
        st.divider()
    
    # Clear Chat History (show for Chat page)
    if pg.title == "💬 Chat":
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

# Run the selected page
pg.run()
