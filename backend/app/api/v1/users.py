from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.deps import get_db, get_ajax_client
from backend.app.crud import user as crud_user
from backend.app.schemas.user import UserCreate, UserRead
from backend.app.schemas.auth import ErrorMessage
from backend.app.api.v1.auth import get_current_user
from backend.app.domain.models import User
from backend.app.services.ajax_client import AjaxClient
from backend.app.services import billing_service

router = APIRouter()

@router.post(
    "/", 
    response_model=UserRead,
    summary="Register New User",
    responses={
        400: {"model": ErrorMessage, "description": "User already exists"},
    }
)
async def create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Registers a new user in the local system. 
    This is usually called during the first login or manual signup.
    """
    user = await crud_user.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    return await crud_user.create_user(db, email=user_in.email, password=user_in.password)

@router.get(
    "/me", 
    response_model=UserRead,
    summary="Get Current User Profile",
    description="Returns the profile information of the currently authenticated user enriched with Ajax data."
)
async def read_user_me(
    current_user: User = Depends(get_current_user),
    client: AjaxClient = Depends(get_ajax_client)
):
    # 1. Start with local data
    user_read_data = UserRead.model_validate(current_user).model_dump()
    
    # 2. Inject dynamic billing info
    # subscription_active determines if the user's plan is valid (any paid plan)
    user_read_data["subscription_active"] = billing_service.is_subscription_active(current_user)
    user_read_data["billing_status"] = current_user.subscription_status
    
    # 3. Attempt to enrich with Ajax data
    try:
        ajax_data = await client.get_user_info(current_user.email)
        user_read_data["ajax_info"] = ajax_data
    except Exception as e:
        import logging
        logging.getLogger("uvicorn.error").warning(f"Failed to fetch Ajax user info for {current_user.email}: {e}")
    
    return user_read_data
