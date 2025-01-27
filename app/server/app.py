from fastapi import FastAPI

from server.routes.food import router as FoodRouter

app = FastAPI()

app.include_router(FoodRouter, tags=["Food"], prefix="/food")


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to this fantastic app!"}