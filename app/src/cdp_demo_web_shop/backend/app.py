from .core import create_app
from . import _seed_dep  # noqa: F401  registers the Lakebase post-init seed hook
from .router import router
from .events import router as events_router
from .analytics import router as analytics_router
from .jobs import router as jobs_router

app = create_app(routers=[router, events_router, analytics_router, jobs_router])
