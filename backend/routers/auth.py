"""
Velocity AI - Auth Router
Simple in-memory authentication for development/demo.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# In-memory user store
_users: dict[str, dict] = {}


class SignupRequest(BaseModel):
    email: str
    password: str
    name: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str
    remember_me: bool = False


class UserUpdate(BaseModel):
    email: str | None = None
    password: str | None = None
    name: str | None = None


class UserResponse(BaseModel):
    id: int
    email: str
    name: str | None = None
    token: str | None = None
    created_at: str | None = None


# Auto-increment ID
_next_id = 1


@router.post("/signup", response_model=UserResponse)
async def signup(request: SignupRequest):
    """Register a new user."""
    global _next_id

    # Check if email already exists
    for user in _users.values():
        if user["email"] == request.email:
            raise HTTPException(status_code=400, detail="Email already registered")

    user_id = _next_id
    _next_id += 1
    token = str(uuid.uuid4())

    user = {
        "id": user_id,
        "email": request.email,
        "password": request.password,
        "name": request.name or request.email.split("@")[0],
        "token": token,
        "created_at": datetime.utcnow().isoformat(),
    }

    _users[token] = user

    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        token=token,
        created_at=user["created_at"],
    )


@router.post("/login", response_model=UserResponse)
async def login(request: LoginRequest):
    """Log in an existing user."""
    for user in _users.values():
        if user["email"] == request.email and user["password"] == request.password:
            return UserResponse(
                id=user["id"],
                email=user["email"],
                name=user["name"],
                token=user["token"],
                created_at=user["created_at"],
            )

    raise HTTPException(status_code=401, detail="Invalid email or password")


@router.put("/user/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, request: UserUpdate):
    """Update user profile."""
    for user in _users.values():
        if user["id"] == user_id:
            if request.email:
                user["email"] = request.email
            if request.password:
                user["password"] = request.password
            if request.name:
                user["name"] = request.name

            return UserResponse(
                id=user["id"],
                email=user["email"],
                name=user["name"],
                token=user["token"],
                created_at=user["created_at"],
            )

    raise HTTPException(status_code=404, detail="User not found")
