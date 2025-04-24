import os
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from .models import CreateUser
from backend.database import db
from backend.users.services import hash_password, verify_password
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from dotenv import load_dotenv



load_dotenv()

SECRET_KEY=os.getenv("SECRET_KEY")
ALGORITHM=os.getenv("ALGORITHM")

users_router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@users_router.post("/signup", tags=["Authentication"])
async def signup(user: CreateUser):
    
    try:
        # check if user already exists

        existing_user = db.table("users").select("*").eq("username", user.username).execute()

        if existing_user.data:
            raise HTTPException(status_code=400, detail="User already exists")
        
        hashed_password = hash_password(user.password)

        db.table("users").insert({
            "username": user.username,
            "password": hashed_password,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }).execute()

        return {"message": "User created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@users_router.post("/token", include_in_schema=False)
async def login(login_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    existing_user = db.table("users").select("*").eq("username", login_data.username).execute() 

    if not existing_user.data:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    hashed_password = existing_user.data[0]["password"]

    if not verify_password(login_data.password, hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    username = existing_user.data[0]["username"]
    user_id = existing_user.data[0]["id"]

    # create JWT token

    token = create_access_token(username, user_id, timedelta(minutes=20))
    
    return {"access_token": token, "token_type": "bearer"}


def create_access_token(username, user_id, expires_delta):
    encode = {"sub": username, "id": user_id}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        return {"username": username, "id": user_id}
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    
    


