from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.routes.food import router as FoodRouter

app = FastAPI()

# ✅ Correct CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Change this to production frontend URL if needed
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # ✅ Explicitly allow OPTIONS
    allow_headers=["*"],  # ✅ Allow all headers
)

# Include router without prefix issue
app.include_router(FoodRouter)

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to this fantastic app!"}
