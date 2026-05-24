from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database import get_db, User, Group, AuditLog
from auth import verify_password, hash_password, create_access_token, get_current_user, get_admin_user
from config import settings

router = APIRouter(prefix="/api", tags=["认证"])

class LoginRequest(BaseModel):
    username: str
    password: str
    id: str | None = None
    uuid: str | None = None
    type: str = "account"

class LoginResponse(BaseModel):
    access_token: str
    user: dict

class UserCreate(BaseModel):
    username: str
    password: str
    email: str | None = None
    group_id: int | None = None
    is_admin: bool = False

class UserUpdate(BaseModel):
    email: str | None = None
    group_id: int | None = None
    is_admin: bool | None = None
    is_active: bool | None = None
    password: str | None = None

@router.post("/login", response_model=LoginResponse)
async def login(
    req: LoginRequest, 
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(User.username == req.username)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用"
        )
    
    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(last_login=datetime.utcnow())
    )
    
    audit = AuditLog(
        user_id=user.id,
        action="login",
        ip_address=request.client.host if request.client else None
    )
    db.add(audit)
    await db.commit()
    
    token = create_access_token(user.id, user.username)
    
    return LoginResponse(
        access_token=token,
        user={
            "id": user.id,
            "name": user.username,
            "email": user.email,
            "is_admin": user.is_admin
        }
    )

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return {"success": True}

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str | None = None
    id: str | None = None
    uuid: str | None = None

@router.post("/register")
async def register(
    req: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    existing = await db.execute(
        select(User).where(User.username == req.username)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        email=req.email,
        is_admin=False,
        is_active=True
    )
    db.add(user)
    
    audit = AuditLog(
        action="register",
        target_peer=req.id,
        ip_address=request.client.host if request.client else None,
        details=f"username={req.username}"
    )
    db.add(audit)
    await db.commit()
    
    token = create_access_token(user.id, user.username)
    
    return {
        "access_token": token,
        "user": {
            "id": user.id,
            "name": user.username,
            "email": user.email,
            "is_admin": False
        }
    }

@router.post("/currentUser")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "name": current_user.username,
        "email": current_user.email,
        "is_admin": current_user.is_admin
    }

@router.get("/users")
async def list_users(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "group_id": u.group_id,
            "is_admin": u.is_admin,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login": u.last_login.isoformat() if u.last_login else None
        }
        for u in users
    ]

@router.post("/users")
async def create_user(
    req: UserCreate,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    existing = await db.execute(
        select(User).where(User.username == req.username)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        email=req.email,
        group_id=req.group_id,
        is_admin=req.is_admin
    )
    db.add(user)
    await db.commit()
    
    return {"id": user.id, "username": user.username}

@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    req: UserUpdate,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if req.email is not None:
        user.email = req.email
    if req.group_id is not None:
        user.group_id = req.group_id
    if req.is_admin is not None:
        user.is_admin = req.is_admin
    if req.is_active is not None:
        user.is_active = req.is_active
    if req.password is not None:
        user.password_hash = hash_password(req.password)
    
    await db.commit()
    return {"success": True}

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    await db.delete(user)
    await db.commit()
    return {"success": True}
