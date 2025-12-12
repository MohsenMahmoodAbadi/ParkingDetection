import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import parking_app.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parking_project.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            parking_app.routing.websocket_urlpatterns
        )
    ),
})