from uuid import UUID
from fastapi import FastAPI, Depends, HTTPException
from pydantic.utils import to_camel
from schemas import CreateUser
from sqlalchemy.orm import Session
from database import get_db
from models import User
from auth import AuthHandler
from schemas import AuthDetails


app = FastAPI()

auth_handler = AuthHandler()
users = []

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

@app.post('/register', status_code=201)
def register(auth_details: AuthDetails):
    if any(x['username'] == auth_details.username for x in users):
        raise HTTPException(status_code=400, detail='Username is taken')
    hashed_password = auth_handler.get_password_hash(auth_details.password)
    users.append({
        'username': auth_details.username,
        'password': hashed_password    
    })
    return


@app.post('/login')
def login(auth_details: AuthDetails):
    user = None
    for x in users:
        if x['username'] == auth_details.username:
            user = x
            break
    
    if (user is None) or (not auth_handler.verify_password(auth_details.password, user['password'])):
        raise HTTPException(status_code=401, detail='Invalid username and/or password')
    token = auth_handler.encode_token(user['username'])
    return { 'token': token }


@app.get('/unprotected')
def unprotected():
    return { 'hello': 'world' }


@app.get('/protected')
def protected(username=Depends(auth_handler.auth_wrapper)):
    return { 'name': username }