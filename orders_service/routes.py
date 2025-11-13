from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from . import models
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import httpx

SECRET_KEY = "didi_food_secret_key_2024"
ALGORITHM = "HS256"
PRODUCTS_SERVICE_URL = "http://127.0.0.1:8002"  # Ajusta al puerto real

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
class OrderCreate(BaseModel):
    producto_id: int
    cantidad: int

# Endpoints
@router.get("/orders")
def list_orders(
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    orders = db.query(models.Order).filter(models.Order.user_email == current_user.get("sub")).all()
    return orders

from fastapi import status

@router.post("/orders", status_code=status.HTTP_201_CREATED)
def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    # Consultar datos del producto desde el microservicio de productos
    response = httpx.get(f"{PRODUCTS_SERVICE_URL}/products")
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Error al obtener productos del servicio de productos")

    products = response.json()
    product = next((p for p in products if p["id"] == order.producto_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    total = product["precio"] * order.cantidad

    new_order = models.Order(
        user_email=current_user.get("sub"),
        producto_nombre=product["nombre"],
        producto_precio=product["precio"],
        producto_descripcion=product["descripcion"],
        cantidad=order.cantidad,
        total=total
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return new_order

@router.get("/orders/{order_id}")
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    if order.user_email != current_user.get("sub"):
        raise HTTPException(status_code=403, detail="No puedes ver pedidos de otros usuarios")

    return order
