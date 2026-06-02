# 1. Update builder to use Python 3.13 to match distroless
FROM --platform=linux/amd64 python:3.13-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y gcc python3-dev

COPY requirements.txt .
# Install dependencies into /app/deps
RUN pip install --upgrade pip && \
    pip install --target=/app/deps -r requirements.txt

# 2. Final stage (already using Python 3.13 via distroless/python3)
FROM --platform=linux/amd64 gcr.io/distroless/python3

ENV PYTHONPATH=/app/deps

WORKDIR /app

# Copy deps and your app
COPY --from=builder /app/deps /app/deps
COPY idletest_app.py .

CMD ["-m", "uvicorn", "idletest_app:app", "--host", "0.0.0.0", "--port", "8080"]
