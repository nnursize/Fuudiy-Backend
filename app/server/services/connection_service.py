from bson import ObjectId
from server.database import database
from datetime import datetime

connection_collection = database.get_collection("connections")

async def send_request(from_id: str, to_id: str):
    existing = await connection_collection.find_one({
        "from": ObjectId(from_id),
        "to": ObjectId(to_id),
        "status": "pending"
    })
    if existing:
        return None  # Already requested
    return await connection_collection.insert_one({
        "from": ObjectId(from_id),
        "to": ObjectId(to_id),
        "status": "pending",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })

async def get_connections(user_id: str):
    cursor = connection_collection.find({
        "$or": [
            {"from": ObjectId(user_id), "status": "accepted"},
            {"to": ObjectId(user_id), "status": "accepted"}
        ]
    })
    return [conn async for conn in cursor]

async def get_pending_requests(user_id: str):
    cursor = connection_collection.find({
        "to": ObjectId(user_id),
        "status": "pending"
    })
    return [conn async for conn in cursor]

async def respond_to_request(from_id: str, to_id: str, status: str):
    result = await connection_collection.update_one(
        {"from": ObjectId(from_id), "to": ObjectId(to_id), "status": "pending"},
        {"$set": {"status": status, "updated_at": datetime.utcnow()}}
    )
    return result.modified_count > 0

async def get_user_ids_connected_to(user_id: str):
    connections = await get_connections(user_id)
    connected_ids = []
    for conn in connections:
        if str(conn["from"]) == user_id:
            connected_ids.append(str(conn["to"]))
        else:
            connected_ids.append(str(conn["from"]))
    return connected_ids
