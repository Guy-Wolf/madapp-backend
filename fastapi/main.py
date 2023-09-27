from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

import mdaappDB

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


connected_users = {}


DB_CON = mdaappDB.MdaappDB()

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    disabled: bool | None = None

class UserInfo(BaseModel):
    username: str
    first_name: str 
    last_name: str 
    birth_date: str
    user_city: str
    user_street: str
    disabled: bool = False

class EventInfo(BaseModel):
    eid: int
    mood: int
    notes: str


class UserInDB(User):
    hashed_password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

origins = ["*"]

# cors handeling
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def convert_mysql_dict_to_user_dict(username, mysql_dict):
    return {'username': username,
            'first_name': mysql_dict['FIRST_NAME'], 
            'last_name': mysql_dict['LAST_NAME'], 
            'birth_date': str(mysql_dict['BIRTH']), 
            'user_city': mysql_dict['CITY'], 
            'user_street': mysql_dict['STREET'], 
            'disabled': False}


def get_user(db, username: str):
    print("here!!")
    if db.is_user_exists(username):
        user_dict = db.get_user_data_by_mail(username)
        user_info_dict = convert_mysql_dict_to_user_dict(username, user_dict)
        return UserInfo(**user_info_dict)


def authenticate_user(db, username: str, password: str):
    user_exists = db.is_user_exists(username)
    if not user_exists:
        return False
    if not db.check_user_creds(username, password):
        return False
    return True

def add_user(db, username: str, password: str, signup_info: UserInfo):
    user_exists = db.is_user_exists(username)
    if user_exists:
        return False
    db.add_user(username, password, signup_info.first_name, signup_info.last_name, signup_info.birth_date,
                signup_info.user_city, signup_info.user_street)
    return True


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(DB_CON, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = authenticate_user(DB_CON, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/add/event", response_model=bool)
async def add_event(
    current_user: Annotated[User, Depends(get_current_active_user)],
    event_info: Annotated[EventInfo, Depends()]
):
    add_event_res = DB_CON.log_event(current_user.username, event_info.eid, event_info.mood, event_info.notes)
    if not add_event_res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event doesn't exist",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return 
    
    
@app.post("/register", response_model=Token)
async def register_for_access_token(
    signup_info: Annotated[UserInfo, Depends()],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = add_user(DB_CON, form_data.username, form_data.password, signup_info)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User already existes",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=UserInfo)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return current_user

@app.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return [{"item_id": "Foo", "owner": current_user.username}]
