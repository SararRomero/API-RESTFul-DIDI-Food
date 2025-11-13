from fastapi import FastAPI
from . import routes

app = FastAPI(title="Auth Service")

app.include_router(routes.router)

@app.get("/")
def root():
    return {"message": "Auth Service running "}