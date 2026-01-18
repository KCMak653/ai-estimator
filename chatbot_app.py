from fastapi import FastAPI
from pydantic import BaseModel
from chatbot.chatbot import agent_app
import uuid
from typing import Optional

app = FastAPI(title="Windows Chatbot Backend")

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # Use existing thread_id or create a new one
    thread_id = request.thread_id or str(uuid.uuid4())
    
    config = {"configurable": {"thread_id": thread_id}}
    
    # Run the graph
    input_message = {"messages": [("user", request.message)]}
    result = agent_app.invoke(input_message, config=config)
    
    # Get the last message from the assistant
    assistant_msg = result["messages"][-1].content
    
    return {
        "response": assistant_msg,
        "thread_id": thread_id
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)