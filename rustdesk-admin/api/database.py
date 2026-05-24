from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, create_engine
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from config import settings

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    email = Column(String(100), unique=True, nullable=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    group = relationship("Group", back_populates="users")
    address_book = relationship("AddressBookEntry", back_populates="user", cascade="all, delete-orphan")
    devices = relationship("Device", back_populates="user", cascade="all, delete-orphan")

class Group(Base):
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200), nullable=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    users = relationship("User", back_populates="group")
    strategy = relationship("Strategy", back_populates="groups")

class Strategy(Base):
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    allow_remote = Column(Boolean, default=True)
    allow_file_transfer = Column(Boolean, default=True)
    allow_clipboard = Column(Boolean, default=True)
    allow_keyboard = Column(Boolean, default=True)
    allow_mouse = Column(Boolean, default=True)
    allow_audio = Column(Boolean, default=False)
    allow_terminal = Column(Boolean, default=False)
    force_confirm = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    groups = relationship("Group", back_populates="strategy")

class AddressBookEntry(Base):
    __tablename__ = "address_book"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    peer_id = Column(String(20), nullable=False, index=True)
    alias = Column(String(100), nullable=True)
    tags = Column(String(200), nullable=True)
    password = Column(String(128), nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="address_book")

class Device(Base):
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    peer_id = Column(String(20), unique=True, nullable=False, index=True)
    uuid = Column(String(64), nullable=True)
    hostname = Column(String(100), nullable=True)
    platform = Column(String(20), nullable=True)
    group_name = Column(String(50), nullable=True)
    is_online = Column(Boolean, default=False)
    last_seen = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="devices")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True, index=True)
    action = Column(String(50), nullable=False)
    target_peer = Column(String(20), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

DATABASE_URL = f"sqlite+aiosqlite:///{settings.ADMIN_DB_PATH}"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.is_admin == True))
        if not result.scalar_one_or_none():
            from auth import hash_password
            
            admin = User(
                username="admin",
                password_hash=hash_password("admin"),
                email="admin@xiaoxiang.local",
                is_admin=True,
                is_active=True
            )
            session.add(admin)
            
            default_strategy = Strategy(name="默认策略")
            session.add(default_strategy)
            await session.commit()

async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
