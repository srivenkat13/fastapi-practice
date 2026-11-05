"""Entry point for servers: `fastapi run lessons/r4_deployment/solution/main.py` or uvicorn ...main:app"""
from .app import create_app
from .settings import Settings

app = create_app(Settings())
