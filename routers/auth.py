from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from starlette import status
from typing import Annotated
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext

from models import User
from database import SessionLocal

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

SECRET_KEY = '52769ef4655713ac69c12f8e1d689ba05755560f7b748bf9d348e6ab0b21d2b6 '

ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')


class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    is_admin: bool


class Token(BaseModel):
    access_token: str
    token_type: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def authenticate_user(username: str, password: str, db):
    user = db.query(User).filter(User.username == username).first()

    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user


def create_access_token(username: str, user_id: int, is_admin: str, expires_data: timedelta):
    encode = {'sub': username, 'id': user_id, 'is_admin': is_admin}
    expires = datetime.now(timezone.utc) + expires_data
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        username: str = payload.get('sub')  # type: ignore
        user_id: int = payload.get('id')
        user_is_admin: str = payload.get('is_admin')
        if user_id is None or username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not valid user.')
        return {'user': username, 'id': user_id, 'user_is_admin': user_is_admin}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not valid user.')


db_dependency = Annotated[Session, Depends(get_db)]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def post_user(db: db_dependency, user_request: CreateUserRequest):
    user_model = User(
        email=user_request.email,
        username=user_request.username,
        first_name=user_request.first_name,
        last_name=user_request.last_name,
        is_admin=user_request.is_admin,
        hashed_password=bcrypt_context.hash(user_request.password)
    )

    db.add(user_model)
    db.commit()


@router.post("/token", response_model=Token)
async def login_for_acces_token(form_date: Annotated[OAuth2PasswordRequestForm, Depends()],
                                db: db_dependency):
    user = authenticate_user(form_date.username, form_date.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not valid user.')
    token = create_access_token(user.username, user.id, user.is_admin, timedelta(minutes=20))

    return {'access_token': token, 'token_type': 'bearer'}
