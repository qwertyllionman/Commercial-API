from typing import Annotated

from database import SessionLocal
from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from models import Order, Product
from pydantic import BaseModel
from requests import Session
from routers.auth import get_current_user
from starlette import status

router = APIRouter(
    prefix='/admin',
    tags=['admin']
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


class ProductRequest(BaseModel):
    name: str
    description: str
    price: float
    stock: int


@router.get('/orders/', status_code=status.HTTP_200_OK)
async def get_orders(user: user_dependency, db: db_dependency):
    if user is None or user.get("user_is_admin") == False:
        raise HTTPException(status_code=403, detail="Admin privilege is required")

    model = db.query(Order).all()

    if model is None:
        raise HTTPException(status_code=404, detail="Order is not found!")
    return model


@router.get('/orders/{id}', status_code=status.HTTP_200_OK)
async def get_specific_orders(user: user_dependency, db: db_dependency, id: int):
    if user is None or user.get("user_is_admin") == False:
        raise HTTPException(status_code=403, detail="Admin privilege is required")

    model = db.query(Order).filter(Order.id == id).first()

    if model is None:
        raise HTTPException(status_code=404, detail="Order is not found!")
    return model


@router.get('/products/{id}', status_code=status.HTTP_200_OK)
async def get_products(user: user_dependency, db: db_dependency, id: int):
    if user is None or user.get("user_is_admin") == False:
        raise HTTPException(status_code=403, detail="Admin privilege is required")

    model = db.query(Product).filter(Product.id == id).first()

    if model is None:
        raise HTTPException(status_code=404, detail="Order is not found!")
    return model


@router.post("/products", status_code=status.HTTP_201_CREATED)
async def add_product(user: user_dependency, db: db_dependency, product: ProductRequest):
    if user is None or user.get("user_is_admin") == False:
        raise HTTPException(status_code=403, detail="Admin privilege is required")

    product_db = Product(
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock
    )
    db.add(product_db)
    db.commit()


@router.put("/products/{id}")
async def update_product(user: user_dependency, db: db_dependency, product: ProductRequest, id: int):
    if user is None or user.get("user_is_admin") == False:
        raise HTTPException(status_code=403, detail="Admin privilege is required")

    product_db = db.query(Product).filter(Product.id == id).first()

    if product_db is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    product_db.name = (product.name)
    product_db.description = product.description
    product_db.price = product.price
    product_db.price = product.price
    db.add(product_db)
    db.commit()


@router.delete("/products/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency, db: db_dependency, id: int):
    if user is None or user.get("user_is_admin") == False:
        raise HTTPException(status_code=403, detail="Admin privilege is required")
    product_db = db.query(Product).filter(Product.id == id).first()
    if product_db is None:
        raise HTTPException(status_code=404, detail="Todo not found.")
    db.query(Product).filter(Product.id == id).delete()
    db.commit()
