from uuid import UUID
from fastapi import FastAPI, Depends
from pydantic.utils import to_camel
from schemas import CreateUser
from sqlalchemy.orm import Session
from database import get_db
from models import User


app = FastAPI()

@app.post("/users")
def create(details: CreateUser, db: Session = Depends(get_db)):
    to_create = User(
        email=details.email,
        name=details.name
    )
    db.add(to_create)
    db.commit()
    return {
        "success": True,
        "created_at": to_create.id
    }

@app.get("/users")
def get_by_id(id: str, db: Session = Depends(get_db)):
    return db.query(User).filter(User.id == id).first()

@app.delete("/users")
def delete(id: str, db: Session = Depends(get_db)):
    db.query(User).filter(User.id == id).delete()
    db.commit()
    return {"success": True}