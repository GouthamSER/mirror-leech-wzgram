from os import environ
from aiohttp import web

from ... import LOGGER
from ...core.config_manager import Config


async def _ok(_):
    return web.Response(text="OK")


async def start_health_server():
    """Tiny HTTP server so Koyeb (or any PaaS) health check passes.

    Port: HEALTH_PORT env > PORT env > 8000.
    Skipped if the web selection server (BASE_URL) already owns that port.
    """
    port = int(environ.get("HEALTH_PORT") or environ.get("PORT") or 8000)
    if Config.BASE_URL and int(Config.BASE_URL_PORT) == port:
        LOGGER.info(f"Health check: BASE_URL server already on port {port}")
        return
    try:
        app = web.Application()
        app.router.add_get("/", _ok)
        app.router.add_get("/health", _ok)
        runner = web.AppRunner(app, access_log=None)
        await runner.setup()
        await web.TCPSite(runner, "0.0.0.0", port).start()
        LOGGER.info(f"Health check server on port {port}")
    except OSError as e:
        LOGGER.error(f"Health check server failed on port {port}: {e}")
