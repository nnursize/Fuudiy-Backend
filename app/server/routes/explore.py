
import re
from spark_utils import spark
from pyspark.sql import functions as F
from pyspark.sql import Row 
from pyspark.sql.types import ArrayType
from pyspark.ml.feature import IDF
from pyspark.ml.feature import CountVectorizer
from pyspark.ml import Pipeline
from pyspark.sql.types import ArrayType, DoubleType
from pyspark.ml.functions import vector_to_array
from config import MONGO_URI, DATABASE_NAME, COLLECTION_FOOD, COLLECTION_SURVEY, COLLECTION_USER_COMMENTS
from fastapi import APIRouter, HTTPException, Depends, Query
from ..services.auth_service import get_current_user
import traceback
from collections import defaultdict

router = APIRouter()

DISH_INGREDIENT_MAP = {
    "vegetarian_dishes": ["lettuce", "tomato"],
    "meat_dishes": ["meat"],
    "seafood": ["seafood", "crab", "fish"],
    "pastries_and_bread": ["flour", "yeast"],
    "sweets_and_confectionery": ["sugar", "chocolate"],
    "sushi": ["rice", "seafood", "nori"],
    "pizza": ["cheese", "tomato", "flour"],
    "dumpling": ["flour", "meat", "vegetables"],
    "hamburger": ["meat", "lettuce", "tomato", "bread"],
    "fried_chicken": ["chicken", "flour", "spices"],
    "taco": ["tortilla", "meat", "lettuce", "tomato"],
    "pasta": ["pasta", "tomato", "cheese"]
}

RATING_ADJUSTMENTS = {
    5: 2.0,
    4: 1.0,
    3: 0.0,
    2: -1.0,
    1: -2.0
}

def load_food_data(spark, collection_name):
    """Secure data loading with proper environment variables"""
    return spark.read.format("mongodb") \
        .option("uri", MONGO_URI) \
        .option("database", DATABASE_NAME) \
        .option("collection", collection_name) \
        .load()


survey_df = load_food_data(spark, COLLECTION_SURVEY).cache()

food_df = (
    load_food_data(spark, COLLECTION_FOOD)
    .select("_id", "country", "ingredients", "name", "url_id")
    .withColumn(
        "ingredients",
        F.array_distinct(
            F.transform(
                F.split(F.col("ingredients"), "\s*,\s*"),
                lambda x: F.regexp_replace(F.lower(F.trim(x)), r's$', '')
            )
        )
    )
    .filter(F.size(F.col("ingredients")) > 0)
)

def get_user_preferences(user_id):
    survey = survey_df.filter(F.col("user_id") == user_id).first()
    if not survey:
        raise HTTPException(400, "Survey missing")
    
    prefs = survey.asDict().get("responses", {})
    return prefs.asDict() if isinstance(prefs, Row) else prefs

def parse_prefs(value):
        if isinstance(value, str):
            return [x.strip().lower() for x in value.split(",")]
        return value if isinstance(value, list) else []

def clean_ingredients(df):
    return df.withColumn(
        "clean_ingredients",
        F.expr("""transform(
            ingredients,
            x -> regexp_replace(
                lower(trim(regexp_replace(x, "'|\\\\[|\\\\]", ""))), 
                's$', ''
            )
        )""")
    )

def filter_disliked_allergies(df, disliked, allergies=None):
    # Combine disliked ingredients and allergies
    all_exclusions = set(disliked)
    if allergies:
        all_exclusions.update(allergies)
    
    if not all_exclusions:
        return df
    
    # Clean combined exclusions
    clean_exclusions = [
        re.sub(r's$', '', ing.strip().lower())
        for ing in all_exclusions
        if ing.strip() and ing.strip() != 'on'
    ]
    
    # Single cleaning and filtering operation
    return clean_ingredients(df).filter(
        F.size(F.array_intersect(
            F.col("clean_ingredients"),
            F.array([F.lit(ing) for ing in clean_exclusions])
        )) == 0
    )

def calculate_ingredient_adjustments(prefs):
    adjustments = defaultdict(float)
    
    # Handle different food_prefs formats
    food_prefs = prefs.get("food_preferences", {})
    
    # Convert list format to dict if needed
    if isinstance(food_prefs, list):
        # Convert from [{key: "pizza", value: "loves"}, ...] format
        food_prefs = {item["key"]: item["value"] for item in food_prefs}
    elif isinstance(food_prefs, Row):
        food_prefs = food_prefs.asDict()
    
    for dish, ingredients in DISH_INGREDIENT_MAP.items():
        # Get rating from both root and food_prefs
        raw_rating = prefs.get(dish) or food_prefs.get(dish)
        
        # Default to neutral if no rating
        numerical_rating = 3
        
        if raw_rating:
            # Handle numeric values
            if isinstance(raw_rating, (int, float)):
                numerical_rating = max(1, min(int(raw_rating), 5))
            # Handle string values
            elif isinstance(raw_rating, str):
                clean_rating = raw_rating.strip().lower()
                numerical_rating = {
                    "loves": 5, 
                    "likes": 3, 
                    "neutral": 3,
                    "dislikes": 1
                }.get(clean_rating, 3)  # Default to 3 if unknown string

        adj = RATING_ADJUSTMENTS.get(numerical_rating, 0.0)
        for ingredient in ingredients:
            adjustments[ingredient] += adj
            
    return adjustments

# 3. TF-IDF Pipeline
tfidf_pipeline = Pipeline(stages=[
    CountVectorizer(inputCol="ingredients", outputCol="rawFeatures", vocabSize=10000),
    IDF(inputCol="rawFeatures", outputCol="features")
]).fit(food_df)
food_df = tfidf_pipeline.transform(food_df).cache()

vector_to_array = F.udf(lambda v: v.toArray().tolist(), ArrayType(DoubleType()))

# ---------- Recommendation Endpoint ----------
@router.get("/recommend/")
async def recommend_foods(country: str = Query(..., title="Target country"), user_id: str = Depends(get_current_user), top_n: int = 10):
    print(f"Received country: {country}, user_id: {user_id}")  # Debugging
    try:
        # 2. Validate user survey
        prefs = get_user_preferences(user_id)
        if isinstance(prefs, Row):  # If responses is stored as Row
            prefs = prefs.asDict()

        """
        liked = set(parse_prefs(prefs.get("liked_ingredients")))
        print("Liked:  ",liked)
        disliked = set(parse_prefs(prefs.get("disliked_ingredients"))) | \
                set(parse_prefs(prefs.get("allergies")))
        print("DisLiked:  ",disliked)
        """

        ingredient_adjustments = calculate_ingredient_adjustments(prefs)

        # Process user comments to adjust ingredient scores based on their ratings
        user_comments_df = load_food_data(spark, COLLECTION_USER_COMMENTS).cache()
        user_comments_filtered = user_comments_df.filter(F.col("userId") == user_id)

        # Join with food_df to get ingredients for each commented food
        commented_foods = user_comments_filtered.join(
            food_df.select("_id", "ingredients"),
            user_comments_filtered.foodId == food_df._id,
            "inner"
        ).select("rate", "ingredients")

        # Collect the data to the driver to process adjustments
        commented_foods_data = commented_foods.collect()

        # Calculate adjustments from user comments
        for row in commented_foods_data:
            rate = row['rate']
            ingredients = row['ingredients']
            rate_val = float(rate) if rate is not None else 3.0
            # Scale adjustment to match survey's impact (rate - 3) * 1.0
            adjustment = (rate_val - 3) * 1.0
            for ingredient in ingredients:
                ingredient_adjustments[ingredient] += adjustment

        # Broadcast the combined adjustments (survey + user comments)
        bc_adjustments = spark.sparkContext.broadcast(ingredient_adjustments)
        calculate_adjustment_udf = F.udf(
            lambda ingredients: float(sum(
                bc_adjustments.value.get(ing, 0.0) for ing in ingredients
            )),
            DoubleType()
        )
    
        country_foods = filter_disliked_allergies(
            food_df.filter(F.col("country") == country), 
            disliked=parse_prefs(prefs.get("disliked_ingredients")),
            allergies=parse_prefs(prefs.get("allergies"))
        ).withColumn("score", 
            F.aggregate(
                vector_to_array("features"), 
                F.lit(0.0), 
                lambda acc, x: acc + x
            ) + calculate_adjustment_udf(F.col("ingredients"))
        )

        # 5. Calculate TF-IDF scores and adjustment scores
        country_foods = country_foods.withColumn(
            "tfidf_array", 
            vector_to_array("features")
        )

        # Calculate TF-IDF sum
        score_expr = """
            aggregate(
                tfidf_array,
                CAST(0.0 AS DOUBLE),
                (acc, x) -> acc + x
            )
        """
        country_foods = country_foods.withColumn("tfidf_sum", F.expr(score_expr))

        # Calculate adjustment score
        country_foods = country_foods.withColumn(
            "adjustment_score", 
            calculate_adjustment_udf(F.col("ingredients"))
        )

        # Total score is sum of TF-IDF and adjustment
        country_foods = country_foods.withColumn(
            "score", 
            F.col("tfidf_sum") + F.col("adjustment_score")
        )

        current_user_high_ratings = user_comments_df.filter(
            (F.col("userId") == user_id) & 
            (F.col("rate") >= 4)
        ).select("foodId").distinct()

        # 2. Find similar users who also rated these foods highly
        similar_users = user_comments_df.filter(
            (F.col("userId") != user_id) &
            (F.col("rate") >= 4)
        ).join(
            current_user_high_ratings,
            "foodId",
            "inner"
        ).select("userId").distinct()

        # 3. Get similar users' high-rated foods that current user hasn't rated
        similar_users_ratings = user_comments_df.filter(
            F.col("userId").isin([u.userId for u in similar_users.collect()]) &
            (F.col("rate") >= 4)
        ).join(
            current_user_high_ratings,
            "foodId",
            "left_anti"  # Exclude foods user already rated
        )

        # 4. Aggregate and rank recommendations
        similarity_recommendations = similar_users_ratings.groupBy("foodId") \
            .agg(
                F.count("*").alias("similar_user_count"),
                F.avg("rate").alias("average_rating")
            ) \
            .orderBy(F.desc("similar_user_count"), F.desc("average_rating")) \
            .limit(5)  # Top 5 most popular among similar users
        # 5. Join with food data to get details
        if similarity_recommendations.count() > 0:
            similar_foods = similarity_recommendations.join(
                food_df.select("_id", "name", "country", "ingredients", "url_id"),
                F.col("foodId") == F.col("_id"),
                "inner"
            ).select(
                "_id",
                "name",
                "country",
                "ingredients",
                "url_id",
                "similar_user_count",
                "average_rating"
            )
            allergies = set(parse_prefs(prefs.get("allergies")))

            if allergies:  # Only filter if there are allergies
                similar_foods = filter_disliked_allergies(
                    similar_foods,
                    disliked={},
                    allergies=set(parse_prefs(prefs.get("allergies")))
                )
                print(f"Remaining similar foods after allergen check: {similar_foods.count()}")
            else:
                print("No allergens to filter")

            # 5. Join with food data to get details
            similar_foods_json = similar_foods.toJSON().collect()
        else:
            similar_foods_json = []

        recommendations = (
            country_foods
            .withColumn("score", F.expr(score_expr))
            .orderBy(F.desc("score"))
            .limit(top_n)
            .select(
                "_id",
                "name",
                "country",
                "url_id",
                F.expr("transform(ingredients, x -> lower(trim(x)))").alias("ingredients"),
                "score"
            )
        )
        # ========== Combine Results ==========
        main_recommendations = recommendations.toJSON().collect()
        print("Successfully generated recommendations")

        return {
            "personalized_recommendations": main_recommendations,
            "similar_users_recommendations": similar_foods_json
        }

    except Exception as e:
        print(f"Error during recommendation generation: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Recommendation engine failed: {str(e)}"
        )

from pyspark.ml.linalg import Vectors
import re

@router.get("/similar/{food_id}")
async def get_similar_foods(food_id: str, country: str = Query(..., title="Target country"), user_id: str = Depends(get_current_user),top_n: int = 10):
    try:
         # 1. Validate target country exists
        country_count = food_df.filter(F.col("country") == country).count()
        if country_count == 0:
            raise HTTPException(400, detail=f"No foods available in {country}")

        # 2. Find target food (regardless of its country)
        target_food = food_df.filter(F.col("_id") == food_id).first()
        if not target_food:
            raise HTTPException(404, detail="Food not found")
        
        # 3. Get user preferences
        survey = survey_df.filter(F.col("user_id") == user_id).first()
        if not survey:
            raise HTTPException(400, "Survey missing")
        
        prefs = survey.asDict().get("responses", {})
        if isinstance(prefs, Row):
            prefs = prefs.asDict()

        # 4. Prepare base dataset
        country_foods = food_df.filter(
            (F.col("country") == country) & 
            (F.col("_id") != food_id)
        ) 
        allergies = set(parse_prefs(prefs.get("allergies")))
        # 5. Filter disliked ingredients
        if allergies:  # Only filter if there are allergies
                country_foods = filter_disliked_allergies(
                    country_foods.filter(F.col("country") == country),
                    disliked={},
                    allergies=set(parse_prefs(prefs.get("allergies")))
                )
                print(f"Remaining similar foods after allergen check: {country_foods.count()}")
        else:
            print("No allergens to filter")

        # 6. Calculate cosine similarity
        target_vector = target_food.features
        target_bc = spark.sparkContext.broadcast(target_vector)

        def cosine_similarity(v):
            t = target_bc.value
            dot = float(t.dot(v))
            norm = float(t.norm(2) * v.norm(2))
            return dot / norm if norm != 0 else 0.0

        similarity_udf = F.udf(cosine_similarity, DoubleType())

        # 7. Get recommendations
        similar_foods = country_foods.withColumn(
            "similarity", similarity_udf(F.col("features"))
        ).orderBy(F.desc("similarity")).limit(top_n)

        return {
            "results": similar_foods.select(
                "_id", "name", "country", "ingredients", "similarity"
            ).toJSON().collect()
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))