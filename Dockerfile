FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

RUN pip install --upgrade pip uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --no-dev

ENV PATH="/app/.venv/bin:$PATH"

COPY . .

EXPOSE 8000

CMD ["python", "-m", "server"]
