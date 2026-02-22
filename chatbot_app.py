from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from chatbot.chatbot import agent_app
import uuid
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
import os


def get_real_ip(request: Request):
    # Railway passes the real user IP in this header
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()  # Get the first IP in the list
    return request.client.host


limiter = Limiter(key_func=get_real_ip)
app = FastAPI(title="Windows Chatbot Backend")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    # allow_origins=["https://direct-windows-quote.myshopify.com", "https://window-chatbot-production.up.railway.app"], 
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_AUTH_KEY = os.getenv("CHAT_CUSTOM_HEADER_KEY")

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None

@app.post("/chat")
@limiter.limit("5/minute; 100/day")
async def chat_endpoint(request: Request, chat_request: ChatRequest):

    auth = request.headers.get("Authorization")
    client_key = auth.split(maxsplit=1)[1] if auth and auth.startswith("Bearer ") else None
    if client_key != API_AUTH_KEY:
        return PlainTextResponse("Invalid API key", status_code=403)  

    thread_id = chat_request.thread_id or str(uuid.uuid4())
    
    config = {"configurable": {"thread_id": thread_id}}
    
    # Run the graph
    input_message = {"messages": [("user", chat_request.message)]}
    result = agent_app.invoke(input_message, config=config)
    
    # Get the last message from the assistant
    assistant_msg = result["messages"][-1].content

    return {
        "response": assistant_msg,
        "thread_id": thread_id,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)