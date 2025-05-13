from handlers.admin import router as admin_router
from handlers.commands import router as commands_router
from handlers.user import router as user_router

__all__ = ["commands_router", "admin_router", "user_router"]
