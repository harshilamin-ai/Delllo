logging.basicConfig(level=logging.DEBUG)
import logging
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from background_tasks import run_networking_event
from utils_llm import query_llm

router = APIRouter()

class EventRequest(BaseModel):
    event_id: str

class ChatRequest(BaseModel):
    prompt: str

@router.post("/trigger_networking_event")
async def trigger_event(request: EventRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_networking_event, request.event_id)
    return {"status": "triggered", "event_id": request.event_id}

@router.post("/chat")
def chat(request: ChatRequest):
    response = query_llm(request.prompt)
    return {"response": response}
