from app.connection import get_db
from app.models import User
from app.schemas import Token, UserCreate, UserLogin, UserOut
from app.service import get_response
from app.utils import create_access_token, hash_password, verify_password
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.encoders import jsonable_encoder
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Configuration


# Password hashing

router = APIRouter(prefix="/api", tags=["users"])

# Utility functions


@router.post("/users/register")
async def register(user: UserCreate,db: AsyncSession = Depends(get_db)):
    try:
        # Check if user already exists
        result = await db.execute(
            select(User).where(User.email == user.email)
        )
        existing_user = result.scalars().first()
        if existing_user:
            response=get_response(
                status="error",
                data=None,
                message="Email already registered."
            )
            return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response)
        
        # Create new user
        new_user = User(
            email=user.email,
            hashed_password=hash_password(user.password),
            full_name=user.full_name,
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        response=get_response(
            status="success",
            data=jsonable_encoder(new_user),
            message="User registered successfully."
        )
        return HTTPException(status_code=status.HTTP_201_CREATED, detail=response)
    except Exception as e:
        await db.rollback()

        response= get_response(
            status="error",
            data=str(e),
            message="An error occurred during registration."
        )
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=response)

@router.post("/auth/login")
async def login(user: UserLogin):
    try:
        async with AsyncSession() as db:
            result = await db.execute(
                select(User).where(User.email == user.email)
            )
            existing_user = result.scalars().first()
            if not existing_user or not verify_password(user.password, existing_user.hashed_password):
                response=get_response(
                    status="error",
                    data=None,
                    message="Invalid email or password."
                )
                return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=response)
            
            access_token = create_access_token(
                data={"sub": existing_user.email}
            )

            response=get_response(
                status="success",
                data={"access_token": access_token, "token_type": "bearer"},
                message="Login successful."
            )
            return HTTPException(status_code=status.HTTP_200_OK, detail=response)

    except Exception as e:
        print(e)
        response= get_response(
            status="error",
            data=str(e),
            message="An error occurred during login."
        )
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=response)