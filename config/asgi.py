"""Point d'entrée ASGI, servi par Uvicorn.

ASGI permet les vues asynchrones, dont le chat en direct (SSE) aura besoin.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()
