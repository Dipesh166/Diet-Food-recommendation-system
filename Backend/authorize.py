from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import bcrypt
import jwt
import datetime
from pymongo import MongoClient
from fastapi.responses import JSONResponse

# MongoDB client
client = MongoClient("mongodb://localhost:27017/RecommendationUsers")

# Test the connection to MongoDB
try:
    # Attempt to ping the database
    client.admin.command('ping')
    db_connection_status = "Connected to MongoDB"
except Exception as e:
    db_connection_status = f"Failed to connect to MongoDB: {e}"

db = client["diet_recommendation"]
users_collection = db["users"]

# FastAPI app
app = FastAPI()

# JWT secret key
SECRET_KEY = "mysecretkey"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Helper functions for authentication
def hash_password(password: str):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

def verify_password(stored_password: str, provided_password: str):
    return bcrypt.checkpw(provided_password.encode("utf-8"), stored_password)

def create_access_token(data: dict):
    expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    to_encode = data.copy()
    to_encode.update({"exp": expiration})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

# Pydantic models
class User(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

@app.get("/")
async def root():
    return {"message": db_connection_status}

@app.post("/signup")
async def signup(user: User):
    if users_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="User already exists")
    hashed_password = hash_password(user.password)
    users_collection.insert_one({"username": user.username, "password": hashed_password})
    return {"msg": "User created successfully"}

@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_collection.find_one({"username": form_data.username})
    if not user or not verify_password(user["password"], form_data.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token(data={"sub": form_data.username})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/protected")
async def protected(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return {"msg": f"Welcome, {payload['sub']}!"}
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@app.get("/signup")
def signup():
    print("Getting data")