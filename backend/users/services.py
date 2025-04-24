from passlib.context import CryptContext
from backend.database import db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        return {"Error": str(e)}

def user_has_credits(username: str) -> bool:
    try:
        user = db.table("users").select("*").eq("username", username).execute()
        user_credits = user.data[0]["credits"]

        return user_credits > 0 
    except Exception as e:
        return {"Error": str(e)}
    
def user_is_admin(username: str) -> bool:
    try:
        user = db.table("users").select("*").eq("username", username).execute()
        is_admin = user.data[0]["is_admin"]

        return is_admin
    
    except Exception as e:
        return {"Error": str(e)}

def decrease_credits_for_free_users(username: str):
    try:
        user = db.table("users").select("*").eq("username", username).execute()
        user_credits = user.data[0]["credits"]

        db.table("users").update({"credits": user_credits - 1}).eq("username", username).execute()
        
    except Exception as e:
        return {"Error": str(e)}