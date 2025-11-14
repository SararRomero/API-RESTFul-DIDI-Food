from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from . import models
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import httpx
from typing import List

SECRET_KEY = "didi_food_secret_key_2024"
ALGORITHM = "HS256"
PRODUCTS_SERVICE_URL = "http://127.0.0.1:8002"

models.Base.metadata.create_all(bind=engine)
router = APIRouter()
security = HTTPBearer()

# --------------------------
#     DEPENDENCIAS
# --------------------------
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


# --------------------------
#     SCHEMAS
# --------------------------
class OrderItem(BaseModel):
    product_id: int
    quantity: int


class OrderCreate(BaseModel):
    items: List[OrderItem]


# **RESPONSE MODEL OBLIGATORIO**
class OrderResponse(BaseModel):
    id: int
    user_email: str
    producto_nombre: str
    producto_precio: float
    producto_descripcion: str
    cantidad: int
    total: float

    class Config:
        orm_mode = True


# --------------------------
#     ENDPOINTS
# --------------------------

@router.get("/orders", response_model=List[OrderResponse])
def list_orders(
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    orders = (
        db.query(models.Order)
        .filter(models.Order.user_email == current_user.get("sub"))
        .all()
    )
    return orders



@router.post("/orders", status_code=status.HTTP_201_CREATED, response_model=List[OrderResponse])
def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    created_orders = []

    # Obtener lista de productos del microservicio
    response = httpx.get(f"{PRODUCTS_SERVICE_URL}/products")
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Error consultando productos")

    products = response.json()

    # Recorrer todos los productos enviados
    for item in order.items:
        product = next((p for p in products if p["id"] == item.product_id), None)

        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Producto con ID {item.product_id} no encontrado"
            )

        total = product["precio"] * item.quantity

        new_order = models.Order(
            user_email=current_user.get("sub"),
            producto_nombre=product["nombre"],
            producto_precio=product["precio"],
            producto_descripcion=product["descripcion"],
            cantidad=item.quantity,
            total=total
        )

        db.add(new_order)
        db.commit()
        db.refresh(new_order)

        created_orders.append(new_order)

    return created_orders



@router.get("/orders/{order_id}", response_model=OrderResponse)
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
