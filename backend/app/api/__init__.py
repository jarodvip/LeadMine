from fastapi import APIRouter
from app.api import auth, leads, resources, processor, alerts, users

api_router = APIRouter(prefix="/api/v1")

# 挂载各个模块的路由
api_router.include_router(auth.router)
api_router.include_router(leads.router)
api_router.include_router(resources.router_article)
api_router.include_router(resources.router_source)
api_router.include_router(processor.router)
api_router.include_router(alerts.router)
api_router.include_router(users.router)
