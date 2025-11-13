from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from . import models
from jose import jwt, JWTError
from pydantic import BaseModel
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = "didi_food_secret_key_2024"
ALGORITHM = "HS256"

models.Base.metadata.create_all(bind=engine)
router = APIRouter()
security = HTTPBearer()

# Dependencias
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

# Schemas
class ProductCreate(BaseModel):
    nombre: str
    descripcion: str
    precio: float

class ProductUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    precio: float | None = None

# Endpoints
@router.get("/products")
def list_products(db: Session = Depends(get_db)):
    products = db.query(models.Product).all()
    return [{"id": p.id, "nombre": p.nombre, "precio": p.precio, "descripcion": p.descripcion} for p in products]


from fastapi import status
@router.post("/products", status_code=status.HTTP_201_CREATED)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):

    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo los administradores pueden crear productos")

    new_product = models.Product(**product.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@router.put("/products/{product_id}")
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo los administradores pueden actualizar productos")

    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    for key, value in product_data.dict(exclude_unset=True).items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)
    return product

@router.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo los administradores pueden eliminar productos")

    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    db.delete(product)
    db.commit()
    return {"message": f"Producto '{product.nombre}' eliminado correctamente"}
