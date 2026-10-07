from fastapi import FastAPI
from src.link.routes import link_router
from src.errors import register_all_errors

app = FastAPI()

register_all_errors(app)

app.include_router(link_router, prefix="", tags=["Links"])

@app.get("/")
def home():
    return {"message": "server running live"}
