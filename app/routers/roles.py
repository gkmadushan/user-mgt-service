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
    tags=["RoleManagementAPIs"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

#@todo - Unit test
@router.get("/roles")
def get_by_filter(page: Optional[str] = 1, limit: Optional[int] = page_size, commons: dict = Depends(common_params), db: Session = Depends(get_db), id: Optional[str] = None, group: Optional[str] = None):
    filters = {}

    if(id):
        filters['id'] = id
    if(group):
        filters['name'] = group

    query = db.query(
        over(func.row_number(), order_by='name').label('index'),
        Role.id,        
        Role.name,
        Role.code
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

