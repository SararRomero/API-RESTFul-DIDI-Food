from sqlalchemy import Column, Integer, String, Float
from .database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, nullable=False)
    producto_nombre = Column(String, nullable=False)
    producto_precio = Column(Float, nullable=False)
    producto_descripcion = Column(String, nullable=False)
    cantidad = Column(Integer, nullable=False)
    total = Column(Float, nullable=False)
