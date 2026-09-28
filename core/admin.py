import importlib
import inspect

import bcrypt
from sqladmin import Admin
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select
from starlette.requests import Request
from starlette.responses import RedirectResponse

from apps.users.admin import UserAdmin
from apps.users.models import User
from core.db.service import logger
from core.db.session import SessionLocal
from core.utils.pkg import get_modules


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool | RedirectResponse:
        form = await request.form()
        username, password = form["username"], form["password"]
        async with SessionLocal() as session:
            user: User = await session.scalar(select(User).filter_by(email = username))
            if bcrypt.checkpw(password.encode('utf-8'), user.hashed_password.encode('utf-8')):
                request.session.update({"token": "..."})
                return True
            return False

    async def logout(self, request: Request) -> bool | RedirectResponse:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        if not token:
            return False

        # Check the token in depth
        return True


authentication_backend = AdminAuth(secret_key="qwerty")

def autodiscover_admin_views(admin: Admin):
    for module_path in get_modules('apps'):
        if module_path.endswith('admin'):
            module = importlib.import_module(module_path)
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if name.endswith('Admin') and obj.__module__ == module.__name__:
                    admin.add_view(obj)