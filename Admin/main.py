

#login

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, validator
from enum import Enum
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from jose import JWTError, jwt
import bcrypt
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
SECRET_KEY = os.getenv("SECRET_KEY", "mysecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Initialize FastAPI app and MongoDB client
app = FastAPI()
client = AsyncIOMotorClient(MONGO_URI)
db = client["diet_food_app_admin"]

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Enum to define valid roles
class UserRole(str, Enum):
    user = "user"
    admin = "admin"

# Models
class UserSignup(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: UserRole = UserRole.user  # Default role is 'user'

    @validator("role")
    def validate_role(cls, v):
        if v not in UserRole.__members__.values():
            raise ValueError("Role must be 'user' or 'admin'")
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Helper functions to hash and verify passwords
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# Helper function to create access token
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Helper function to decode token
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        user = await db.users.find_one({"email": email})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# Function to check if user is admin
async def is_admin(user: dict):
    return user.get("role") == "admin"

# Signup Endpoint
@app.post("/signup")
async def signup(user: UserSignup):
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists.")
    
    hashed_password = hash_password(user.password)
    user_data = {
        "email": user.email,
        "username": user.username,
        "password": hashed_password,
        "role": user.role,  # Store the role in the database
    }
    await db.users.insert_one(user_data)
    return {"message": "Account created successfully!"}

# Login Endpoint
@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db.users.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user["email"]}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}

# Current User Profile Endpoint
@app.get("/profile")
async def read_profile(current_user: dict = Depends(get_current_user)):
    return {
        "email": current_user["email"],
        "username": current_user["username"],
        "role": current_user.get("role"),
    }




from bson import ObjectId
from fastapi.encoders import jsonable_encoder

# Function to convert ObjectId to string in the response
def user_to_dict(user):
    user["_id"] = str(user["_id"])  # Convert ObjectId to string
    return user

@app.get("/admin/data")
async def get_all_users(current_user: dict = Depends(get_current_user)):
    if not await is_admin(current_user):
        raise HTTPException(status_code=403, detail="Access denied. Admins only.")
    
    users_cursor = db.users.find()  # Retrieve all users
    users = await users_cursor.to_list(None)
    
    # Convert all users' ObjectId to string
    users = [user_to_dict(user) for user in users]
    
    return users


# 5. Update User's Role (admin only)
@app.put("/admin/update_role/{user_id}")
async def update_user_role(user_id: str, role: UserRole, current_user: dict = Depends(get_current_user)):
    if not await is_admin(current_user):
        raise HTTPException(status_code=403, detail="Access denied. Admins only.")
    
    result = await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"role": role}}
    )
    if result.modified_count == 1:
        return {"message": "User role updated successfully"}
    else:
        raise HTTPException(status_code=404, detail="User not found")

# 6. Delete User (admin only)
@app.delete("/admin/delete_user/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    if not await is_admin(current_user):
        raise HTTPException(status_code=403, detail="Access denied. Admins only.")
    
    result = await db.users.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 1:
        return {"message": "User deleted successfully."}
    else:
        raise HTTPException(status_code=404, detail="User not found")

