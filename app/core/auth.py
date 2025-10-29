from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.core.exceptions.user import ExpiredTokenError, InvalidTokenError
from app.schemas.user import TokenResponse

SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_MINUTES = 10080


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)


def create_tokens(id: UUID) -> TokenResponse:
    access_token = _encode_jwt(
        data={"sub": str(id)},
        time_expires=ACCESS_TOKEN_EXPIRE_MINUTES,
        token_type="access",
    )
    refresh_token = _encode_jwt(
        data={"sub": str(id)},
        time_expires=REFRESH_TOKEN_EXPIRE_MINUTES,
        token_type="refresh",
    )

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


def refresh_tokens(refresh_token: str) -> TokenResponse:
    user_id = decode_jwt(refresh_token).get("sub")
    new_tokens = create_tokens(UUID(user_id))

    return new_tokens


def decode_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ExpiredTokenError()
    except jwt.InvalidTokenError:
        raise InvalidTokenError()


def _encode_jwt(data: dict, time_expires: int, token_type: str) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=time_expires)

    to_encode.update({"exp": expire})
    to_encode.update({"type": token_type})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
