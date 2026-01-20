FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock /app/
RUN uv sync --system --frozen --no-cache

COPY gradient_mapper.py /app/gradient_mapper.py
COPY lib /app/lib
COPY web /app/web
COPY gradient /app/gradient
COPY input /app/input
COPY output /app/output

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "web.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
