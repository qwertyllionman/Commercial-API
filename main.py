from fastapi import FastAPI
import models
from database import engine
from routers import auth, customer, admin

app = FastAPI()

models.Base.metadata.drop_all(bind=engine)
models.Base.metadata.create_all(bind=engine)
app.include_router(auth.router)
app.include_router(customer.router)
app.include_router(admin.router)
