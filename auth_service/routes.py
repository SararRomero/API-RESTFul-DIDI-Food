from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from . import models
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


# Crear tablas
models.Base.metadata.create_all(bind=engine)

SECRET_KEY = "didi_food_secret_key_2024"
ALGORITHM = "HS256"


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str = "cliente"



class UserLogin(BaseModel):
    name: str  | None = None
    email: str | None = None
    password: str | None = None



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)



# ENDPOINT 1: Registrar usuario

from fastapi import FastAPI, status
@router.post("/register",status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email ya registrado")

    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        name=user.name,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return {"id": db_user.id,"name": db_user.name, "email": db_user.email, "role": db_user.role}


#  ENDPOINT 2: Login
from fastapi import FastAPI, status
@router.post("/login", status_code=status.HTTP_200_OK)
def login(user: UserLogin, db: Session = Depends(get_db)):

    # Validar que envíen todos los campos
    if not user.name or not user.email or not user.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe enviar 'name', 'email' y 'password'."
        )

    # Buscar usuario por email
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )

    # Validar nombre
    if db_user.name != user.name:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre incorrecto"
        )

    # Validar contraseña
    if not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )

    # Crear token
    token_data = {
        "sub": db_user.email,
        "role": db_user.role,
        "name": db_user.name
    }
    access_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "name": db_user.name
    }

#  ENDPOINT 3: Validar token y obtener usuario actual
@router.get("/me")
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Buscar usuario en la base de datos para obtener el ID
        db = SessionLocal()
        user = db.query(models.User).filter(models.User.email == payload.get("sub")).first()
        db.close()

        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }

    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
#  ENDPOINT ADICIONAL: Listar usuarios (SOLO para que Users Service pueda consultar)
@router.get("/users")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    # No devolver contraseñas
    return [{"id": user.id, "email": user.email, "role": user.role} for user in users]