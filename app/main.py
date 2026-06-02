from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import auth, documents, admin, query
from app.core.config import settings


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the routers
app.include_router(
    auth.router, 
    prefix=f"{settings.API_V1_STR}/auth", 
    tags=["Authentication"]
)
app.include_router(
    documents.router,
    prefix=f"{settings.API_V1_STR}/documents",
    tags=["Documents"]
)
app.include_router(
    admin.router,
    prefix=f"{settings.API_V1_STR}/admin",
    tags=["Admin"]
)
app.include_router(
    query.router,
    prefix=f"{settings.API_V1_STR}/query",
    tags=["Query"]
)

