from .admin import admin_router
from .channels import channels_router
from .info import info_router
from .start import start_router

__all__ = [
    "start_router",
    "info_router",
    "admin_router",
    "channels_router",
]
