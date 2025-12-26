from fastapi.security import OAuth2PasswordRequestForm
from app.connection import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.utils import create_access_token, hash_password, verify_password
from app.models import User
from app.schemas import Token, UserCreate, UserLogin, UserOut
from app.service import get_response
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/register", response_model=UserOut)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        # Check if user already exists
        result = await db.execute(
            select(User).where(User.email == user.email)
        )
        existing_user = result.first()
        if existing_user:
            return get_response(
                status_code_enum=status.HTTP_400_BAD_REQUEST,
                data=None,
                message="Email already registered."
            )
        
        # Create new user
        new_user = User(
            email=user.email,
            hashed_password=hash_password(user.password),
            full_name=user.full_name,
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        return new_user

    except Exception as e:
        await db.rollback()
        return get_response(
            status_code_enum=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data=str(e),
            message="An error occurred while retrieving the portfolio."
        )


@router.post("/login", response_model=Token)
async def login(
    credentials: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Login endpoint - accepts email as username."""
    try:
        user = UserLogin(
            email=credentials.username,
            password=credentials.password
        )
        
        result = await db.execute(
            select(User).where(
                User.email == user.email,
                User.enabled == True
            )
        )
        existing_user = result.scalar_one_or_none()

        if not existing_user or not verify_password(
            user.password, existing_user.hashed_password
        ):
            return get_response(
                status_code_enum=status.HTTP_401_UNAUTHORIZED,
                data=None,
                message="Invalid credentials"
            )

        token = create_access_token({"user_id": existing_user.user_id})

        return {
            "access_token": token,
            "token_type": "bearer"
        }

    except Exception as e:
        return get_response(
            status_code_enum=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data=str(e),
            message="An error occurred while retrieving the portfolio."
        )


@router.get("/me", response_model=UserOut)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user info."""
    return current_user
