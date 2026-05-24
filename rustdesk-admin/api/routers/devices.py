from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database import get_db, Device, User, AuditLog
from auth import get_current_user, get_admin_user
import aiosqlite
from config import settings

router = APIRouter(prefix="/api/devices", tags=["设备管理"])

class DeviceRegister(BaseModel):
    id: str
    uuid: str | None = None
    hostname: str | None = None
    platform: str | None = None
    group_name: str | None = None

@router.get("")
async def list_devices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.is_admin:
        result = await db.execute(select(Device))
    else:
        result = await db.execute(
            select(Device).where(Device.user_id == current_user.id)
        )
    
    devices = result.scalars().all()
    
    async with aiosqlite.connect(settings.HBBS_DB_PATH) as hbbs_db:
        hbbs_db.row_factory = aiosqlite.Row
        cursor = await hbbs_db.execute("SELECT id, status, info FROM peer")
        peers = {row["id"]: dict(row) async for row in cursor}
    
    return [
        {
            "id": d.id,
            "peer_id": d.peer_id,
            "uuid": d.uuid,
            "hostname": d.hostname,
            "platform": d.platform,
            "group_name": d.group_name,
            "user_id": d.user_id,
            "is_online": peers.get(d.peer_id, {}).get("status", 0) == 0,
            "last_seen": d.last_seen.isoformat() if d.last_seen else None,
            "info": peers.get(d.peer_id, {}).get("info"),
            "created_at": d.created_at.isoformat() if d.created_at else None
        }
        for d in devices
    ]

@router.post("/register")
async def register_device(
    req: DeviceRegister,
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Device).where(Device.peer_id == req.id)
    )
    device = result.scalar_one_or_none()
    
    if device:
        device.uuid = req.uuid or device.uuid
        device.hostname = req.hostname or device.hostname
        device.platform = req.platform or device.platform
        device.group_name = req.group_name or device.group_name
        device.last_seen = datetime.utcnow()
        if not device.user_id:
            device.user_id = current_user.id
    else:
        device = Device(
            peer_id=req.id,
            uuid=req.uuid,
            hostname=req.hostname,
            platform=req.platform,
            group_name=req.group_name,
            user_id=current_user.id,
            last_seen=datetime.utcnow()
        )
        db.add(device)
    
    audit = AuditLog(
        user_id=current_user.id,
        action="device_register",
        target_peer=req.id,
        ip_address=request.client.host if request and request.client else None
    )
    db.add(audit)
    await db.commit()
    
    return {"success": True, "peer_id": device.peer_id}

@router.put("/{device_id}")
async def update_device(
    device_id: int,
    req: DeviceRegister,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    if req.hostname is not None:
        device.hostname = req.hostname
    if req.platform is not None:
        device.platform = req.platform
    if req.group_name is not None:
        device.group_name = req.group_name
    
    await db.commit()
    return {"success": True}

@router.delete("/{device_id}")
async def delete_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    if not current_user.is_admin and device.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权删除此设备")
    
    await db.delete(device)
    await db.commit()
    return {"success": True}

@router.get("/online")
async def get_online_devices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    async with aiosqlite.connect(settings.HBBS_DB_PATH) as hbbs_db:
        hbbs_db.row_factory = aiosqlite.Row
        cursor = await hbbs_db.execute(
            "SELECT id, status, info FROM peer WHERE status = 0"
        )
        online_peers = [dict(row) async for row in cursor]
    
    return online_peers
