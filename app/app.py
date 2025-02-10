from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.routes.food import router as FoodRouter
from server.routes.user import router as UserRouter
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],  
)

# Include routers directly
app.include_router(FoodRouter)
app.include_router(UserRouter)

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to this fantastic app!"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
