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
ICON = """<img src="iVBORw0KGgoAAAANSUhEUgAAAJYAAAAvCAYAAAABxDNfAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJ
bWFnZVJlYWR5ccllPAAAA3NpVFh0WE1MOmNvbS5hZG9iZS54bXAAAAAAADw/eHBhY2tldCBiZWdp
bj0i77u/IiBpZD0iVzVNME1wQ2VoaUh6cmVTek5UY3prYzlkIj8+IDx4OnhtcG1ldGEgeG1sbnM6
eD0iYWRvYmU6bnM6bWV0YS8iIHg6eG1wdGs9IkFkb2JlIFhNUCBDb3JlIDYuMC1jMDAyIDc5LjE2
NDQ4OCwgMjAyMC8wNy8xMC0yMjowNjo1MyAgICAgICAgIj4gPHJkZjpSREYgeG1sbnM6cmRmPSJo
dHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4gPHJkZjpEZXNjcmlw
dGlvbiByZGY6YWJvdXQ9IiIgeG1sbnM6eG1wTU09Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEu
MC9tbS8iIHhtbG5zOnN0UmVmPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvc1R5cGUvUmVz
b3VyY2VSZWYjIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtcE1N
Ok9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDo0NjNjZGNjNy05YmQ4LThlNDctYWQ0MS0wYTE4
MTE2ZWIwY2EiIHhtcE1NOkRvY3VtZW50SUQ9InhtcC5kaWQ6MzkwNzcxQ0I2NzFFMTFFQzkyQUNG
NTlDMDVDNjYwOTUiIHhtcE1NOkluc3RhbmNlSUQ9InhtcC5paWQ6MzkwNzcxQ0E2NzFFMTFFQzky
QUNGNTlDMDVDNjYwOTUiIHhtcDpDcmVhdG9yVG9vbD0iQWRvYmUgUGhvdG9zaG9wIDIyLjAgKFdp
bmRvd3MpIj4gPHhtcE1NOkRlcml2ZWRGcm9tIHN0UmVmOmluc3RhbmNlSUQ9InhtcC5paWQ6NTQx
MjQ3NDgtYzhiYS1hNDRiLWFhZDEtMjcwZTcwNmM2MzQ3IiBzdFJlZjpkb2N1bWVudElEPSJ4bXAu
ZGlkOjQ2M2NkY2M3LTliZDgtOGU0Ny1hZDQxLTBhMTgxMTZlYjBjYSIvPiA8L3JkZjpEZXNjcmlw
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"/>
"""

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
    Hi {}\n
    You are Invited to join SecOps - Automated Vulnerability Management System.\n
    Please click the link below to confirm your email address and configure password and OTP\n
    {}/users/confirm?user={}&token={}\n\n
    Thank you\n\n
    SecOps
    """.format(details.name, BASE_URL, user_id, otp)

    html = """
    Hi {}<br/><br/>
    You are Invited to join SecOps - Automated Vulnerability Management System.<br/>
    Please click the link below to confirm your email address and configure password and OTP<br/><br/>
    <a href="{}/users/confirm?user={}&token={}">Click here to confirm</a><br/><br/>
    Thank you<br/>
    SecOps<br/>    
    {}
    """.format(details.name, BASE_URL, user_id, otp, ICON)
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
