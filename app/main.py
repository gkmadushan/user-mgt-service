from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from routers import users, auth, groups, roles
from fastapi.security import OAuth2PasswordBearer

app = FastAPI(debug=True)

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
]

#middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#user routes
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(groups.router)
app.include_router(roles.router)