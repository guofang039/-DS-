import os
import subprocess
import httpx
import platform
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/update", tags=["更新管理"])

GITEE_API = "https://gitee.com/api/v5/repos/xueguofang/xiaoxiangyun-ds-remote"
GITEE_TOKEN = "b6936ae928ac80cd75bcca1007cd406a"

def find_git_repo(start: Path) -> str:
    for d in [start, start.parent]:
        try:
            r = subprocess.run(
                ["git", "remote", "-v"],
                capture_output=True, text=True, cwd=d, timeout=5
            )
            if r.stdout.strip():
                return str(d)
        except:
            pass
    if start.parent:
        for child in start.parent.iterdir():
            if child == start:
                continue
            try:
                r = subprocess.run(
                    ["git", "remote", "-v"],
                    capture_output=True, text=True, cwd=child, timeout=5
                )
                if r.stdout.strip():
                    return str(child)
            except:
                pass
    return os.getenv("SERVER_CODE_DIR", str(start))

SERVER_CODE_DIR = find_git_repo(Path(__file__).parent.parent.parent)

class ServerUpdateCheckResponse(BaseModel):
    has_update: bool
    current_commit: str
    latest_commit: str
    current_branch: str
    behind_count: int
    commit_message: str = ""

class ServerUpdateApplyResponse(BaseModel):
    success: bool
    message: str
    output: str

class ClientRelease(BaseModel):
    version: str
    name: str
    changelog: str
    created_at: str
    assets: list

class ClientCheckResponse(BaseModel):
    has_update: bool
    current_version: str
    latest_version: str
    download_url: str | None = None
    changelog: str | None = None


@router.get("/server/status")
async def server_update_status():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd=SERVER_CODE_DIR, timeout=10
        )
        current_commit = result.stdout.strip()

        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, cwd=SERVER_CODE_DIR, timeout=10
        )
        current_branch = result.stdout.strip()

        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, cwd=SERVER_CODE_DIR, timeout=10
        )
        remote_url = result.stdout.strip()

        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD..origin/master"],
            capture_output=True, text=True, cwd=SERVER_CODE_DIR, timeout=10
        )
        behind = result.stdout.strip()

        return {
            "current_commit": current_commit,
            "current_branch": current_branch,
            "remote_url": remote_url,
            "behind_count": int(behind) if behind else 0
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/server/check")
async def server_check_update():
    try:
        subprocess.run(
            ["git", "fetch", "origin"],
            capture_output=True, text=True, cwd=SERVER_CODE_DIR, timeout=30
        )

        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd=SERVER_CODE_DIR, timeout=10
        )
        current_commit = result.stdout.strip()

        result = subprocess.run(
            ["git", "rev-parse", "origin/master"],
            capture_output=True, text=True, cwd=SERVER_CODE_DIR, timeout=10
        )
        latest_commit = result.stdout.strip()

        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, cwd=SERVER_CODE_DIR, timeout=10
        )
        current_branch = result.stdout.strip()

        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD..origin/master"],
            capture_output=True, text=True, cwd=SERVER_CODE_DIR, timeout=10
        )
        behind_count = int(result.stdout.strip()) if result.stdout.strip() else 0

        commit_msg = ""
        if behind_count > 0:
            result = subprocess.run(
                ["git", "log", "--oneline", f"HEAD..origin/master"],
                capture_output=True, text=True, cwd=SERVER_CODE_DIR, timeout=10
            )
            commit_msg = result.stdout.strip()

        return ServerUpdateCheckResponse(
            has_update=behind_count > 0,
            current_commit=current_commit[:8],
            latest_commit=latest_commit[:8],
            current_branch=current_branch,
            behind_count=behind_count,
            commit_message=commit_msg
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/server/apply")
async def server_apply_update():
    try:
        subprocess.run(
            ["git", "fetch", "origin"],
            capture_output=True, text=True, cwd=SERVER_CODE_DIR, timeout=30
        )

        result = subprocess.run(
            ["git", "pull", "origin", "master"],
            capture_output=True, text=True, cwd=SERVER_CODE_DIR, timeout=60
        )

        output = result.stdout + "\n" + result.stderr

        if result.returncode != 0:
            return ServerUpdateApplyResponse(
                success=False,
                message="更新失败",
                output=output
            )

        return ServerUpdateApplyResponse(
            success=True,
            message="更新成功",
            output=output
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


CURRENT_CLIENT_VERSION = "1.4.6"

@router.get("/client/version")
async def get_client_version():
    return {
        "version": CURRENT_CLIENT_VERSION,
        "platform": platform.system().lower(),
        "arch": platform.machine()
    }

@router.get("/client/check")
async def check_client_update():
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{GITEE_API}/releases/latest?access_token={GITEE_TOKEN}")
            if resp.status_code != 200:
                return ClientCheckResponse(
                    has_update=False,
                    current_version=CURRENT_CLIENT_VERSION,
                    latest_version=CURRENT_CLIENT_VERSION
                )

            release = resp.json()
            latest_version = release.get("tag_name", "").lstrip("v")
            changelog = release.get("body", "")

            has_update = latest_version != CURRENT_CLIENT_VERSION

            download_url = None
            if has_update:
                assets = release.get("assets", [])
                system = platform.system().lower()
                for asset in assets:
                    name = asset.get("name", "").lower()
                    if system == "linux" and "amd64.deb" in name:
                        download_url = asset.get("browser_download_url")
                        break
                    elif system == "windows" and ("windows" in name or ".exe" in name):
                        download_url = asset.get("browser_download_url")
                        break

            return ClientCheckResponse(
                has_update=has_update,
                current_version=CURRENT_CLIENT_VERSION,
                latest_version=latest_version,
                download_url=download_url,
                changelog=changelog
            )
    except Exception:
        return ClientCheckResponse(
            has_update=False,
            current_version=CURRENT_CLIENT_VERSION,
            latest_version=CURRENT_CLIENT_VERSION
        )

@router.get("/client/releases")
async def list_client_releases():
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{GITEE_API}/releases?access_token={GITEE_TOKEN}")
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

@router.get("/client/download/{version}")
async def get_client_download_url(version: str):
    system = platform.system().lower()
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            tag = f"v{version}" if not version.startswith("v") else version
            resp = await client.get(f"{GITEE_API}/releases/tags/{tag}?access_token={GITEE_TOKEN}")
            if resp.status_code != 200:
                raise HTTPException(status_code=404, detail="版本不存在")

            release = resp.json()
            assets = release.get("assets", [])

            for asset in assets:
                name = asset.get("name", "").lower()
                if system == "linux" and "amd64.deb" in name:
                    return {"download_url": asset.get("browser_download_url")}
                elif system == "windows" and (".exe" in name):
                    return {"download_url": asset.get("browser_download_url")}

            return {"download_url": None, "message": "未找到对应平台的安装包"}
    except httpx.HTTPError:
        raise HTTPException(status_code=500, detail="获取下载链接失败")
