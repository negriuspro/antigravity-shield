from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timezone
from jose import JWTError

from app.database import get_db
from app.models.user import User
from app.auth.jwt import verify_password, hash_password, create_access_token, create_refresh_token, decode_token
from app.auth.dependencies import get_current_user
from app.schemas.user import UserCreate, UserOut, TokenResponse, TokenRefresh

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == form.username, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    await db.execute(update(User).where(User.id == user.id).values(last_login=datetime.now(timezone.utc)))
    await db.commit()

    return TokenResponse(
        access_token=create_access_token(user.username, user.role.value),
        refresh_token=create_refresh_token(user.username),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: TokenRefresh, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError
        username = payload["sub"]
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    result = await db.execute(select(User).where(User.username == username, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return TokenResponse(
        access_token=create_access_token(user.username, user.role.value),
        refresh_token=create_refresh_token(user.username),
    )


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user


@router.post("/register", response_model=UserOut, status_code=201)
async def register(body: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(
        (User.username == body.username) | (User.email == body.email)
    ))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username or email already exists")
    user = User(
        email=body.email,
        username=body.username,
        hashed_password=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
