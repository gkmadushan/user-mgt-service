from sqlalchemy.sql.sqltypes import DateTime
from sqlalchemy.exc import IntegrityError
from starlette.responses import Response
from models import OnetimeToken
from fastapi import APIRouter, Depends, HTTPException, Request
from dependencies import common_params, get_db, get_secret_random, send_email
from schemas import CreateUser, UpdateUser
from sqlalchemy.orm import Session
from typing import Optional
from models import User, Group, Role
from dependencies import get_token_header
import uuid
from datetime import datetime
from exceptions import username_already_exists
from sqlalchemy import over
from sqlalchemy import engine_from_config, and_, func, case
from sqlalchemy_filters import apply_pagination
import time
import os
import uuid
import base64
import pyotp

page_size = os.getenv('PAGE_SIZE')
BASE_URL = "http://localhost:8089"

router = APIRouter(
    prefix="/v1",
    tags=["UserManagementAPIs"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

# @todo - Unit test, sending confirmation email


@router.post("/users")
def create(details: CreateUser, commons: dict = Depends(common_params), db: Session = Depends(get_db)):
    # generate token
    otp = get_secret_random()
    user_id = details.id or uuid.uuid4().hex
    # Set user entity
    user = User(
        id=user_id,
        email=details.email,
        name=details.name,
        role_id=details.role,
        secret=pyotp.random_base32()
    )

    # Set user groups
    if details.groups != []:
        for group in details.groups:
            group_entity = db.query(Group).get(group)
            user.groups.append(group_entity)

    # Set token entity
    token = OnetimeToken(
        id=uuid.uuid4().hex,
        otp=otp,
        created_at=datetime.now(),
        user_id=user_id,
        active=1
    )

    # commiting data to db
    try:
        db.add(user)
        db.add(token)
        db.commit()
    except IntegrityError as err:
        db.rollback()
        raise HTTPException(status_code=422, detail=username_already_exists)

    # Sending the confirmation link
    recipient = details.email
    # Test address
    recipient = 'gkmadushan@gmail.com'
    msg = """
    Hi\n
    Please confirm you email by navigating your browser to below URL\n
    {}/users/confirm?user={}&token={}\n
    Thank you\n
    SecOps
    """.format(BASE_URL, user_id, otp)

    html = """
    Hi<br/>
    Please confirm you email by navigating your browser to below URL<br/>
    <a href="{}/users/confirm?user={}&token={}">Confirm</a><br/>
    Thank you<br/>
    SecOps
    """.format(BASE_URL, user_id, otp)
    send_email(recipient, 'SecOps - Registration Confirmation Email', msg=msg, html=html)

    return {
        "success": True,
    }

# @todo - Unit test


@router.get("/users")
def get_by_filter(page: Optional[str] = 1, limit: Optional[int] = page_size, commons: dict = Depends(common_params), db: Session = Depends(get_db), id: Optional[str] = None, group: Optional[str] = None, role: Optional[str] = None, email: Optional[str] = None, role_code: Optional[str] = None):
    filters = []

    if(role):
        filters.append(User.role_id == role)

    if(group):
        filters.append(Group.id == group)

    if(role_code):
        filters.append(Role.code == role_code)

    if(email):
        filters.append(User.email.ilike(email+'%'))
    else:
        filters.append(User.email.ilike('%'))

    query = db.query(
        over(func.dense_rank(), order_by="email").label('index'),
        User.id,
        User.email,
        Role.name.label('role'),
        User.name,
        case((User.active == 1, 'Yes'), (User.active == 0, 'No')).label('active'),
        func.to_char(User.created_at, 'DD/MM/YYYY HH12:MI PM').label('created_at'),
    )

    query, pagination = apply_pagination(query.distinct(User.email).join(User.groups).join(
        User.role).where(and_(*filters)).order_by(User.email.asc()), page_number=int(page), page_size=int(limit))

    response = {
        "data": query.all(),
        "meta": {
            "total_records": pagination.total_results,
            "limit": pagination.page_size,
            "num_pages": pagination.num_pages,
            "current_page": pagination.page_number
        }
    }

    return response

# @todo - Unit test


@router.delete("/users/{id}")
def delete_by_id(id: str, commons: dict = Depends(common_params), db: Session = Depends(get_db)):
    user = db.query(User).get(id.strip())
    db.delete(user)
    db.commit()
    return Response(status_code=204)


# get user by id
@router.get("/users/{id}")
def get_by_id(id: str, commons: dict = Depends(common_params), db: Session = Depends(get_db)):
    user = db.query(User).get(id.strip())
    if user == None:
        raise HTTPException(status_code=404, detail="Item not found")
    user.groups = user.groups
    response = {
        "data": user
    }
    return response


# @router.get("/users/{id}/generate-secret/{confirmation}")
# def generate_qr(db: Session = Depends(get_db), token = Depends(get_token_header)):
#     user = db.query(User).get(token)
#     user_secret = user.secret
#     qr = qrcode.make("otpauth://totp/SecOps:OTP?secret={}&issuer=SecOpsRobot".format(user_secret))
#     buffer = BytesIO()
#     qr.save(buffer, format="PNG")
#     image = base64.b64encode(buffer.getvalue()).decode()

#     return image


@router.put("/users/{id}")
def update(id: str, details: UpdateUser, commons: dict = Depends(common_params), db: Session = Depends(get_db)):
    # Set user entity
    user = db.query(User).get(id)

    user.name = details.name
    if user.role_id != details.role:
        user.role_id = details.role

    # Set user groups
    if user.groups != []:
        user.groups = []

    if details.groups != []:
        for group in details.groups:
            group_entity = db.query(Group).get(group)
            user.groups.append(group_entity)

    # commiting data to db
    try:
        db.add(user)
        db.commit()
    except IntegrityError as err:
        db.rollback()
        raise HTTPException(status_code=422, detail=username_already_exists)
    return {
        "success": True
    }

# @todo - Unit test, sending confirmation email


@router.post("/users/{id}/reset-password")
def send_recovery_email(id: str, commons: dict = Depends(common_params), db: Session = Depends(get_db)):
    user = db.query(User).get(id)
    otp = get_secret_random()

    # Set token entity
    token = OnetimeToken(
        id=uuid.uuid4().hex,
        otp=otp,
        created_at=datetime.now(),
        user_id=id,
        active=1
    )

    # commiting data to db
    try:
        db.add(token)
        db.commit()
    except IntegrityError as err:
        db.rollback()
        raise HTTPException(status_code=422, detail="Unable to store token")

    # Sending the confirmation link
    recipient = user.email
    # Test address
    recipient = 'gkmadushan@gmail.com'
    msg = """
    Hi\n
    Please click the below link to reset the password\n
    {}/users/confirm?user={}&token={}\n
    Thank you\n
    SecOps
    """.format(BASE_URL, id, otp)

    html = """
    Hi<br/>
    Please click the below link to reset the password<br/>
    <a href="{}/users/confirm?user={}&token={}">Confirm</a><br/>
    Thank you<br/>
    SecOps
    """.format(BASE_URL, id, otp)
    send_email(recipient, 'SecOps - Password Recovery', msg=msg, html=html)

    return {
        "success": True,
    }
