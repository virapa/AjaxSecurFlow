from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt 
from jwt.exceptions import PyJWTError
from backend.app.core.security import create_access_token
from backend.app.core.config import settings

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY.get_secret_value(), algorithms=[settings.ALGORITHM])
        user_email: str = payload.get("sub")
        if user_email is None:
             raise HTTPException(status_code=401, detail="Invalid credentials")
        return user_email
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/token")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    # Verify against bootstrap admin (for Phase 2 testing before DB is ready)
    # In Phase 3, this will replace with: user = await authenticate_user(db, form_data.username, form_data.password)
    
    if (form_data.username == settings.FIRST_SUPERUSER and 
        form_data.password == settings.FIRST_SUPERUSER_PASSWORD):
         pass
    else:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(subject=form_data.username)
    return {"access_token": access_token, "token_type": "bearer"} # nosec
