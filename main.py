import os
import uuid
import datetime
from fastapi import FastAPI, Depends, HTTPException, Request, Response, Form, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel
import asyncio
import json

class NoteCreate(BaseModel):
    content: str

class BucketCreate(BaseModel):
    title: str

class TimeCapsuleCreate(BaseModel):
    content: str
    unlock_date: str

class MarkerCreate(BaseModel):
    lat: str
    lng: str
    title: str
    description: str

import models
from database import engine, get_db
from sqladmin import Admin, ModelView

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# Setup Admin Panel
admin = Admin(app, engine)

class UserAdmin(ModelView, model=models.User):
    column_list = [models.User.id, models.User.username, models.User.display_name]
    name = "Tài Khoản"
    name_plural = "Tài Khoản"

class ImageAdmin(ModelView, model=models.Image):
    column_list = [models.Image.id, models.Image.filename, models.Image.uploader_id, models.Image.upload_time]
    name = "Hình Ảnh"
    name_plural = "Hình Ảnh"

class NoteAdmin(ModelView, model=models.Note):
    column_list = [models.Note.id, models.Note.content, models.Note.author_id, models.Note.created_at]
    name = "Lời Nhắc"
    name_plural = "Lời Nhắc"

admin.add_view(UserAdmin)
admin.add_view(ImageAdmin)
admin.add_view(NoteAdmin)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# In-memory session store (token -> user_id)
sessions = {}

def get_current_user(request: Request, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    if not session_token:
        return None
    user_id = sessions.get(session_token)
    if not user_id:
        return None
    user = db.query(models.User).filter(models.User.id == user_id).first()
    return user

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.on_event("startup")
def create_initial_users():
    db = next(get_db())
    if db.query(models.User).count() == 0:
        # Create user 1
        u1 = models.User(username="bang", password_hash="123456", display_name="Trần Hải Bằng")
        # Create user 2
        u2 = models.User(username="tuyet", password_hash="123456", display_name="Trần Thị Tuyết")
        db.add(u1)
        db.add(u2)
        db.commit()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    
    images = db.query(models.Image).order_by(models.Image.upload_time.desc()).all()
    
    # Enrich with uploader name
    for img in images:
        uploader = db.query(models.User).filter(models.User.id == img.uploader_id).first()
        img.uploader_name = uploader.display_name if uploader else "Unknown"

    return templates.TemplateResponse("index.html", {"request": request, "user": user, "images": images})

@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login_post(response: Response, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or user.password_hash != password:
        return RedirectResponse(url="/login?error=1", status_code=303)
    
    session_token = str(uuid.uuid4())
    sessions[session_token] = user.id
    
    redirect_resp = RedirectResponse(url="/", status_code=303)
    redirect_resp.set_cookie(key="session_token", value=session_token, httponly=True)
    return redirect_resp

@app.get("/logout")
async def logout(response: Response, request: Request):
    session_token = request.cookies.get("session_token")
    if session_token in sessions:
        del sessions[session_token]
    redirect_resp = RedirectResponse(url="/login", status_code=303)
    redirect_resp.delete_cookie("session_token")
    return redirect_resp

@app.post("/upload")
async def upload_image(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    content = await file.read()
    content_type = file.content_type or "image/jpeg"
    new_image = models.Image(
        filename=file.filename,
        content_type=content_type,
        data=content,
        uploader_id=user.id
    )
    db.add(new_image)
    db.commit()
    db.refresh(new_image)
    
    await manager.broadcast(f"photo|{user.display_name} vừa tải lên một bức ảnh mới nha!")
    return RedirectResponse(url="/", status_code=303)

@app.get("/image/{image_id}")
async def serve_image(image_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401)
    img = db.query(models.Image).filter(models.Image.id == image_id).first()
    if not img or not img.data:
        raise HTTPException(status_code=404)
    return Response(content=img.data, media_type=img.content_type or "image/jpeg")

@app.post("/notes")
async def create_note(note: NoteCreate, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    new_note = models.Note(content=note.content, author_id=user.id)
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    
    await manager.broadcast(f"note|{user.display_name} vừa viết một lời nhắn mới!")
    return {"status": "ok", "id": new_note.id}

@app.get("/notes")
async def get_notes(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    notes = db.query(models.Note).order_by(models.Note.created_at.desc()).limit(50).all()
    result = []
    for n in notes:
        author = db.query(models.User).filter(models.User.id == n.author_id).first()
        result.append({
            "id": n.id,
            "content": n.content,
            "author_name": author.display_name if author else "Unknown",
            "created_at": n.created_at.strftime('%d/%m/%Y %H:%M')
        })
    return result

@app.post("/bucket")
async def create_bucket(item: BucketCreate, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    new_item = models.BucketItem(title=item.title)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    await manager.broadcast(f"note|{user.display_name} vừa thêm một Thử thách mới vào Danh sách: {item.title}!")
    return {"status": "ok", "id": new_item.id}

@app.get("/bucket")
async def get_bucket(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    items = db.query(models.BucketItem).order_by(models.BucketItem.id.desc()).all()
    return [{"id": i.id, "title": i.title, "is_completed": i.is_completed} for i in items]

@app.post("/bucket/{item_id}/toggle")
async def toggle_bucket(item_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    item = db.query(models.BucketItem).filter(models.BucketItem.id == item_id).first()
    if item:
        item.is_completed = 1 if item.is_completed == 0 else 0
        db.commit()
        status_text = "hoàn thành" if item.is_completed else "hủy hoàn thành"
        await manager.broadcast(f"note|{user.display_name} vừa {status_text} thử thách: {item.title}!")
        return {"status": "ok", "is_completed": item.is_completed}
    raise HTTPException(status_code=404)

@app.post("/capsules")
async def create_capsule(capsule: TimeCapsuleCreate, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    ud = datetime.datetime.strptime(capsule.unlock_date, "%Y-%m-%d")
    new_cap = models.TimeCapsule(content=capsule.content, author_id=user.id, unlock_date=ud)
    db.add(new_cap)
    db.commit()
    await manager.broadcast(f"note|{user.display_name} vừa giấu một bức thư tương lai! Bí mật sẽ được bật mí vào ngày {ud.strftime('%d/%m/%Y')}!")
    return {"status": "ok"}

@app.get("/capsules")
async def get_capsules(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    capsules = db.query(models.TimeCapsule).order_by(models.TimeCapsule.unlock_date.asc()).all()
    result = []
    
    # Reset microseconds to allow matching just by days correctly, or use simple check
    now = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    for c in capsules:
        author = db.query(models.User).filter(models.User.id == c.author_id).first()
        is_locked = c.unlock_date > now
        result.append({
            "id": c.id,
            "author_name": author.display_name if author else "Unknown",
            "unlock_date": c.unlock_date.strftime("%d/%m/%Y"),
            "created_at": c.created_at.strftime('%d/%m/%Y'),
            "is_locked": is_locked,
            "content": "🔒 Bức thư đang bị khóa thời gian!" if is_locked else c.content
        })
    return result

@app.get("/tree-status")
async def get_tree_status(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Calculate EXP
    images_count = db.query(models.Image).count()
    notes_count = db.query(models.Note).count()
    buckets_count = db.query(models.BucketItem).filter(models.BucketItem.is_completed == 1).count()
    capsules_count = db.query(models.TimeCapsule).count()
    
    exp = (images_count * 10) + (notes_count * 5) + (buckets_count * 15) + (capsules_count * 20)
    
    # Level breakpoints
    exp_table = [0, 50, 150, 300, 600, 1000, 1500, 2500, 4000, 6000]
    level = 1
    next_level_exp = 50
    current_level_base = 0
    
    for i, req_exp in enumerate(exp_table):
        if exp < req_exp:
            level = i
            next_level_exp = req_exp
            current_level_base = exp_table[i-1]
            break
    else:
        level = len(exp_table)
        next_level_exp = exp
        current_level_base = exp
        
    exp_in_level = exp - current_level_base
    exp_needed = next_level_exp - current_level_base
    progress = 100 if exp_needed == 0 else int((exp_in_level / exp_needed) * 100)
    
    return {
        "exp": exp,
        "level": level,
        "progress": progress,
        "next_level_exp": next_level_exp
    }

@app.get("/map", response_class=HTMLResponse)
async def map_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("map.html", {"request": request, "user": user})

@app.get("/markers")
async def get_markers(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    markers = db.query(models.MemoryMarker).all()
    return [{"id": m.id, "lat": m.lat, "lng": m.lng, "title": m.title, "description": m.description} for m in markers]

@app.post("/markers")
async def create_marker(marker: MarkerCreate, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    new_marker = models.MemoryMarker(lat=marker.lat, lng=marker.lng, title=marker.title, description=marker.description)
    db.add(new_marker)
    db.commit()
    await manager.broadcast(f"photo|{user.display_name} vừa ghim một địa điểm kỷ niệm trên Bản đồ Tình Yêu: {marker.title}!")
    return {"status": "ok"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
