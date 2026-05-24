from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from database import get_db, AddressBookEntry, User
from auth import get_current_user

router = APIRouter(prefix="/api/ab", tags=["地址簿"])

class AddressBookData(BaseModel):
    tags: list[str] = []
    peers: list[dict] = []

class AbEntry(BaseModel):
    id: str
    alias: str | None = None
    tags: list[str] = []
    password: str | None = None
    note: str | None = None

@router.get("/get")
async def get_address_book(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(AddressBookEntry).where(AddressBookEntry.user_id == current_user.id)
    )
    entries = result.scalars().all()
    
    all_tags = set()
    peers = []
    
    for entry in entries:
        tags = entry.tags.split(",") if entry.tags else []
        all_tags.update(tags)
        peers.append({
            "id": entry.peer_id,
            "alias": entry.alias,
            "tags": tags,
            "password": entry.password,
            "note": entry.note
        })
    
    return {
        "tags": list(all_tags),
        "peers": peers
    }

@router.post("")
async def update_address_book(
    req: AddressBookData,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await db.execute(
        delete(AddressBookEntry).where(AddressBookEntry.user_id == current_user.id)
    )
    
    for peer in req.peers:
        entry = AddressBookEntry(
            user_id=current_user.id,
            peer_id=peer.get("id"),
            alias=peer.get("alias"),
            tags=",".join(peer.get("tags", [])),
            password=peer.get("password"),
            note=peer.get("note")
        )
        db.add(entry)
    
    await db.commit()
    return {"success": True}

@router.post("/add")
async def add_address_book_entry(
    req: AbEntry,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(AddressBookEntry).where(
            AddressBookEntry.user_id == current_user.id,
            AddressBookEntry.peer_id == req.id
        )
    )
    entry = result.scalar_one_or_none()
    
    if entry:
        entry.alias = req.alias or entry.alias
        entry.tags = ",".join(req.tags) if req.tags else entry.tags
        entry.password = req.password or entry.password
        entry.note = req.note or entry.note
    else:
        entry = AddressBookEntry(
            user_id=current_user.id,
            peer_id=req.id,
            alias=req.alias,
            tags=",".join(req.tags),
            password=req.password,
            note=req.note
        )
        db.add(entry)
    
    await db.commit()
    return {"success": True}

@router.delete("/{peer_id}")
async def delete_address_book_entry(
    peer_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await db.execute(
        delete(AddressBookEntry).where(
            AddressBookEntry.user_id == current_user.id,
            AddressBookEntry.peer_id == peer_id
        )
    )
    await db.commit()
    return {"success": True}
