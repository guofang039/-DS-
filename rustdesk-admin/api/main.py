import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from config import settings
from database import init_db
from routers import auth, devices, addressbook, audit, update

@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(os.path.dirname(settings.ADMIN_DB_PATH), exist_ok=True)
    await init_db()
    yield

app = FastAPI(
    title="小翔DS 管理后台 API",
    description="RustDesk 远程桌面管理系统 API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(devices.router)
app.include_router(addressbook.router)
app.include_router(audit.router)
app.include_router(update.router)

@app.get("/api/heartbeat")
async def heartbeat():
    return {"status": "ok"}

@app.get("/api/server-config")
async def get_server_config():
    return {
        "hbbs": f"{settings.HBBS_HOST}:{settings.HBBS_PORT}",
        "hbbr": f"{settings.HBBS_HOST}:{settings.HBBR_PORT}",
        "api_server": f"http://{settings.HBBS_HOST}:{settings.API_PORT}"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )

WEB_DIR = Path(__file__).parent.parent / "web" / "dist"
if WEB_DIR.exists():
    app.mount("/assets", StaticFiles(directory=WEB_DIR / "assets"), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = WEB_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(WEB_DIR / "index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.API_PORT)
