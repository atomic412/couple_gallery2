import datetime
from sqlalchemy import Column, Integer, String, DateTime, LargeBinary, Boolean, Text, ForeignKey
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)     # username thường ngắn
    password_hash = Column(String(255), nullable=False)                         # hashed password cần dài
    display_name = Column(String(100), nullable=True)                           # tên hiển thị, có thể dài hơn

class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), index=True, nullable=False)                  # tên file ảnh
    content_type = Column(String(100), default="image/jpeg", nullable=False)    # MIME type
    data = Column(LargeBinary(length=4294967295), nullable=True)                # binary data (hỗ trợ LONGBLOB cho ảnh lớn)
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=False)       # liên kết với user
    upload_time = Column(DateTime, default=datetime.datetime.utcnow)

class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)                                      # nội dung note → dùng Text (không cần length)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class BucketItem(Base):
    __tablename__ = "bucket_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)                                 # tiêu đề mục tiêu
    is_completed = Column(Boolean, default=False)                               # thay Integer bằng Boolean cho rõ nghĩa
    # Nếu muốn liên kết với couple/user: thêm author_id hoặc couple_id
    # author_id = Column(Integer, ForeignKey("users.id"), nullable=False)

class TimeCapsule(Base):
    __tablename__ = "time_capsules"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)                                      # nội dung → Text để dài
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    unlock_date = Column(DateTime, nullable=False)                              # ngày mở
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class MemoryMarker(Base):
    __tablename__ = "memory_markers"

    id = Column(Integer, primary_key=True, index=True)
    lat = Column(String(50), nullable=False)                                    # vĩ độ (có thể dùng Float thay String)
    lng = Column(String(50), nullable=False)                                    # kinh độ
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)                                   # mô tả → Text
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    # Nếu muốn liên kết với user/couple: thêm author_id
    # author_id = Column(Integer, ForeignKey("users.id"), nullable=False)