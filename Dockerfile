# NOTE: The build context should be the repository root.
FROM python:3.12-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING="utf-8" \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN apt-get update && \
    apt-get install -y gcc build-essential curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

RUN chmod +x /app/run_server.sh

ENV PYTHONPATH="/app:${PYTHONPATH}"
EXPOSE 8000

#
# Production image
#
FROM base AS prod
CMD ["./run_server.sh"]

#
# Development image
#
FROM base AS dev
RUN pip install --no-cache-dir watchfiles
CMD ["./run_server.sh"]

