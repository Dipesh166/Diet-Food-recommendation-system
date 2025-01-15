from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
from model import recommend, output_recommended_recipes

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import bcrypt
import jwt
import datetime
from pymongo import MongoClient




# Reading the dataset
dataset = pd.read_csv('../data/last_20000_rows.csv')
 
app = FastAPI()

# Define Params model to capture recommendation parameters
class Params(BaseModel):
    n_neighbors: int = 5
    return_distance: bool = False

# Input data model for prediction
class PredictionIn(BaseModel):
    nutrition_input: List[float]
    ingredients: Optional[str] = None  # Ingredients input as an optional semicolon-separated string
    params: Optional[Params] = Params()  # Include Params for recommendations, using default if not provided

# Recipe output model
class Recipe(BaseModel):
    Name: str
    CookTime: str
    PrepTime: str
    TotalTime: str
    RecipeIngredientParts: List[str]
    Calories: float
    FatContent: float
    SaturatedFatContent: float
    CholesterolContent: float
    SodiumContent: float
    CarbohydrateContent: float
    FiberContent: float
    SugarContent: float
    ProteinContent: float
    RecipeInstructions: List[str]

# Output model for prediction response
class PredictionOut(BaseModel):
    output: Optional[List[Recipe]] = None

# Root endpoint for health check
@app.get("/")
def home():
    return {"health_check": "OK"}

# Prediction endpoint
@app.post("/predict/", response_model=PredictionOut)
def update_item(prediction_input: PredictionIn):
    # Manual validation of the nutrition_input length
    if len(prediction_input.nutrition_input) != 9:
        raise HTTPException(status_code=422, detail="nutrition_input must have exactly 9 items.")
    
    # Ensure params are passed correctly or use defaults
    params = prediction_input.params.dict() if prediction_input.params else {}
    
    # Split ingredients string by ";" if ingredients are provided and strip spaces
    ingredients = [ingredient.strip() for ingredient in prediction_input.ingredients.split(";")] if prediction_input.ingredients else []
    
    # Call the recommend function with nutrition input and ingredients
    recommendation_dataframe = recommend(
        dataset, prediction_input.nutrition_input, ingredients, params
    )
    
    # Call the function to process the dataframe and output recommended recipes
    output = output_recommended_recipes(recommendation_dataframe)
    
    # Return the recommended recipes as output, fallback to empty list if no recommendations
    return {"output": output if output is not None else []}






#login

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
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
db = client["diet_food_app"]

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Models
class UserSignup(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Helper to hash passwords
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Helper to verify passwords
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# Helper to create access tokens
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Helper to decode tokens
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

# Routes
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
    }
    await db.users.insert_one(user_data)
    return {"message": "Account created successfully!"}

@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db.users.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user["email"]}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/profile")
async def read_profile(current_user: dict = Depends(get_current_user)):
    return {"email": current_user["email"], "username": current_user["username"]}
