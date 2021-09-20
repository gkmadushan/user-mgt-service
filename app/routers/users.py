from sqlalchemy.sql.sqltypes import DateTime
from sqlalchemy.exc import IntegrityError
from models import OnetimeToken
from fastapi import APIRouter, Depends, HTTPException, Request
from dependencies import common_params, get_db, get_secret_random
from schemas import CreateUser
from sqlalchemy.orm import Session
from typing import Optional
from models import User, Group
from dependencies import get_token_header
import uuid
from datetime import datetime
from exceptions import username_already_exists
import time


router = APIRouter(
    prefix="/user-service/v1",
    tags=["UserManagementAPIs"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

#@todo - Unit test, sending confirmation email
@router.post("/users")
def create(details: CreateUser, commons: dict = Depends(common_params), db: Session = Depends(get_db)):
    #generate token
    otp = get_secret_random()
    user_id = details.id or uuid.uuid4().hex
    #Set user entity
    user = User(
        id=user_id,
        email=details.email,
        name=details.name,
        role_id=details.role,        
        secret=get_secret_random(10)
    )

    #Set user groups
    for group in details.groups:
        group_entity = db.query(Group).get(group)
        user.groups.append(group_entity)

    #Set token entity
    token = OnetimeToken(
        id=uuid.uuid4().hex,
        otp=otp,
        created_at=datetime.now(),
        user_id=user_id,
        active=1
    )    

    #commiting data to db
    try:
        db.add(user)
        db.add(token)
        db.commit()
    except IntegrityError as err:
        db.rollback()
        raise HTTPException(status_code=422, detail=username_already_exists)
    return {
        "success": True,
        "tokenTMPShow":otp
    }

#@todo - Unit test
@router.get("/users")
def get_by_filter(commons: dict = Depends(common_params), db: Session = Depends(get_db), id: Optional[str] = None, group: Optional[str] = None, role: Optional[str] = None):
    filters = {}

    if(id):
        filters['id'] = id
    if(group):
        filters['id'] = group
    if(role):
        filters['role_id'] = role

    return db.query(User).join(User.groups).filter_by(**filters).all()

#@todo - Unit test
@router.delete("/users/{id}")
def delete_by_id(id: str, commons: dict = Depends(common_params), db: Session = Depends(get_db)):
    user = db.query(User).get(id)
    db.delete(user)
    db.commit()





@router.get("/users/{id}/generate-secret/{confirmation}")
def generate_qr(db: Session = Depends(get_db), token = Depends(get_token_header)):
    user = db.query(User).get(token)
    user_secret = user.secret
    qr = qrcode.make("otpauth://totp/SecOps:OTP?secret={}&issuer=SecOpsRobot".format(user_secret))
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    image = base64.b64encode(buffer.getvalue()).decode()
    
    return image