from typing import Annotated, List
from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from requests import Session
from starlette import status
from pydantic import Field, BaseModel

from database import SessionLocal
from models import Order, Product, OrderDetail
from routers.auth import get_current_user


router = APIRouter(
    prefix='/customer',
    tags=['customer']
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

def check_stock(product_id: int, quantity: int, db: Session) -> bool:
    product = db.query(Product).filter(Product.id == product_id).first()
    if product and product.stock >= quantity:
        return True
    return False

class ProductRequest(BaseModel):
    name: str
    description: str
    price: float
    stock: int


class OrderResponse(BaseModel):
    order_id: int
    customer_id: int
    total_price: float

class OrderItem(BaseModel):
    product_id: int
    quantity: int

class OrderCreate(BaseModel):
    items: List[OrderItem]

@router.get('/products', status_code=status.HTTP_200_OK)
async def get_orders(user: user_dependency, db: db_dependency):
    model = db.query(Product).all()

    if model is None:
        raise HTTPException(status_code=404, detail="Product is not found!")
    return model


@router.get('/orders/{id}', status_code=status.HTTP_200_OK)
async def get_specific_orders(user: user_dependency, db: db_dependency, id: int):
    model = db.query(Order).filter(Order.id == id).first()
    if model is None:
        raise HTTPException(status_code=404, detail="Order is not found!")
    return model


@router.get('/orders/{id}/status', status_code=status.HTTP_200_OK)
async def get_products(user: user_dependency, db: db_dependency, id: int):
    model = db.query(OrderDetail).filter(OrderDetail.id == id).first()

    if model is None:
        raise HTTPException(status_code=404, detail="Order is not found!")
    return model.status


@router.post("/api/orders", response_model=OrderResponse)
async def create_order(user: user_dependency, db: db_dependency, order_request: OrderCreate):

    order_model = Order(customer_id=user.get("id"))
    db.add(order_model)
    db.commit()
    db.refresh(order_model)


    total_price = 0
    for item in order_request.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product ID {item.product_id} not found")
        if not check_stock(item.product_id, item.quantity, db):
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for product ID {item.product_id}"
                )



        order_detail = OrderDetail(
            order_id=order_model.id,
            product_id=item.product_id,
            quantity=item.quantity,
            status="pending"
        )
        db.add(order_detail)


        product.stock -= item.quantity
        total_price += product.price * item.quantity

    db.commit()

    return {
        "order_id": order_model.id,
        "customer_id": order_model.customer_id,
        "total_price": total_price,
        "message": "Order created successfully"
    }