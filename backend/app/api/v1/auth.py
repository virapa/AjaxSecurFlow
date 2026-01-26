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

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: AsyncSession = Depends(get_db)):
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
    # Authenticate user against DB
    user = await crud_user.authenticate_user(db, form_data.username, form_data.password)
    
    # Fallback to bootstrap superuser if DB is empty or user not found, 
    # but ONLY if configured and credentials match exactly.
    if not user:
        if (form_data.username == settings.FIRST_SUPERUSER and 
            form_data.password == settings.FIRST_SUPERUSER_PASSWORD):
            # Create the superuser in DB if it doesn't exist? 
            # Ideally yes, let's auto-provision or just allow login.
            # For strictness: Just allow token generation for now.
            pass
        else:
             raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    # If user exists, or bootstrap passed
    subject = user.email if user else form_data.username
    access_token = create_access_token(subject=subject)
    return {"access_token": access_token, "token_type": "bearer"} # nosec
