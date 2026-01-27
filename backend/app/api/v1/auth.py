from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt 
from jwt.exceptions import PyJWTError
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.security import create_access_token
from backend.app.core.config import settings
from backend.app.core.db import get_db
from backend.app.core import crud_user
from backend.app.services.ajax_client import AjaxClient, AjaxAuthError

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], 
    db: AsyncSession = Depends(get_db)
):
    """
    Validate the JWT token and retrieve the current authenticated user.

    Args:
        token: The bearer JWT token from the Authorization header.
        db: Async database session.

    Returns:
        User: The database user object if the token is valid.

    Raises:
        HTTPException: 401 if the token is invalid, expired, or the user doesn't exist.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY.get_secret_value(), algorithms=[settings.ALGORITHM])
        user_email: str = payload.get("sub")
        if user_email is None:
             raise HTTPException(status_code=401, detail="Invalid credentials")
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    user = await crud_user.get_user_by_email(db, email=user_email)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db)
):
    """
    Unified login: Verify email/password against Ajax Systems.
    If valid, ensure the user exists in the local database and return a JWT access token.

    Args:
        form_data: Standard OAuth2 login form (includes username as email and password).
        db: Async database session.

    Returns:
        dict: A dictionary containing the 'access_token' and 'token_type'.

    Raises:
        HTTPException: 401 for incorrect Ajax credentials, 500 for service errors.
    """
    ajax = AjaxClient()
    try:
        # 1. Verify credentials directly with Ajax API
        ajax_data = await ajax.login_with_credentials(
            email=form_data.username, 
            password_raw=form_data.password
        )
        
        # 2. Get or create user in local database
        user = await crud_user.get_user_by_email(db, email=form_data.username)
        if not user:
            # Auto-provision user if they exist in Ajax but not in our DB
            from backend.app.schemas.user import UserCreate
            user_in = UserCreate(
                email=form_data.username,
                full_name=form_data.username.split("@")[0],
                password=form_data.password # Still hashed locally for consistency
            )
            user = await crud_user.create_user(db, user_in=user_in)
        
        # 3. Generate our system's Access Token
        access_token = create_access_token(subject=user.email)
        return {"access_token": access_token, "token_type": "bearer"}

    except AjaxAuthError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect Ajax email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Authentication service error: {str(e)}"
        )
