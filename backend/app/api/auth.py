from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user

from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import get_db
from app.db.models import User
from app.schemas.auth import LoginRequest, RegisterRequest

router = APIRouter(tags=["auth"])


@router.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == request.username).first()
    if existing_user:
        return {"error": "Username already taken"}

    new_user = User(
        username=request.username,
        hashed_password=hash_password(request.password),
    )
    db.add(new_user)
    db.commit()

    return {"message": f"User '{request.username}' registered successfully"}


@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == request.username).first()

    if not user or not verify_password(request.password, user.hashed_password):
        return {"error": "Invalid username or password"}

    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}



@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {"username": current_user.username, "is_admin": bool(current_user.is_admin)}