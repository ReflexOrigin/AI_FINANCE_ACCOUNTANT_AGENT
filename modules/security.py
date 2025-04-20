"""
Security Module for Finance Accountant Agent

This module handles authentication, authorization, input sanitization,
rate limiting, and other security-related functions for the Finance Agent.

Features:
- JWT-based authentication
- Input sanitization for financial data
- Rate limiting for API endpoints
- Secure credential storage
- Permission management
- Audit logging

Dependencies:
- fastapi.security: For OAuth2 and JWT implementation
- jose: For JWT encoding/decoding
- passlib: For password hashing
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from config.settings import settings

logger = logging.getLogger(__name__)

# Security tools initialization
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Demo users (in production, use a database)
USERS = {
    "admin": {
        "username": "admin",
        "hashed_password": pwd_context.hash("admin"),  # Not secure for production
        "full_name": "Admin User",
        "email": "admin@example.com",
        "permissions": ["admin", "read", "write"],
        "disabled": False,
    },
    "user": {
        "username": "user",
        "hashed_password": pwd_context.hash("user"),  # Not secure for production
        "full_name": "Regular User",
        "email": "user@example.com",
        "permissions": ["read"],
        "disabled": False,
    },
}

# Rate limiting configuration
RATE_LIMIT_COUNTER = {}


async def authenticate_user(username: str, password: str) -> Optional[str]:
    if username not in USERS:
        return None

    user = USERS[username]

    if user["disabled"] or not pwd_context.verify(password, user["hashed_password"]):
        return None

    token_data = {
        "sub": username,
        "permissions": user["permissions"],
        "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }

    token = jwt.encode(token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    logger.info(f"User {username} authenticated successfully")
    return token


async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        if username is None or username not in USERS:
            raise credentials_exception

        user_data = USERS[username]
        if user_data["disabled"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled",
            )

        user_data["permissions"] = payload.get("permissions", [])
        return user_data

    except JWTError:
        raise credentials_exception


async def check_permission(user: Dict, required_permission: str) -> bool:
    if "admin" in user.get("permissions", []):
        return True
    return required_permission in user.get("permissions", [])


async def sanitize_input(text: str) -> str:
    sanitized = text.replace("<", "&lt;").replace(">", "&gt;")
    return sanitized


async def rate_limit_check(
    request: Request,
    max_requests: Optional[int] = None,
    timeframe: Optional[int] = None,
) -> bool:
    if not settings.RATE_LIMIT_ENABLED:
        return True

    max_requests = max_requests or settings.RATE_LIMIT_MAX_REQUESTS
    timeframe = timeframe or settings.RATE_LIMIT_TIMEFRAME_SECONDS

    client_ip = request.client.host if request.client else "unknown"
    client_id = f"{client_ip}"

    current_time = time.time()

    if client_id not in RATE_LIMIT_COUNTER:
        RATE_LIMIT_COUNTER[client_id] = {"count": 0, "reset_time": current_time + timeframe}

    client_data = RATE_LIMIT_COUNTER[client_id]

    if current_time > client_data["reset_time"]:
        client_data["count"] = 0
        client_data["reset_time"] = current_time + timeframe

    if client_data["count"] >= max_requests:
        logger.warning(f"Rate limit exceeded for {client_id}")
        return False

    client_data["count"] += 1
    return True


async def audit_log(user: Dict, action: str, resource: str, success: bool, details: Optional[str] = None):
    username = user.get("username", "anonymous")
    log_message = f"AUDIT: User={username} Action={action} Resource={resource} Success={success}"
    if details:
        log_message += f" Details={details}"

    if success:
        logger.info(log_message)
    else:
        logger.warning(log_message)
