from datetime import datetime
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from server.services.auth_service import get_current_user
from server.services.connection_service import (
    send_request, get_connections, get_pending_requests, respond_to_request, get_user_ids_connected_to
)
from server.models.connection import ConnectionUpdateModel
from server.services.user_service import retrieve_user
from bson import ObjectId
from server.database import database

connection_collection = database.get_collection("connections")

class ConnectionStatusUpdate(BaseModel):
    connection_id: str
    status: Literal["accepted", "rejected"]

router = APIRouter()

@router.post("/send-request/{from_username}/{to_username}", tags=["Connection"])
async def send_friend_request(from_username: str, to_username: str):
    print("AAAAAAAAAAAAAAA")
    from_user_obj = await retrieve_user(from_username)
    to_user_obj = await retrieve_user(to_username)

    if not from_user_obj or not to_user_obj:
        raise HTTPException(status_code=404, detail="User not found.")

    if from_user_obj["id"] == to_user_obj["id"]:
        raise HTTPException(status_code=400, detail="You cannot send a request to yourself.")

    result = await send_request(from_user_obj["id"], to_user_obj["id"])
    if not result:
        raise HTTPException(status_code=400, detail="Request already sent or exists.")
    
    return {"message": "Friendship request sent."}


@router.get("/my-connections", tags=["Connection"])
async def my_connections(user_id: str = Depends(get_current_user)):
    connections = await get_user_ids_connected_to(user_id)
    return {"connected_users": connections}

@router.get("/incoming-requests", tags=["Connection"])
async def get_incoming_requests(user_id: str = Depends(get_current_user)):
    print(f"[INCOMING REQUESTS] user_id: {user_id}")  # ← add this line
    requests = await get_pending_requests(user_id)
    return {"pending_requests": requests}

@router.put("/respond/{from_user}", tags=["Connection"])
async def respond_request(from_user: str, response: ConnectionUpdateModel, to_user: str = Depends(get_current_user)):
    success = await respond_to_request(from_user, to_user, response.status)
    if not success:
        raise HTTPException(status_code=404, detail="No pending request found.")
    return {"message": f"Request {response.status}."}

@router.get("/requests/details/{username}", tags=["Connection"])
async def get_request_details(username: str):
    from server.services.user_service import retrieve_user, retrieve_user_by_id

    user = await retrieve_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_id = user["id"]  # This is the correct way after user_helper()

    print("get_request_details user_id: ", user_id)

    # Incoming requests
    incoming_cursor = connection_collection.find({
        "to": ObjectId(user_id),
        "status": "pending"
    })

    incoming_requests = []
    async for conn in incoming_cursor:
        from_user_id = str(conn["from"])
        from_user = await retrieve_user_by_id(from_user_id)
        if from_user:
            incoming_requests.append({
                "_id": str(conn["_id"]),
                "from_username": from_user["username"],
                "status": conn["status"],
                "created_at": conn["created_at"]
            })

    # Sent requests
    sent_cursor = connection_collection.find({
        "from": ObjectId(user_id)
    })

    sent_requests = []
    async for conn in sent_cursor:
        to_user_id = str(conn["to"])
        to_user = await retrieve_user_by_id(to_user_id)
        if to_user:
            sent_requests.append({
                "to_username": to_user["username"],
                "status": conn["status"],
                "updated_at": conn["updated_at"]
            })

    return {
        "incoming_requests": incoming_requests,
        "sent_requests": sent_requests
    }

@router.put("/update-status", tags=["Connection"])
async def update_connection_status(update: ConnectionStatusUpdate, user_id: str = Depends(get_current_user)):
    try:
        conn_id = ObjectId(update.connection_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid connection ID.")

    connection = await connection_collection.find_one({"_id": conn_id})

    print(" AAAAAAA updated connection: ", connection)

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found.")

    if str(connection["to"]) != user_id:
        raise HTTPException(status_code=403, detail="You are not authorized to update this connection.")

    result = await connection_collection.update_one(
        {"_id": conn_id},
        {"$set": {"status": update.status, "updated_at": datetime.utcnow()}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Update failed.")

    return {"message": f"Connection {update.status}."}


@router.get("/count/{username}", tags=["Connection"])
async def get_accepted_connection_count(username: str):
    user = await retrieve_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_id = ObjectId(user["id"])

    accepted_connections = await connection_collection.count_documents({
        "$or": [
            {"from": user_id},
            {"to": user_id}
        ],
        "status": "accepted"
    })

    return {"count": accepted_connections}


@router.get("/list/{username}", tags=["Connection"])
async def get_accepted_connection_usernames(username: str):
    print("     get_accepted_connection_usernames       ")
    from server.services.user_service import retrieve_user_by_id

    user = await retrieve_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_id = ObjectId(user["id"])

    # Find all accepted connections where the user is either the sender or receiver
    cursor = connection_collection.find({
        "$or": [
            {"from": user_id},
            {"to": user_id}
        ],
        "status": "accepted"
    })

    connected_usernames = []
    async for conn in cursor:
        other_user_id = conn["to"] if conn["from"] == user_id else conn["from"]
        other_user = await retrieve_user_by_id(str(other_user_id))
        if other_user:
            connected_usernames.append(other_user["username"])

    print("connected_usernames: ", connected_usernames)

    return {"connected_usernames": connected_usernames}


@router.delete("/remove/{from_username}/{to_username}", tags=["Connection"])
async def remove_connection(from_username: str, to_username: str):
    from server.services.user_service import retrieve_user
    from bson import ObjectId

    from_user = await retrieve_user(from_username)
    to_user = await retrieve_user(to_username)

    if not from_user or not to_user:
        raise HTTPException(status_code=404, detail="User not found.")

    result = await connection_collection.delete_one({
        "$or": [
            {"from": ObjectId(from_user["id"]), "to": ObjectId(to_user["id"])},
            {"from": ObjectId(to_user["id"]), "to": ObjectId(from_user["id"])}
        ]
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Connection not found.")

    return {"message": "Connection removed."}

@router.get("/status/{from_username}/{to_username}", tags=["Connection"])
async def get_connection_status(from_username: str, to_username: str):
    from server.services.user_service import retrieve_user
    from bson import ObjectId

    from_user = await retrieve_user(from_username)
    to_user = await retrieve_user(to_username)

    if not from_user or not to_user:
        raise HTTPException(status_code=404, detail="User not found.")

    connection = await connection_collection.find_one({
        "$or": [
            {"from": ObjectId(from_user["id"]), "to": ObjectId(to_user["id"])},
            {"from": ObjectId(to_user["id"]), "to": ObjectId(from_user["id"])}
        ]
    })

    if not connection:
        return {"status": None}

    return {"status": connection["status"]}


@router.delete("/remove-by-id/{connection_id}", tags=["Connection"])
async def remove_connection_by_id(connection_id: str, user_id: str = Depends(get_current_user)):
    try:
        conn_id = ObjectId(connection_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid connection ID.")

    connection = await connection_collection.find_one({"_id": conn_id})
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found.")

    # Only the "to" user (recipient) can reject
    if str(connection["to"]) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this connection.")

    result = await connection_collection.delete_one({"_id": conn_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=400, detail="Failed to delete connection.")

    return {"message": "Connection request rejected and removed."}
