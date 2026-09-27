from fastapi import FastAPI
from src.link.routes import link_router

app = FastAPI()

app.include_router(link_router, prefix="", tags=["Links"])

@app.get("/")
def home():
    return {"message": "server running live"}
