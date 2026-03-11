from fastapi import FastAPI
from app.api.route import router

app = FastAPI(
    title="Vehicle Monitoring Chatbot"
)

app.include_router(router)
