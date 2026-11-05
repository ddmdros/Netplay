import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from .api.chat_routes import router as chat_router  # noqa: E402  (depois do .env)

app = FastAPI(title="NetPlay API", version="1.1.0")

# Em produção, CORS_ORIGINS deve listar só o domínio do front-end.
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")


@app.get("/")
def read_root():
    return {"message": "NetPlay API is up and running!"}
