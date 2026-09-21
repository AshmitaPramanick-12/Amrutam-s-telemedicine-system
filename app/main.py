from fastapi import FastAPI, Depends, HTTPException, Header, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, String, Boolean, DateTime, ForeignKey, Integer, Text, select, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker, Session
from pydantic import BaseModel, Field
from datetime import datetime, timezone, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from prometheus_fastapi_instrumentator import Instrumentator
from typing import Optional
import os, uuid, logging, json

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./amrutam.db")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
ALGORITHM = "HS256"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer = HTTPBearer()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("amrutam")

class Base(DeclarativeBase): pass

class User(Base):
    __tablename__="users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda:str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default="patient", index=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda:datetime.now(timezone.utc))

class Doctor(Base):
    __tablename__="doctors"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda:str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    specialty: Mapped[str] = mapped_column(String(120), index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

class Slot(Base):
    __tablename__="availability_slots"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda:str(uuid.uuid4()))
    doctor_id: Mapped[str] = mapped_column(ForeignKey("doctors.id"), index=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20), default="available", index=True)

class Consultation(Base):
    __tablename__="consultations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda:str(uuid.uuid4()))
    patient_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    doctor_id: Mapped[str] = mapped_column(ForeignKey("doctors.id"), index=True)
    slot_id: Mapped[str] = mapped_column(ForeignKey("availability_slots.id"), unique=True)
    status: Mapped[str] = mapped_column(String(30), default="booked", index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda:datetime.now(timezone.utc))

class Prescription(Base):
    __tablename__="prescriptions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda:str(uuid.uuid4()))
    consultation_id: Mapped[str] = mapped_column(ForeignKey("consultations.id"), index=True)
    medicine: Mapped[str] = mapped_column(String(255))
    dosage: Mapped[str] = mapped_column(String(255))
    instructions: Mapped[str] = mapped_column(Text)

class AuditLog(Base):
    __tablename__="audit_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda:str(uuid.uuid4()))
    actor_id: Mapped[str] = mapped_column(String(36), index=True)
    action: Mapped[str] = mapped_column(String(120), index=True)
    resource: Mapped[str] = mapped_column(String(120))
    resource_id: Mapped[str] = mapped_column(String(36))
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda:datetime.now(timezone.utc), index=True)

class IdempotencyKey(Base):
    __tablename__="idempotency_keys"
    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    response_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda:datetime.now(timezone.utc))

Base.metadata.create_all(engine)

def db():
    s=SessionLocal()
    try: yield s
    finally: s.close()

def token_for(u:User):
    return jwt.encode({"sub":u.id,"role":u.role,"exp":datetime.now(timezone.utc)+timedelta(minutes=30)},JWT_SECRET,algorithm=ALGORITHM)

def current_user(c:HTTPAuthorizationCredentials=Depends(bearer), s:Session=Depends(db)):
    try: payload=jwt.decode(c.credentials,JWT_SECRET,algorithms=[ALGORITHM])
    except JWTError: raise HTTPException(401,"Invalid token")
    u=s.get(User,payload.get("sub"))
    if not u: raise HTTPException(401,"User not found")
    return u

def role(*roles):
    def dep(u=Depends(current_user)):
        if u.role not in roles: raise HTTPException(403,"Forbidden")
        return u
    return dep

class Register(BaseModel):
    email:str
    password:str=Field(min_length=8)
    role:str="patient"

class Login(BaseModel):
    email:str
    password:str

class SlotIn(BaseModel):
    starts_at:datetime
    ends_at:datetime

class BookIn(BaseModel):
    doctor_id:str
    slot_id:str

class PrescriptionIn(BaseModel):
    medicine:str
    dosage:str
    instructions:str

app=FastAPI(title="Amrutam Telemedicine API",version="1.0.0")
Instrumentator().instrument(app).expose(app)

@app.get("/health")
def health(s:Session=Depends(db)):
    try: s.execute(select(1)); return {"status":"ok","db":"ok"}
    except Exception: raise HTTPException(503,"database unavailable")

@app.post("/auth/register")
def register(x:Register,s:Session=Depends(db)):
    if x.role not in {"patient","doctor","admin"}: raise HTTPException(400,"Invalid role")
    if s.scalar(select(User).where(User.email==x.email)): raise HTTPException(409,"Email already exists")
    u=User(email=x.email,password_hash=pwd.hash(x.password),role=x.role)
    s.add(u); s.commit(); s.refresh(u)
    if x.role=="doctor":
        d=Doctor(user_id=u.id,name=x.email.split("@")[0],specialty="General Medicine"); s.add(d); s.commit()
    return {"id":u.id,"token":token_for(u)}

@app.post("/auth/login")
def login(x:Login,s:Session=Depends(db)):
    u=s.scalar(select(User).where(User.email==x.email))
    if not u or not pwd.verify(x.password,u.password_hash): raise HTTPException(401,"Invalid credentials")
    return {"access_token":token_for(u),"token_type":"bearer","mfa_required":u.mfa_enabled}

@app.get("/doctors")
def search_doctors(q:str="",specialty:str="",s:Session=Depends(db)):
    stmt=select(Doctor).where(Doctor.active.is_(True))
    if q: stmt=stmt.where(Doctor.name.ilike(f"%{q}%"))
    if specialty: stmt=stmt.where(Doctor.specialty.ilike(f"%{specialty}%"))
    return [{"id":d.id,"name":d.name,"specialty":d.specialty} for d in s.scalars(stmt).all()]

@app.post("/doctors/{doctor_id}/slots")
def create_slot(doctor_id:str,x:SlotIn,s:Session=Depends(db),u=Depends(role("doctor","admin"))):
    if u.role=="doctor" and not s.scalar(select(Doctor).where(Doctor.id==doctor_id,Doctor.user_id==u.id)): raise HTTPException(403,"Not your doctor profile")
    if x.ends_at<=x.starts_at: raise HTTPException(400,"Invalid interval")
    slot=Slot(doctor_id=doctor_id,starts_at=x.starts_at,ends_at=x.ends_at)
    s.add(slot); s.commit(); s.refresh(slot)
    return {"id":slot.id,"status":slot.status}

@app.get("/doctors/{doctor_id}/slots")
def slots(doctor_id:str,s:Session=Depends(db)):
    return [{"id":x.id,"starts_at":x.starts_at,"ends_at":x.ends_at,"status":x.status}
            for x in s.scalars(select(Slot).where(Slot.doctor_id==doctor_id,Slot.status=="available").order_by(Slot.starts_at)).all()]

@app.post("/consultations/book")
def book(x:BookIn, idempotency_key:str=Header(...,alias="Idempotency-Key"), s:Session=Depends(db), u=Depends(role("patient"))):
    import hashlib
    raw=f"{x.doctor_id}:{x.slot_id}:{u.id}".encode(); h=hashlib.sha256(raw).hexdigest()
    old=s.get(IdempotencyKey,idempotency_key)
    if old:
        if old.request_hash!=h: raise HTTPException(409,"Idempotency key reused with different request")
        return json.loads(old.response_json)
    slot=s.execute(select(Slot).where(Slot.id==x.slot_id,Slot.doctor_id==x.doctor_id).with_for_update()).scalar_one_or_none()
    if not slot or slot.status!="available": raise HTTPException(409,"Slot unavailable")
    c=Consultation(patient_id=u.id,doctor_id=x.doctor_id,slot_id=slot.id)
    slot.status="booked"; s.add(c); s.flush()
    s.add(AuditLog(actor_id=u.id,action="BOOK_CONSULTATION",resource="consultation",resource_id=c.id))
    result={"id":c.id,"status":c.status}
    s.add(IdempotencyKey(key=idempotency_key,request_hash=h,response_json=json.dumps(result)))
    s.commit()
    return result

@app.get("/consultations/{cid}")
def consultation(cid:str,s:Session=Depends(db),u=Depends(current_user)):
    c=s.get(Consultation,cid)
    if not c or (u.role=="patient" and c.patient_id!=u.id): raise HTTPException(404,"Not found")
    return {"id":c.id,"doctor_id":c.doctor_id,"patient_id":c.patient_id,"slot_id":c.slot_id,"status":c.status,"notes":c.notes}

@app.post("/consultations/{cid}/complete")
def complete(cid:str,s:Session=Depends(db),u=Depends(role("doctor","admin"))):
    c=s.get(Consultation,cid)
    if not c: raise HTTPException(404,"Not found")
    c.status="completed"; s.add(AuditLog(actor_id=u.id,action="COMPLETE_CONSULTATION",resource="consultation",resource_id=cid)); s.commit()
    return {"id":cid,"status":c.status}

@app.post("/consultations/{cid}/prescriptions")
def prescription(cid:str,x:PrescriptionIn,s:Session=Depends(db),u=Depends(role("doctor","admin"))):
    c=s.get(Consultation,cid)
    if not c or c.status!="completed": raise HTTPException(409,"Consultation must be completed")
    p=Prescription(consultation_id=cid,medicine=x.medicine,dosage=x.dosage,instructions=x.instructions)
    s.add(p); s.add(AuditLog(actor_id=u.id,action="CREATE_PRESCRIPTION",resource="prescription",resource_id=p.id)); s.commit(); s.refresh(p)
    return {"id":p.id}

@app.get("/admin/analytics")
def analytics(s:Session=Depends(db),u=Depends(role("admin"))):
    return {"users":s.scalar(select(func.count(User.id))),
            "doctors":s.scalar(select(func.count(Doctor.id))),
            "consultations":s.scalar(select(func.count(Consultation.id))),
            "completed":s.scalar(select(func.count(Consultation.id)).where(Consultation.status=="completed"))}
