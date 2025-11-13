from fastapi import FastAPI
from . import routes
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Products Service",
    docs_url="/docs",
    swagger_ui_parameters={"persistAuthorization": True}
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router)

@app.get("/")
def root():
    return {"message": "Products Service run"}
