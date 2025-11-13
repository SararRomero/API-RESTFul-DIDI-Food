from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from . import models
from pydantic import BaseModel
from jose import JWTError, jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = "didi_food_secret_key_2024"
ALGORITHM = "HS256"

# Crear tablas (en la misma base que usa auth_service)
models.Base.metadata.create_all(bind=engine)

router = APIRouter()
security = HTTPBearer()

# -------------------------------
# Dependencias
# -------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verifica y decodifica el token JWT.
    Retorna el payload (email, role, etc.) si es válido.
    """
    try:
        if credentials.scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Esquema de autenticación inválido")

        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload

    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Error de autenticación: {str(e)}")


# -------------------------------
# Esquemas Pydantic
# -------------------------------
class UserUpdate(BaseModel):
    email: str | None = None
    role: str | None = None


class UserCreate(BaseModel):
    email: str
    role: str = "cliente"


# -------------------------------
# Rutas del servicio
# -------------------------------

#  Listar todos los usuarios (solo admin)
@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Se requieren privilegios de administrador")

    users = db.query(models.User).all()
    return [{"id": u.id, "email": u.email, "role": u.role} for u in users]


#  Obtener usuario por ID
@router.get("/users/{user_id}")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Se requieren privilegios de administrador")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return {"id": user.id, "email": user.email, "role": user.role}


#  Crear usuario (solo admin)
@router.post("/users")
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Se requieren privilegios de administrador")

    existing_user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    user = models.User(email=user_data.email, role=user_data.role)
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"id": user.id, "email": user.email, "role": user.role}


# Actualizar usuario
@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Se requieren privilegios de administrador")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if user_update.email is not None:
        user.email = user_update.email
    if user_update.role is not None:
        user.role = user_update.role

    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "role": user.role}


#  Eliminar usuario
@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Se requieren privilegios de administrador")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db.delete(user)
    db.commit()
    return {"message": f"Usuario '{user.email}' eliminado correctamente"}


# Obtener información del usuario actual (desde el token)
@router.get("/me")
def get_current_user_info(current_user: dict = Depends(verify_token)):
    return {
        "email": current_user.get("sub"),
        "role": current_user.get("role"),
        "id": "N/A (desde token JWT)"
    }
