# --- Builder Stage ---
FROM python:3.13.1-alpine3.21 AS builder

ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --prefix=/install -r requirements.txt

# --- Final Stage ---
FROM python:3.13.1-alpine3.21

ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY --from=builder /install /usr/local

RUN apk add --no-cache nano bash htop tzdata
