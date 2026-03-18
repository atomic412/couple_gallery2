import datetime
from sqlalchemy import Column, Integer, String, DateTime, LargeBinary
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    display_name = Column(String)

class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    content_type = Column(String, default="image/jpeg")
    data = Column(LargeBinary, nullable=True)
    uploader_id = Column(Integer)
    upload_time = Column(DateTime, default=datetime.datetime.utcnow)

class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)
    author_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class BucketItem(Base):
    __tablename__ = "bucket_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    is_completed = Column(Integer, default=0)

class TimeCapsule(Base):
    __tablename__ = "time_capsules"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)
    author_id = Column(Integer)
    unlock_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class MemoryMarker(Base):
    __tablename__ = "memory_markers"

    id = Column(Integer, primary_key=True, index=True)
    lat = Column(String)
    lng = Column(String)
    title = Column(String)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
