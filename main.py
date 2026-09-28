from fastapi import FastAPI
from fastapi_pagination import add_pagination
from sqladmin import Admin, I18nConfig

from core.admin import authentication_backend, autodiscover_admin_views
from core.config import settings
from core.db.session import engine
from core.lifespan import lifespan
from core.router import autodiscover_routes

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)
app.include_router(autodiscover_routes())
admin = Admin(
    app=app,
    engine=engine,
    authentication_backend=authentication_backend,
    # i18n_config=I18nConfig(default_locale="ru"),
)
autodiscover_admin_views(admin)
add_pagination(app)
