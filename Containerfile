FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --target=/app/deps -r requirements.txt

COPY idletest_app.py .

FROM gcr.io/distroless/python3

ENV PYTHONPATH=/app/deps

WORKDIR /app

COPY --from=builder /app /app

CMD ["-m", "uvicorn", "idletest:app", "--host", "0.0.0.0", "--port", "8080"]
