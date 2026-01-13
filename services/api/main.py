from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import uuid
import time
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from services.api.logic.llm import createGroqClient, generateManimCode
from services.api.logic.sanitizer import sanitizeAndValidateCode
from services.api.logic.renderer import renderCode

app = FastAPI(
    title = "Playground API", 
    description = "An API to convert text prompts into Manim animations.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/media", StaticFiles(directory="media"), name="media")

tasks = {}

@app.get("/")
def root():
    return {
        "message": "Welcome to Playground API",
        "endpoints": {
            "render": "POST /render - Submit a prompt to generate a Manim animation",
            "status": "GET /status/{task_id} - Check the status of a render task"
        }
    }

try:
    groqClient = createGroqClient()
except Exception as exc:
    print(f"CRITICAL ERROR: Failed to create Groq client on startup: {exc}")
    groqClient = None

def RunFullPipeline(taskId: str, prompt: str):
    print(f"Background task {taskId} started.")
    tasks[taskId] = {"status": "PROCESSING"}
    
    try:
        if not groqClient:
            raise ConnectionError("Groq client is not available.")

        rawCode = generateManimCode(prompt, groqClient)
        cleanCode = sanitizeAndValidateCode(rawCode)
        videoPath = renderCode(cleanCode)
        
        if not videoPath:
            raise ValueError("Rendering resulted in no video path.")

        tasks[taskId].update({"status": "SUCCESS", "result": videoPath})
        print(f"Background task {taskId} succeeded.")

    except Exception as e:
        tasks[taskId].update({"status": "FAILURE", "error": str(e)})
        print(f"Background task {taskId} failed: {e}")

class RenderRequest(BaseModel):
    prompt: str

class RenderResponse(BaseModel):
    taskID: str

class StatusResponse(BaseModel):
    status: str
    result: str | None = None
    error: str | None = None

@app.post("/render", response_model=RenderResponse)
def submitRenderJob(request: RenderRequest, background_tasks: BackgroundTasks):
    taskID = str(uuid.uuid4())
    tasks[taskID] = {"status": "PENDING"}

    background_tasks.add_task(RunFullPipeline, taskID, request.prompt)
    return RenderResponse(taskID=taskID)

@app.get("/status/{task_id}", response_model=StatusResponse)
def getTaskStatus(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return StatusResponse(**task)