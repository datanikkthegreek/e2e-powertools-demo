from .core import create_app
from . import _seed_dep  # noqa: F401  registers the Lakebase post-init seed hook
from .router import router
from .events import router as events_router

app = create_app(routers=[router, events_router])
