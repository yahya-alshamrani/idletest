import asyncio
import logging
import os
from urllib.parse import urlsplit, urlunsplit

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

# Set up basic logging config
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

INGRESS_GATEWAY_ENABLED_ENV = "INGRESS_GATEWAY_ENABLED"
INGRESS_GATEWAY_HOST_ENV = "INGRESS_GATEWAY_HOST"
INGRESS_GATEWAY_PATH_ENV = "INGRESS_GATEWAY_PATH"


def required_boolean_environment_variable(name: str) -> bool:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(f"{name} environment variable must be defined")

    normalized_value = value.strip().lower()
    if normalized_value in {"1", "true", "yes", "on"}:
        return True
    if normalized_value in {"0", "false", "no", "off"}:
        return False

    raise RuntimeError(f"{name} must be one of: true, false, 1, 0, yes, no, on, off")


def required_environment_variable(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(f"{name} environment variable must be defined")

    return value.strip()


INGRESS_GATEWAY_ENABLED = required_boolean_environment_variable(INGRESS_GATEWAY_ENABLED_ENV)
GATEWAY_HOST = required_environment_variable(INGRESS_GATEWAY_HOST_ENV) if INGRESS_GATEWAY_ENABLED else ""
GATEWAY_PATH = required_environment_variable(INGRESS_GATEWAY_PATH_ENV) if INGRESS_GATEWAY_ENABLED else ""

app = FastAPI()


def normalized_gateway_path(raw_path: str) -> str:
    gateway_path = raw_path.strip()
    if not gateway_path or gateway_path == "/":
        return ""

    if not gateway_path.startswith("/"):
        gateway_path = f"/{gateway_path}"

    return gateway_path.rstrip("/")


def gateway_external_path(internal_path: str, gateway_path: str) -> str:
    if not gateway_path:
        return internal_path or "/"

    if not internal_path:
        return gateway_path

    if not internal_path.startswith("/"):
        internal_path = f"/{internal_path}"

    if internal_path == gateway_path or internal_path.startswith(f"{gateway_path}/"):
        return internal_path

    return f"{gateway_path}{internal_path}"


def gateway_redirect_location(location: str, request: Request) -> str:
    gateway_host = GATEWAY_HOST
    if not location:
        return location

    gateway_path = normalized_gateway_path(GATEWAY_PATH)

    if "://" in gateway_host:
        gateway = urlsplit(gateway_host)
        redirect_scheme = gateway.scheme
        redirect_host = gateway.netloc
        if not gateway_path:
            gateway_path = normalized_gateway_path(gateway.path)
    else:
        redirect_scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
        redirect_host, _, path_from_host = gateway_host.partition("/")
        if path_from_host and not gateway_path:
            gateway_path = normalized_gateway_path(path_from_host)

    if not redirect_host:
        logger.warning("Ignoring invalid %s=%r", INGRESS_GATEWAY_HOST_ENV, gateway_host)
        return location

    parsed = urlsplit(location)
    if parsed.scheme and parsed.netloc:
        redirect_path = gateway_external_path(parsed.path, gateway_path)
        return urlunsplit(
            (redirect_scheme or parsed.scheme, redirect_host, redirect_path, parsed.query, parsed.fragment)
        )

    if location.startswith("/"):
        relative = urlsplit(location)
        redirect_path = gateway_external_path(relative.path, gateway_path)
        return urlunsplit((redirect_scheme, redirect_host, redirect_path, relative.query, relative.fragment))

    return location


@app.middleware("http")
async def rewrite_redirects_for_gateway(request: Request, call_next):
    response = await call_next(request)

    location = response.headers.get("location")
    if INGRESS_GATEWAY_ENABLED and location and 300 <= response.status_code < 400:
        response.headers["location"] = gateway_redirect_location(location, request)

    return response


@app.get("/idle={idle}")
async def idel(idle: int, request: Request):
    logger.info(f"Received request from {request.client.host} with idle={idle}")

    if idle < 0 or idle > 600:
        logger.warning("Invalid idle received")
        raise HTTPException(status_code=400, detail="Idle must be between 0 and 600 seconds")

    logger.debug(f"Sleeping for {idle} seconds")
    await asyncio.sleep(idle)
    logger.info(f"Returning response after sleeping {idle} seconds")

    return JSONResponse(content={"message": f"Waited for {idle} seconds"}, status_code=200)
