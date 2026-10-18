
import os
import time
import uuid
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()

EMAIL = "23f2004697@ds.study.iitm.ac.in"

ALLOWED_ORIGINS = {
    "https://app-popwnv.example.com",
    "https://exam.sanand.workers.dev",
}


RATE_LIMIT = 11
WINDOW_SECONDS = 10

# Each client has its own rolling 10-second window.
requests_by_client = defaultdict(deque)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path == "/ping" and request.method == "GET":
        client_id = request.headers.get("X-Client-Id")
        if not client_id:
            client_id = request.client.host if request.client else "unknown"

        now = time.monotonic()
        timestamps = requests_by_client[client_id]

        while timestamps and now - timestamps[0] >= WINDOW_SECONDS:
            timestamps.popleft()

        if len(timestamps) >= RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
            )

        timestamps.append(now)

    return await call_next(request)



@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response



@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }


# Explicit origins only; never use "*".
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(ALLOWED_ORIGINS),
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=[
        "X-Request-ID",
        "X-Client-Id",
        "Content-Type",
    ],
    expose_headers=["X-Request-ID"],
)
