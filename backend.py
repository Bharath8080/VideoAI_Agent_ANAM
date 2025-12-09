import json
import os
import time
import re
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from loguru import logger

# Import the existing agent
from scripts.agent import agent, agent_config

load_dotenv()

# -------------------------------
# Logger Configuration
# -------------------------------
WANTED = ["🎙", "👂", "💬", "🔊", "⚡"]

def filter_logs(record):
    return any(e in record["message"] for e in WANTED)

logger.add(
    lambda msg: print(msg),
    level="INFO",
    filter=filter_logs,
    format="<green>{time:HH:mm:ss}</green> | {message}",
)

# Color helper
CYAN   = "\033[96m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

# -------------------------------
# TEXT CLEANER FOR TTS
# -------------------------------
def clean_text_for_tts(text: str) -> str:
    """
    Clean markdown formatting for better TTS output.
    """
    clean_text = text
    clean_text = re.sub(r'\*+', '', clean_text)
    clean_text = re.sub(r'[#_`]', '', clean_text)
    clean_text = re.sub(r'-{2,}', ' ', clean_text)
    clean_text = re.sub(r'\|', ' ', clean_text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text

# -------------------------------
# Pydantic Models
# -------------------------------
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

# -------------------------------
# FastAPI App
# -------------------------------
app = FastAPI(
    title="Samantha Video Agent Backend",
    description="FastAPI backend for Anam AI integration using Samantha Agent.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/llm/stream")
async def llm_stream(
    payload: ChatRequest,
    session_id: str = Query(..., description="Session ID (Thread ID)"),
):
    """
    Streaming LLM endpoint for Anam.
    Invokes the local LangChain agent and streams the response token by token (simulated or real).
    """
    messages = payload.messages
    if not messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    # Extract the last user message
    user_message = next((m.content for m in reversed(messages) if m.role == "user"), None)
    if not user_message:
        raise HTTPException(status_code=400, detail="No user message found")

    async def event_generator():
        chunk_count = 0
        llm_start_time = time.time()
        first_chunk_time = None
        
        try:
            # Convert messages to LangChain format
            langchain_messages = [
                {"role": m.role, "content": m.content} 
                for m in messages
            ]
            
            logger.info(f"👂 Processing {len(langchain_messages)} messages, last: {user_message[:50]}...")
            
            # Prepare configuration with session_id
            config = agent_config.copy()
            config["configurable"]["thread_id"] = session_id

            # Streaming events with full message history
            async for event in agent.astream_events(
                {"messages": langchain_messages},
                config=config,
                version="v1",
            ):
                kind = event["event"]
                
                # We are interested in 'on_chat_model_stream' events from the final LLM response
                # But since it's an agent, it might call tools first.
                # Simplest for Anam: Stream the final answer chunks.
                
                if kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        if first_chunk_time is None:
                            first_chunk_time = time.time()
                            ttft = first_chunk_time - llm_start_time
                            logger.info(f"💬 First chunk received in {YELLOW}{ttft:.2f}s{RESET}")
                        
                        chunk_count += 1
                        # Clean markdown formatting for TTS
                        cleaned_content = clean_text_for_tts(content)
                        payload = json.dumps({"content": cleaned_content})
                        yield f"data: {payload}\n\n"
            
            # Log performance metrics
            llm_end_time = time.time()
            llm_time = llm_end_time - llm_start_time
            
            logger.info(
                f"{CYAN}⚡ Performance:{RESET} "
                f"{MAGENTA}LLM={llm_time:.2f}s{RESET} | "
                f"{RED}Chunks={chunk_count}{RESET}"
            )

        except Exception as e:
            logger.error(f"🔊 Error: {str(e)}")
            err_payload = json.dumps({"content": f"Error: {str(e)}"})
            yield f"data: {err_payload}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
