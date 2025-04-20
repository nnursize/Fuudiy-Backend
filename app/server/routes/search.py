# server/routes/search.py
import re
from fastapi import APIRouter, Query, HTTPException
from server.database import database

router = APIRouter(tags=["Search"])
food_coll = database.get_collection("cleaned_foods")
user_coll = database.get_collection("users")

@router.get("/search")
async def search(
    q: str = Query(..., min_length=1), 
    limit: int = Query(10, ge=1, le=50)
):
    """
    Searches food.name and user.username for substring `q` (case‑insensitive).
    Returns up to `limit` hits from each collection, merged together.
    """
    try:
        regex = re.compile(re.escape(q), re.IGNORECASE)
        # foods
        foods_cursor = food_coll.find(
            {"name": regex}, {"name": 1}
        ).limit(limit)
        foods = [
            {"type": "food", "id": str(f["_id"]), "name": f["name"]}
            async for f in foods_cursor
        ]
        # users
        users_cursor = user_coll.find(
            {"username": regex}, {"username": 1}
        ).limit(limit)
        users = [
            {"type": "user", "id": u["username"], "name": u["username"]}
            async for u in users_cursor
        ]
        # simple merge; you can sort by custom rules if you like
        return {"results": foods + users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
