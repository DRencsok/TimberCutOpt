FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.19 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    PYTHONUNBUFFERED=1

WORKDIR /app


COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --group api --no-install-project


COPY README.md ./
COPY src ./src
COPY api ./api
RUN uv sync --frozen --no-dev --group api

ENV PATH="/app/.venv/bin:$PATH"

RUN DJANGO_SECRET_KEY=build-only python api/manage.py collectstatic --noinput

RUN useradd --create-home app
USER app

ENV PORT=8000 \
    WEB_CONCURRENCY=2
EXPOSE 8000

CMD ["gunicorn", "--chdir", "api", "config.wsgi:application", "--timeout", "60", "--access-logfile", "-"]