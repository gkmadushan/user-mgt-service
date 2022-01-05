from sqlalchemy.sql.sqltypes import DateTime
from sqlalchemy.exc import IntegrityError
from starlette.responses import Response
from models import OnetimeToken
from fastapi import APIRouter, Depends, HTTPException, Request
from dependencies import common_params, get_db, get_secret_random
from schemas import UpdateGroup, CreateGroup
from sqlalchemy.orm import Session
from typing import Optional
from models import User, Group, Role
from dependencies import get_token_header
import uuid
from datetime import datetime
from exceptions import username_already_exists
from sqlalchemy import over
from sqlalchemy import engine_from_config, and_, func, literal_column
from sqlalchemy_filters import apply_pagination
import time
import os
import uuid

page_size = os.getenv('PAGE_SIZE')


router = APIRouter(
    prefix="/v1",
    tags=["GroupManagementAPIs"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.post("/groups")
def create(details: CreateGroup, commons: dict = Depends(common_params), db: Session = Depends(get_db)):
    # generate token
    id = details.id or uuid.uuid4().hex
    # Set user entity
    group = Group(
        id=id,
        name=details.name,
        description=details.description
    )

    # commiting data to db
    try:
        db.add(group)
        db.commit()
    except IntegrityError as err:
        db.rollback()
        raise HTTPException(status_code=422, detail=username_already_exists)
    return {
        "success": True
    }


@router.get("/groups")
def get_by_filter(page: Optional[str] = 1, limit: Optional[int] = page_size, commons: dict = Depends(common_params), db: Session = Depends(get_db), id: Optional[str] = None, group: Optional[str] = None):
    filters = []

    if(group):
        filters.append(Group.name.ilike(group+'%'))
    else:
        filters.append(Group.name.ilike('%'))

    count_users_stmt = literal_column(
        '(SELECT count(*) FROM user_group ug WHERE ug.group_id = "group".id)').label('num_users')

    query = db.query(
        over(func.row_number(), order_by='name').label('index'),
        Group.id,
        Group.name,
        count_users_stmt,
        Group.description
    )

    query, pagination = apply_pagination(query.where(
        and_(*filters)).order_by(Group.name.asc()), page_number=int(page), page_size=int(limit))

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


@router.delete("/groups/{id}")
def delete_by_id(id: str, commons: dict = Depends(common_params), db: Session = Depends(get_db)):
    group = db.query(Group).get(id.strip())
    db.delete(group)
    db.commit()
    return Response(status_code=204)


# get user by id
@router.get("/groups/{id}")
def get_by_id(id: str, commons: dict = Depends(common_params), db: Session = Depends(get_db)):
    group = db.query(Group).get(id.strip())
    if group == None:
        raise HTTPException(status_code=404, detail="Item not found")
    response = {
        "data": group
    }
    return response


@router.put("/groups/{id}")
def update(id: str, details: UpdateGroup, commons: dict = Depends(common_params), db: Session = Depends(get_db)):
    # Set user entity
    group = db.query(Group).get(id)

    group.name = details.name
    group.description = details.description

    # commiting data to db
    try:
        db.add(group)
        db.commit()
    except IntegrityError as err:
        db.rollback()
        raise HTTPException(status_code=422, detail=username_already_exists)
    return {
        "success": True
    }
