
import os
from spark_utils import spark
from pyspark.sql import functions as F
from pyspark.sql import Row 
from pyspark.sql.functions import pandas_udf, col, explode, array_contains, lit, lower
from pyspark.sql.types import FloatType, ArrayType, StringType
from pyspark.ml.feature import Tokenizer, HashingTF, IDF
from pyspark.ml.linalg import SparseVector
from pyspark.ml.feature import CountVectorizer
from pyspark.ml import Pipeline
from pyspark.sql.types import ArrayType, IntegerType, DoubleType
from pyspark.ml.linalg import SparseVector
from pyspark.ml.functions import vector_to_array
from config import MONGO_URI, DATABASE_NAME, COLLECTION_FOOD, COLLECTION_SURVEY
from fastapi import APIRouter, HTTPException, Depends, Query
from ..services.auth_service import get_current_user
from pyspark.sql.functions import expr
import numpy as np

router = APIRouter()

# Security: Load credentials from environment
# f"mongodb+srv://admin:SIxxC6b6kj4pLek3@fuudiy.omyxh.mongodb.net/fuudiy.{collection_name}?retryWrites=true&w=majority&ssl=true&ipv6=false"))

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
    .select("_id", "country", "ingredients", "name")
    .withColumn(
        "ingredients",
        F.array_distinct(
            F.transform(
                F.split(F.col("ingredients"), "\s*,\s*"),
                lambda x: lower(F.trim(x))
            )
        )
    )
    .filter(F.size(F.col("ingredients")) > 0)
)

# 3. TF-IDF Pipeline
cv = CountVectorizer(inputCol="ingredients", outputCol="rawFeatures", vocabSize=10000)
idf = IDF(inputCol="rawFeatures", outputCol="features")
pipeline = Pipeline(stages=[cv, idf])
model = pipeline.fit(food_df)
food_df = model.transform(food_df).cache()

# 4. Broadcast Mappings
cv_model = model.stages[0]
idf_model = model.stages[1]

# Vocabulary (index → word)
reverse_vocab = {idx: word for idx, word in enumerate(cv_model.vocabulary)}
bc_reverse_vocab = spark.sparkContext.broadcast(reverse_vocab)

# IDF weights (index → weight)
idf_weights = {idx: float(w) for idx, w in enumerate(idf_model.idf.toArray())}
bc_idf_weights = spark.sparkContext.broadcast(idf_weights)
vocab_list = cv_model.vocabulary
idf_list = idf_model.idf.toArray().tolist()
# 5. Register UDFs
spark.udf.register("get_vocab_word", lambda idx: bc_reverse_vocab.value.get(idx, "UNKNOWN"))
spark.udf.register("get_idf", lambda idx: bc_idf_weights.value.get(idx, 0.0))

# ---------- Recommendation Endpoint ----------
@router.get("/recommend/")
async def recommend_foods(country: str = Query(..., title="Target country"), user_id: str = Depends(get_current_user), top_n: int = 10):
    print(f"Received country: {country}, user_id: {user_id}")  # Debugging
    #print("11111111111111111111")
    try:
        # 1. Validate country exists
        country_count = food_df.filter(F.col("country") == country).count()
        if country_count == 0:
            raise HTTPException(400, detail=f"No foods available in {country}")
        #print("22222222222222222")
        # 2. Validate user survey
        user_surveys = survey_df.filter(F.col("user_id") == user_id).take(1)
        #print(user_surveys)
        #print("aaaaaaaaaaaaaaaaaaaa")
        #print(user_surveys[0])
        survey_data = user_surveys[0].asDict()
        #print(survey_data)

        #print("33333333333333")
        # Get nested responses (handle Row/None cases)
        prefs = survey_data.get("responses", {})
        #print(prefs)
        if isinstance(prefs, Row):  # If responses is stored as Row
            prefs = prefs.asDict()
          #  print("33333333333333")
        #print("444444444444444444prefsdict44444")
        #print(prefs)
        # Unified preference parser
        def parse_prefs(value):
            if isinstance(value, str):
                # Split comma-separated strings into list
                return [x.strip().lower() for x in value.split(",")]
            if isinstance(value, list):
                return value
            return []
        liked = set(parse_prefs(prefs.get("liked_ingredients")))
        print("Liked:  ",liked)
        disliked = set(parse_prefs(prefs.get("disliked_ingredients"))) | \
                set(parse_prefs(prefs.get("allergies")))
        print("DISLiked:  ",disliked)
        # 4. Filter by country and disliked ingredients
        country_foods = food_df.filter(F.col("country") == country)

        if disliked:
            # Preprocess ingredients in DataFrame to lowercase and trimmed (if not already done)
            # Assuming food_df has a column 'ingredients' with each element cleaned
            # If not, preprocess here:
            country_foods = country_foods.withColumn(
                "ingredients",
                F.transform(F.col("ingredients"), lambda x: F.lower(F.trim(x)))
            )
            clean_disliked = [i.strip().lower() for i in disliked]
            for allergen in clean_disliked:
                country_foods = country_foods.filter(~F.array_contains(F.col("ingredients"), allergen))
        else:
            print("No disliked ingredients to filter")
        #print("5555555555555555531")
        # 5. Calculate TF-IDF scores
        # Convert sparse vectors to arrays
        country_foods = country_foods.withColumn(
            "tfidf_array", 
            vector_to_array("features")
        )
        
        # Simplified scoring using sum of TF-IDF values
        score_expr = """
            aggregate(
                tfidf_array,
                CAST(0.0 AS DOUBLE),
                (acc, x) -> acc + x
            )
        """
        
        # 6. Get recommendations
        recommendations = (
            country_foods
            .withColumn("score", F.expr(score_expr))
            .orderBy(F.desc("score"))
            .limit(top_n)
            .select(
                "_id",
                "name",
                "country",
                F.expr("transform(ingredients, x -> lower(trim(x)))").alias("ingredients"),
                "score"
            )
        )
        #print(recommendations.show(5))
        print("Successfully generated recommendations")
        return recommendations.toJSON().collect()

    except Exception as e:
        print(f"Error during recommendation generation: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Recommendation engine failed: {str(e)}"
        )
# Add this endpoint to your router
@router.get("/countries")
async def get_available_countries():
    """Get distinct available countries from food data"""
    #print("22222222222222222222222")
    try:
        # Get distinct countries from precomputed DataFrame
        countries = food_df.select("country").distinct()
        countries_list = countries.rdd.flatMap(lambda x: x).collect()
        return {"countries": sorted(countries_list)}
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch available countries: {str(e)}"
        )

