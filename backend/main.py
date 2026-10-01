from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from router import ai, analysis, export, feedback, public, questionnaire, register, response

app = FastAPI()

upload_dir = Path(__file__).resolve().parent / "uploads"
upload_dir.mkdir(parents=True, exist_ok=True)
app.mount(
    "/uploads",
    StaticFiles(directory=str(upload_dir)),
    name="uploads",
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(register.router)
app.include_router(questionnaire.router)
app.include_router(public.router)
app.include_router(response.router)
app.include_router(analysis.router)
app.include_router(export.router)
app.include_router(ai.router)
app.include_router(feedback.router)
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000)
