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
from fastapi.responses import JSONResponse



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




