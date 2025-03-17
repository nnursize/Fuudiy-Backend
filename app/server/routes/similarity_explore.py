from pyspark.sql import functions as F
from pyspark.sql.types import StringType
from server.database import food_df

def get_food_by_id(food_id: str):
    food_df.show()
