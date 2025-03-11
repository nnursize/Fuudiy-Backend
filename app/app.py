from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.routes.food import router as FoodRouter
from server.routes.user import router as UserRouter
from server.routes.comment import router as UserCommentsRouter
from server.routes.auth import router as AuthRouter
from server.routes.survey import router as SurveyRouter

from server.database import database

#from server.routes.translation import router as TranslationRouter
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers with unique prefixes
app.include_router(FoodRouter, prefix="/food", tags=["Food"])
app.include_router(UserRouter, prefix="/users", tags=["User"])
app.include_router(UserCommentsRouter, prefix="/comments", tags=["Comment"])
app.include_router(AuthRouter, prefix="/auth", tags=["Auth"])
app.include_router(SurveyRouter, prefix="/survey", tags=["Survey"])
app.include_router(TranslationRouter, prefix="/translation", tags=["Translation"])

#app.include_router(TranslationRouter, prefix="/translation", tags=["Translation"])

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to this fantastic app!"}

app.state.database = database

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

