from typing import Optional
from schemas import ConfirmUser
from uuid import UUID
from fastapi import FastAPI, Depends, HTTPException
from pydantic.utils import to_camel
from schemas import CreateUser
from sqlalchemy.orm import Session
from database import get_db
from models import User, Group, t_user_group
from auth import AuthHandler
from schemas import AuthDetails


app = FastAPI(debug=True)

auth_handler = AuthHandler()
users = []

#@todo - Unit test, sending confirmation email
@app.post("/users")
def create(details: CreateUser, db: Session = Depends(get_db)):
    user = User(
        id=details.id,
        email=details.email,
        name=details.name,
        role_id=details.role,
    )

    for group in details.groups:
        group_entity = db.query(Group).get(group)
        user.groups.append(group_entity)

    db.add(user)
    db.commit()
    return {
        "success": True
    }

#@todo - Unit test
@app.get("/users")
def get_by_filter(id: Optional[str] = None, group: Optional[str] = None, role: Optional[str] = None, db: Session = Depends(get_db)):
    filters = {}

    if(id):
        filters['id'] = id
    if(group):
        filters['id'] = group
    if(role):
        filters['role_id'] = role

    return db.query(User).join(User.groups).filter_by(**filters).all()

#@todo - Unit test
@app.delete("/users/{id}")
def delete_by_id(id: str, db: Session = Depends(get_db)):
    user = db.query(User).get(id)
    db.delete(user)
    db.commit()


@app.post("/users/{id}/confirm")
def confirm(id, details: ConfirmUser, db: Session = Depends(get_db)):
    user = db.query(User).get(id)
    user.active = 1
    db.commit()
    return user



@app.delete("/users")
def delete(id: str, db: Session = Depends(get_db)):
    db.query(User).filter(User.id == id).delete()
    db.commit()
    return {"success": True}

@app.post('/register', status_code=201)
def register(auth_details: AuthDetails):
    return auth_handler.get_password_hash(auth_details.password)
    if any(x['username'] == auth_details.username for x in users):
        raise HTTPException(status_code=400, detail='Username is taken')
    hashed_password = auth_handler.get_password_hash(auth_details.password)
    users.append({
        'username': auth_details.username,
        'password': hashed_password    
    })
    return


@app.post('/login')
def login(auth_details: AuthDetails, db: Session = Depends(get_db)):
    user = None
    user = db.query(User).filter(User.email == auth_details.username).first()
    if (user == None):
        raise HTTPException(status_code=401, detail='Invalid username and/or password')
    else:
        return auth_handler.verify_password('test', "$2b$12$zpHIKCeJyfCXf/w72Fo7POcxzRHTEHrfBqCdD0NLEmfesEd1nnjl2")
    # if (user is None) or (not auth_handler.verify_password(auth_details.password, user['password'])):
    #     raise HTTPException(status_code=401, detail='Invalid username and/or password')
    # token = auth_handler.encode_token(user['username'])
    # return { 'token': token }


@app.get('/unprotected')
def unprotected():
    return { 'hello': 'world' }


@app.get('/protected')
def protected(username=Depends(auth_handler.auth_wrapper)):
    return { 'name': username }