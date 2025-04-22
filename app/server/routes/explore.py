
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
from typing import Optional

router = APIRouter()

from pymongo import MongoClient

client = MongoClient(MONGO_URI)
db = client["fuudiy"]
DISH_INGREDIENT_MAP = {
    "vegetarian_dishes": ["lettuce", "tomato"],
    "meat_dishes": ["meat", "lamb", "beef", "steak"],
    "seafood": ["lobster", "crab", "fish", "shellfish"],
    "pastries_and_bread": ["flour", "yeast"],
    "sweets_and_confectionery": ["sugar", "chocolate"],
    "sushi": ["rice", "fish", "nori", "tuna", "crab", "soy sauce"],
    "pizza": ["cheese", "tomato", "flour", "saussage"],
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
    .filter(F.size(F.col("ingredients")) > 0)
    .filter(F.col("ingredients").isNotNull())  # Add null check
    .cache()
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

def filter_disliked_allergies(df, disliked, allergies=None):
    all_exclusions = list(disliked)
    if allergies:
        all_exclusions += list(allergies)
    
    if not all_exclusions:
        return df

    exclusion_array = F.array(*[F.lit(e) for e in all_exclusions])

    return df.filter(
        F.size(
            F.array_intersect(F.col("ingredients"), exclusion_array)
        ) == 0
    )

def calculate_ingredient_adjustments(prefs):
    adjustments = defaultdict(float)
    
    food_prefs = prefs.get("food_preferences", {})
    
    if isinstance(food_prefs, list):
        food_prefs = {item["key"]: item["value"] for item in food_prefs}
    elif isinstance(food_prefs, Row):
        food_prefs = food_prefs.asDict()
    
    for dish, ingredients in DISH_INGREDIENT_MAP.items():
        raw_rating = prefs.get(dish) or food_prefs.get(dish)
        
        numerical_rating = 3
        
        if raw_rating:
            if isinstance(raw_rating, (int, float)):
                numerical_rating = max(1, min(int(raw_rating), 5))
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

food_df = tfidf_pipeline.transform(food_df)
#food_df.unpersist()
vector_to_array = F.udf(lambda v: v.toArray().tolist(), ArrayType(DoubleType()))

# ---------- Recommendation Endpoint ----------
@router.get("/recommend/")
async def recommend_foods(country: str = Query(..., title="Target country"), diet: Optional[str] = Query(None, title="Dietary restriction"), user_id: str = Depends(get_current_user), top_n: int = 10):
    
    print(f"Received country: {country}, user_id: {user_id}")  # Debugging
    try:
        if diet is not None:
            print("Diet:", diet)
            restrictions = db["special_diet"].find_one({"category": diet.lower()})
            exclusion_ingredients = restrictions.get("restricted_ingredients", []) if restrictions else []
        else:
            exclusion_ingredients = []
            print("No diet filter")
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

        user_comments_df = load_food_data(spark, COLLECTION_USER_COMMENTS).cache()
        user_comments_filtered = user_comments_df.filter(F.col("userId") == user_id)

        commented_foods = user_comments_filtered.join(
            food_df.select("_id", "ingredients"),
            user_comments_filtered.foodId == food_df._id,
            "inner"
        ).select("rate", "ingredients")

        commented_foods_data = commented_foods.collect()

        for row in commented_foods_data:
            rate = row['rate']
            ingredients = row['ingredients']
            rate_val = float(rate) if rate is not None else 3.0
            adjustment = (rate_val - 3) * 1.0
            for ingredient in ingredients:
                ingredient_adjustments[ingredient] += adjustment

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
            allergies=set(parse_prefs(prefs.get("allergies"))) | set(exclusion_ingredients)
        ).withColumn("score", 
            F.aggregate(
                vector_to_array("features"), 
                F.lit(0.0), 
                lambda acc, x: acc + x
            ) + calculate_adjustment_udf(F.col("ingredients"))
        )

        country_foods = country_foods.withColumn(
            "tfidf_array", 
            vector_to_array("features")
        )

        score_expr = """
            aggregate(
                tfidf_array,
                CAST(0.0 AS DOUBLE),
                (acc, x) -> acc + x
            )
        """
        country_foods = country_foods.withColumn("tfidf_sum", F.expr(score_expr))

        country_foods = country_foods.withColumn(
            "adjustment_score", 
            calculate_adjustment_udf(F.col("ingredients"))
        )

        country_foods = country_foods.withColumn(
            "score", 
            F.col("tfidf_sum") + F.col("adjustment_score")
        )

        current_user_high_ratings = user_comments_df.filter(
            (F.col("userId") == user_id) & 
            (F.col("rate") >= 4)
        ).select("foodId").distinct()

        similar_users = user_comments_df.filter(
            (F.col("userId") != user_id) &
            (F.col("rate") >= 4)
        ).join(
            current_user_high_ratings,
            "foodId",
            "inner"
        ).select("userId").distinct()

        similar_users_ratings = user_comments_df.filter(
            F.col("userId").isin([u.userId for u in similar_users.collect()]) &
            (F.col("rate") >= 4)
        ).join(
            current_user_high_ratings,
            "foodId",
            "left_anti"  # Exclude foods user already rated
        )

        similarity_recommendations = similar_users_ratings.groupBy("foodId") \
            .agg(
                F.count("*").alias("similar_user_count"),
                F.avg("rate").alias("average_rating")
            ) \
            .orderBy(F.desc("similar_user_count"), F.desc("average_rating")) \
            .limit(5)  # Top 5 most popular among similar users
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

            if allergies or exclusion_ingredients:
                similar_foods = filter_disliked_allergies(
                    similar_foods,
                    disliked={},
                    allergies=set(parse_prefs(prefs.get("allergies"))) | set(exclusion_ingredients)
                )
                print(f"Remaining similar foods after allergen check: {similar_foods.count()}")
            else:
                print("No allergens to filter")

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
                "ingredients",
                "score"
            )
        )

        if exclusion_ingredients:
            recommendations = filter_disliked_allergies(
                recommendations,
                disliked=[],
                allergies=exclusion_ingredients
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


@router.get("/similar/{food_id}")
async def get_similar_foods(food_id: str, country: str = Query(..., title="Target country"), diet: Optional[str] = Query(None, title="Dietary restriction"), user_id: str = Depends(get_current_user),top_n: int = 10):
    try:
        
        if diet is not None:
            print("Diet:", diet)
            restrictions = db["special_diet"].find_one({"category": diet.lower()})
            exclusion_ingredients = restrictions.get("restricted_ingredients", []) if restrictions else []
        else:
            exclusion_ingredients = []
            print("No diet filter")
        country_count = food_df.filter(F.col("country") == country).count()
        if country_count == 0:
            raise HTTPException(400, detail=f"No foods available in {country}")

        target_food = food_df.filter(F.col("_id") == food_id).first()
        if not target_food:
            raise HTTPException(404, detail="Food not found")
        
        survey = survey_df.filter(F.col("user_id") == user_id).first()
        if not survey:
            raise HTTPException(400, "Survey missing")
        
        prefs = survey.asDict().get("responses", {})
        if isinstance(prefs, Row):
            prefs = prefs.asDict()

        country_foods = food_df.filter(
            (F.col("country") == country) & 
            (F.col("_id") != food_id)
        ) 
        allergies = set(parse_prefs(prefs.get("allergies")))
        if allergies or exclusion_ingredients:
                country_foods = filter_disliked_allergies(
                    country_foods.filter(F.col("country") == country),
                    disliked={},
                    allergies=set(parse_prefs(prefs.get("allergies"))) | set(exclusion_ingredients)
                )
                print(f"Remaining after filters: {country_foods.count()}")
        else:
            print("No filters applied")

        target_vector = target_food.features
        target_bc = spark.sparkContext.broadcast(target_vector)

        def cosine_similarity(v):
            t = target_bc.value
            dot = float(t.dot(v))
            norm = float(t.norm(2) * v.norm(2))
            return dot / norm if norm != 0 else 0.0

        similarity_udf = F.udf(cosine_similarity, DoubleType())

        similar_foods = country_foods.withColumn(
            "similarity", similarity_udf(F.col("features"))
        ).orderBy(F.desc("similarity")).limit(top_n)

        if exclusion_ingredients:
            similar_foods = filter_disliked_allergies(
                similar_foods,
                disliked=[],
                allergies=exclusion_ingredients
            )
        return {
            "results": similar_foods.select(
                "_id", "name", "country", "ingredients", "similarity", "url_id"
            ).toJSON().collect()
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))