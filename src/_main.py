from fastapi import FastAPI
from src.session.ws import router as ws_router
from .api import router as api_router
from .prog import init_program
from .config import settings

app = FastAPI()
app.include_router(ws_router)
app.include_router(api_router)
init_program()

def main():
    import uvicorn
    
    uvicorn.run(
        app,
        ws="websockets",
        host=settings.host,
        port=settings.port,
    )