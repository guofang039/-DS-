from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import platform

router = APIRouter(prefix="/api/update", tags=["更新管理"])

GITEE_API = "https://gitee.com/api/v5/repos/xueguofang/xiaoxiangyun-ds-remote"
CURRENT_VERSION = "1.4.6"

class VersionInfo(BaseModel):
    version: str
    release_url: str
    download_url: str | None = None
    changelog: str | None = None
    force_update: bool = False

class UpdateCheckResponse(BaseModel):
    has_update: bool
    current_version: str
    latest_version: str
    download_url: str | None = None
    changelog: str | None = None

@router.get("/version")
async def get_current_version():
    return {
        "version": CURRENT_VERSION,
        "platform": platform.system().lower(),
        "arch": platform.machine()
    }

@router.get("/check")
async def check_update():
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{GITEE_API}/releases/latest")
            if resp.status_code != 200:
                return UpdateCheckResponse(
                    has_update=False,
                    current_version=CURRENT_VERSION,
                    latest_version=CURRENT_VERSION
                )
            
            release = resp.json()
            latest_version = release.get("tag_name", "").lstrip("v")
            changelog = release.get("body", "")
            
            has_update = latest_version != CURRENT_VERSION
            
            download_url = None
            if has_update:
                assets = release.get("assets", [])
                system = platform.system().lower()
                machine = platform.machine()
                
                for asset in assets:
                    name = asset.get("name", "").lower()
                    if system == "linux" and "amd64.deb" in name:
                        download_url = asset.get("browser_download_url")
                        break
                    elif system == "windows" and "windows" in name and "x64" in name:
                        download_url = asset.get("browser_download_url")
                        break
            
            return UpdateCheckResponse(
                has_update=has_update,
                current_version=CURRENT_VERSION,
                latest_version=latest_version,
                download_url=download_url,
                changelog=changelog
            )
    except Exception as e:
        return UpdateCheckResponse(
            has_update=False,
            current_version=CURRENT_VERSION,
            latest_version=CURRENT_VERSION
        )

@router.get("/releases")
async def list_releases():
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{GITEE_API}/releases")
            if resp.status_code != 200:
                return []
            
            releases = resp.json()
            return [
                {
                    "version": r.get("tag_name", "").lstrip("v"),
                    "name": r.get("name", ""),
                    "changelog": r.get("body", ""),
                    "created_at": r.get("created_at", ""),
                    "assets": [
                        {
                            "name": a.get("name", ""),
                            "size": a.get("size", 0),
                            "download_url": a.get("browser_download_url", "")
                        }
                        for a in r.get("assets", [])
                    ]
                }
                for r in releases[:10]
            ]
    except:
        return []

@router.get("/download/{version}")
async def get_download_url(version: str):
    system = platform.system().lower()
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            tag = f"v{version}" if not version.startswith("v") else version
            resp = await client.get(f"{GITEE_API}/releases/tags/{tag}")
            if resp.status_code != 200:
                raise HTTPException(status_code=404, detail="版本不存在")
            
            release = resp.json()
            assets = release.get("assets", [])
            
            for asset in assets:
                name = asset.get("name", "").lower()
                if system == "linux" and "amd64.deb" in name:
                    return {"download_url": asset.get("browser_download_url")}
                elif system == "windows" and "windows" in name and "x64" in name:
                    return {"download_url": asset.get("browser_download_url")}
            
            return {"download_url": None, "message": "未找到对应平台的安装包"}
    except httpx.HTTPError:
        raise HTTPException(status_code=500, detail="获取下载链接失败")
