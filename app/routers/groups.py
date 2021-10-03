from sqlalchemy.sql.sqltypes import DateTime
from sqlalchemy.exc import IntegrityError
from starlette.responses import Response
from models import OnetimeToken
from fastapi import APIRouter, Depends, HTTPException, Request
from dependencies import common_params, get_db, get_secret_random
from schemas import CreateUser
from sqlalchemy.orm import Session
from typing import Optional
from models import User, Group, Role
from dependencies import get_token_header
import uuid
from datetime import datetime
from exceptions import username_already_exists
from sqlalchemy import over
from sqlalchemy import engine_from_config, and_, func
from sqlalchemy_filters import apply_pagination
import time
import os
import uuid

page_size = os.getenv('PAGE_SIZE')


router = APIRouter(
    prefix="/user-service/v1",
    tags=["GroupManagementAPIs"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

#@todo - Unit test, sending confirmation email
@router.post("/groups")
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
    if details.groups != []:
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
@router.get("/groups")
def get_by_filter(page: Optional[str] = 1, limit: Optional[int] = page_size, commons: dict = Depends(common_params), db: Session = Depends(get_db), id: Optional[str] = None, group: Optional[str] = None):
    filters = {}

    if(id):
        filters['id'] = id
    if(group):
        filters['name'] = group

    query = db.query(
        over(func.row_number(), order_by='name').label('index'),
        Group.id,        
        Group.name,
        Group.description
    )

    query, pagination = apply_pagination(query.filter_by(**filters), page_number = int(page), page_size = int(limit))

    response = {
        "data": query.all(),
        "meta":{
            "totalRecords": pagination.total_results,
            "limit": pagination.page_size,
            "num_pages": pagination.num_pages,
            "current_page": pagination.page_number
        }
    }

    return response

#@todo - Unit test
@router.delete("/groups/{id}")
def delete_by_id(id: str, commons: dict = Depends(common_params), db: Session = Depends(get_db)):
    user = db.query(User).get(id.strip())
    db.delete(user)
    db.commit()
    return Response(status_code=204)


