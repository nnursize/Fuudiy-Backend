from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, DATABASE_NAME, COLLECTION_FOOD, COLLECTION_SURVEY
from fastapi import FastAPI
import os

# python_path = r"C:\\Users\\USER\\Desktop\\Fuudiy\\Fuudiy-Backend\\fenv\Scripts\\python.exe"
# os.environ['PYSPARK_PYTHON'] = python_path
# os.environ['PYSPARK_DRIVER_PYTHON'] = python_path

from pyspark.sql import SparkSession

if not MONGO_URI:
    raise ValueError("MONGO_URI is not set in the .env file")

client = AsyncIOMotorClient(MONGO_URI)

database = client[DATABASE_NAME]
"""
# Initialize Spark session for MongoDB
def get_spark_session():
    #Create and return a Spark session configured for MongoDB.
    return SparkSession.builder \
        .appName("MongoDB-Spark") \
        .config("spark.network.timeout", "600s") \
        .config("spark.executor.cores", "2") \
        .config("spark.executor.heartbeatInterval", "60s") \
        .config("spark.driver.memory", "4g") \
        .config("spark.executor.memory", "4g") \
        .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.3.0") \
        .config("spark.mongodb.read.connection.uri", MONGO_URI) \
        .config("spark.mongodb.write.connection.uri", MONGO_URI) \
        .getOrCreate()

# Load data into Spark DataFrame
def load_food_data(spark, collection_name):
    #Load food data from MongoDB into Spark DataFrame.
  
    return spark.read.format("mongodb") \
        .option("database", "fuudiy") \
        .option("collection", collection_name) \
        .option("uri", f"mongodb+srv://admin:SIxxC6b6kj4pLek3@fuudiy.omyxh.mongodb.net/fuudiy.{collection_name}?retryWrites=true&w=majority&ssl=true&ipv6=false") \
        .option("ssl.enabled", "true") \
        .load()

# Initialize Spark and load data at startup
spark = get_spark_session()
food_df = load_food_data(spark, COLLECTION_FOOD)
survey_df = load_food_data(spark, COLLECTION_SURVEY)
"""