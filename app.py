import os
import json
import asyncio
from typing import List, Dict
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai

load_dotenv()

MODEL_ID = os.environ.get("MODEL_ID")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

app = FastAPI()

client = genai.Client(api_key=GOOGLE_API_KEY)

class ChatSession(BaseModel):
    history: List[Dict[str, str]]

@app.get("/", response_class=HTMLResponse)
async def get_index():
    with open("index.html", "r") as f:
        return f.read()

@app.post("/stream")
async def stream_chat(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "")
    
    async def event_generator():
        try:
            async for chunk in await client.aio.models.generate_content_stream(
                model=MODEL_ID,
                contents=prompt
            ):
                if chunk.text:
                    yield f"data: {json.dumps({'text': chunk.text})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/save")
async def save_session(session: ChatSession):
    try:
        with open("test.json", "w") as f:
            json.dump(session.history, f, indent=4)
        return {"status": "success", "message": "Session saved to test.json"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
