from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response, Cookie
from fastapi.param_functions import Form
from models import User, OnetimeToken
from schemas import ConfirmUser
from dependencies import get_db, hash, validate_token, generate_token, get_secret_random
from sqlalchemy.orm import Session
import pyotp
import qrcode
from io import BytesIO
import base64

router = APIRouter(
    tags=["TokenAPIs"],
    responses={404: {"description": "Not found"}},
)

@router.post("/oauth/token")
async def login(username = Form(...), password = Form(...), otp : Optional[str] = Form(None), db: Session = Depends(get_db), response: Response = None):
    access_token = None
    refresh_token = None
    hashed_password = hash(password)
    #KasunNote: checking the username and password both in the database query is safer than checking them seperately
    #KasunNote: why? because of if someone is estimating the time then they can use timing to detect the user exists scenario
    user = db.query(User).filter(User.email == username).filter(User.password == hashed_password).first()

    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    else:
        if user.secret == None or pyotp.TOTP(user.secret).now() == otp:
            access_token = generate_token(user.id)
            refresh_token = generate_token(user.id, 180)
        else:
            raise HTTPException(status_code=400, detail="Invalid OTP")

    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=True)
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/oauth/refresh-token")
async def refresh_token(refresh_token: Optional[str] = Cookie(None), db: Session = Depends(get_db), response: Response = None):
    user_id = validate_token(refresh_token)
    if user_id == False:
        raise HTTPException(status_code=400, detail="Refresh token invalid or expired")
    else:
        access_token = generate_token(user_id)
        response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=True)
        return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/{id}/verify/{token}")
def confirm(id: str, token, db: Session = Depends(get_db)):
    filters = {}
    filters['user_id'] = id
    filters['otp'] = token
    filters['active'] = 1
    try:
        valid_token_count = db.query(OnetimeToken).filter_by(**filters).count()
        if valid_token_count > 0:
            user = db.query(User).get(id)      
            
            qr = qrcode.make("otpauth://totp/SecOps:OTP?secret={}&issuer=SecOpsRobot".format(user.secret))
            buffer = BytesIO()
            qr.save(buffer, format="PNG")
            image = base64.b64encode(buffer.getvalue()).decode()
            return image
        else:
            raise HTTPException(status_code=500, detail="Invalid User ID or Token") 
    except:
        raise HTTPException(status_code=500, detail="Invalid User ID or Token")
    

@router.patch("/users/{id}/verify/{token}")
def confirm(id: str, token, details: ConfirmUser,  db: Session = Depends(get_db)):
    filters = {}
    filters['user_id'] = id
    filters['otp'] = token
    filters['active'] = 1
    try:
        valid_token_count = db.query(OnetimeToken).filter_by(**filters).count()
        if valid_token_count >= 0:
            user = db.query(User).get(id)    
            if (pyotp.TOTP(user.secret).now() == details.otp):
                active_token = db.query(OnetimeToken).filter_by(**filters)[0]
                user.active = 1
                user.password = hash(details.password)
                active_token.active = 0
                # db.add(user)
                # db.add(active_token)
                db.commit()
                return {"user_id":user.id}
            else:
                raise HTTPException(status_code=500, detail="Invalid OTP"+pyotp.TOTP(user.secret).now())
    except:
        raise HTTPException(status_code=500, detail="Invalid OTP"+pyotp.TOTP(user.secret).now())
    