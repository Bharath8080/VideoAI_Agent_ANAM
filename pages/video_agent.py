import streamlit as st
import streamlit.components.v1 as components
import asyncio
from services.anam_service import anam_service

# Initialize session state for Anam
if "anam_session_token" not in st.session_state:
    st.session_state.anam_session_token = None
if "anam_session_id" not in st.session_state:
    st.session_state.anam_session_id = "default-session"

# Create session token if needed
if st.session_state.anam_session_token is None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    session_data = loop.run_until_complete(
        anam_service.create_session_token(
            persona_name="Samantha",
            system_prompt="You are Samantha, a helpful AI assistant.",
            llm_id="CUSTOMER_CLIENT_V1"
        )
    )
    
    if not session_data or "sessionToken" not in session_data:
        st.error("Failed to create Anam session. Check your ANAM_API_KEY in .env")
        st.stop()
    
    st.session_state.anam_session_token = session_data["sessionToken"]

session_token = st.session_state.anam_session_token
session_id = st.session_state.anam_session_id

# Anam Avatar HTML
anam_html = f"""
<!DOCTYPE html>
<html>
<head>
  <style>
    body {{
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }}
    #persona-video {{
      width: 100%;
      max-width: 600px;
      border-radius: 12px;
      background: black;
      margin: 0 auto;
    }}
    #status {{
      text-align: center;
      margin-top: 10px;
      font-size: 12px;
      color: #666;
      font-weight: 500;
    }}
    .controls {{
      text-align: center;
      margin-top: 15px;
    }}
    button {{
      padding: 8px 20px;
      margin: 0 5px;
      border-radius: 6px;
      border: none;
      cursor: pointer;
      font-size: 14px;
    }}
    .start-btn {{ background: #4CAF50; color: white; }}
    .stop-btn {{ background: #f44336; color: white; }}
    .end-btn {{ background: #ff9800; color: white; }}
  </style>
</head>
<body>
  <video id="persona-video" autoplay playsinline></video>
  <div id="status">Initializing…</div>
  <div class="controls">
    <button class="start-btn" id="start-btn" onclick="startConversation()">Start Conversation</button>
    <button class="stop-btn" id="stop-btn" onclick="stopConversation()" style="display:none;">Stop Conversation</button>
    <button class="end-btn" id="end-btn" onclick="endSession()">End Session</button>
  </div>

  <script type="module">
    import {{ createClient }} from "https://esm.sh/@anam-ai/js-sdk@latest";
    import {{ AnamEvent }} from "https://esm.sh/@anam-ai/js-sdk@latest/dist/module/types";

    const sessionToken = "{session_token}";
    const sessionId = "{session_id}";
    const statusEl = document.getElementById("status");
    const startBtn = document.getElementById("start-btn");
    const stopBtn = document.getElementById("stop-btn");
    const endBtn = document.getElementById("end-btn");
    
    let anamClient = null;

    async function handleUserMessage(messageHistory) {{
      if (messageHistory.length === 0) return;
      
      const lastMessage = messageHistory[messageHistory.length - 1];
      if (lastMessage.role !== 'user') return;

      if (!anamClient) return;

      try {{
        const messages = messageHistory.map((msg) => ({{
          role: msg.role === 'user' ? 'user' : 'assistant',
          content: msg.content,
        }}));

        const talkStream = anamClient.createTalkMessageStream();
        await new Promise(resolve => setTimeout(resolve, 50));

        const response = await fetch(
          `http://localhost:8000/llm/stream?session_id=${{sessionId}}`,
          {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify({{ messages }}),
          }}
        );

        if (!response.ok) {{
          throw new Error(`Backend returned ${{response.status}}`);
        }}

        const reader = response.body?.getReader();
        if (!reader) throw new Error('Failed to get response stream reader');

        const textDecoder = new TextDecoder();
        
        while (true) {{
          const {{ done, value }} = await reader.read();
          if (done) {{
            if (talkStream.isActive()) talkStream.endMessage();
            break;
          }}

          if (value) {{
            const text = textDecoder.decode(value, {{ stream: true }});
            const lines = text.split('\\n').filter((line) => line.trim());

            for (const line of lines) {{
              if (line.startsWith('data: ')) {{
                try {{
                  const data = JSON.parse(line.slice(6));
                  if (data.content && talkStream.isActive()) {{
                    talkStream.streamMessageChunk(data.content, false);
                  }}
                }} catch (e) {{}}
              }}
            }}
          }}
        }}
      }} catch (error) {{
        console.error('Error:', error);
        if (anamClient) {{
          anamClient.talk("I encountered an error. Please ensure the backend is running on port 8000.");
        }}
      }}
    }}

    async function start() {{
      try {{
        statusEl.textContent = "Connecting…";
        anamClient = createClient(sessionToken);

        anamClient.addListener(AnamEvent.SESSION_READY, () => {{
          statusEl.textContent = "Connected";
          statusEl.style.color = "#22c55e";
          startBtn.style.display = "inline-block";
          stopBtn.style.display = "none";
        }});

        anamClient.addListener(AnamEvent.CONNECTION_CLOSED, () => {{
          statusEl.textContent = "Disconnected";
          statusEl.style.color = "#dc3545";
        }});

        anamClient.addListener(AnamEvent.MESSAGE_HISTORY_UPDATED, handleUserMessage);

        await anamClient.streamToVideoElement("persona-video");
      }} catch (error) {{
        statusEl.textContent = `Error: ${{error.message}}`;
        statusEl.style.color = "#dc3545";
      }}
    }}
    
    window.startConversation = function() {{
      if (anamClient) {{
        anamClient.talk("Hello! How can I help you today?");
        startBtn.style.display = "none";
        stopBtn.style.display = "inline-block";
        statusEl.textContent = "Listening...";
      }}
    }};
    
    window.stopConversation = function() {{
      if (anamClient) {{
        anamClient.stopStreaming();
        startBtn.style.display = "inline-block";
        stopBtn.style.display = "none";
        statusEl.textContent = "Connected";
      }}
    }};
    
    window.endSession = function() {{
      if (anamClient) {{
        anamClient.stopStreaming();
        statusEl.textContent = "Session ended.";
        statusEl.style.color = "#ff9800";
        startBtn.style.display = "none";
        stopBtn.style.display = "none";
        endBtn.style.display = "none";
      }}
    }};

    start();
  </script>
</body>
</html>
"""

components.html(anam_html, height=650, scrolling=False)
