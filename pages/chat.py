import streamlit as st
from scripts.agent import agent, agent_config

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "processing" not in st.session_state:
    st.session_state.processing = False

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input at the bottom
if prompt := st.chat_input("Ask me anything...", key="chat_input"):
    if not st.session_state.processing:
        st.session_state.processing = True
        
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        try:
            # Convert session state messages to LangChain format
            langchain_messages = [
                {"role": msg["role"], "content": msg["content"]} 
                for msg in st.session_state.messages
            ]
            
            # Invoke agent with full conversation history
            agent_reply = agent.invoke(
                {"messages": langchain_messages},
                config=agent_config,
            )
            
            # Extract only the final assistant response content
            final_message = agent_reply["messages"][-1]
            if hasattr(final_message, 'content'):
                response = final_message.content
            else:
                response = str(final_message)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            st.session_state.messages.append({"role": "assistant", "content": f"❌ Error: {str(e)}"})
        
        st.session_state.processing = False
        st.rerun()
