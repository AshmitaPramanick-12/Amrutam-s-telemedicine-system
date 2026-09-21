import os
os.environ["DATABASE_URL"]="sqlite:///./test.db"
from fastapi.testclient import TestClient
from app.main import app, Base, engine
Base.metadata.drop_all(engine); Base.metadata.create_all(engine)
client=TestClient(app)

def test_auth_and_booking():
    p=client.post("/auth/register",json={"email":"p@test.com","password":"password123","role":"patient"}).json()
    d=client.post("/auth/register",json={"email":"d@test.com","password":"password123","role":"doctor"}).json()
    assert p["id"] and d["id"]
    token=d["token"]
    # discover doctor
    doc=client.get("/doctors").json()[0]
    from datetime import datetime,timedelta,timezone
    s=client.post(f"/doctors/{doc['id']}/slots",headers={"Authorization":f"Bearer {token}"},json={
        "starts_at":(datetime.now(timezone.utc)+timedelta(hours=2)).isoformat(),
        "ends_at":(datetime.now(timezone.utc)+timedelta(hours=2,minutes=30)).isoformat()}).json()
    pt=client.post("/auth/login",json={"email":"p@test.com","password":"password123"}).json()
    r=client.post("/consultations/book",headers={"Authorization":f"Bearer {pt['access_token']}","Idempotency-Key":"abc-1"},
                  json={"doctor_id":doc["id"],"slot_id":s["id"]})
    assert r.status_code==200
    r2=client.post("/consultations/book",headers={"Authorization":f"Bearer {pt['access_token']}","Idempotency-Key":"abc-1"},
                  json={"doctor_id":doc["id"],"slot_id":s["id"]})
    assert r2.json()["id"]==r.json()["id"]
