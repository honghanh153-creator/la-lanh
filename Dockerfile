# syntax=docker/dockerfile:1.7

FROM node:24-bookworm-slim AS web-build
WORKDIR /source
RUN corepack enable && corepack prepare pnpm@11.19.0 --activate

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/package.json
COPY packages/contracts/package.json packages/contracts/package.json
RUN pnpm install --frozen-lockfile --filter @la-lanh/web...

COPY apps/web apps/web
COPY packages/contracts packages/contracts
RUN pnpm --filter @la-lanh/web build


FROM debian:bookworm-slim AS swiss-build
RUN apt-get update \
    && apt-get install --no-install-recommends -y build-essential ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /source
COPY vendor/swisseph vendor/swisseph
RUN make -C vendor/swisseph verify


FROM python:3.13-slim-bookworm AS runtime
COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /uvx /bin/

ENV PATH="/app/apps/api/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LA_LANH_REQUIRE_WEB_DIST=true \
    LA_LANH_SWISSEPH_LIBRARY_PATH=/app/vendor/swisseph/build/libswe.so \
    LA_LANH_SWISSEPH_EPHEMERIS_PATH=/app/vendor/swisseph/ephe

WORKDIR /app/apps/api
COPY apps/api/pyproject.toml apps/api/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY apps/api /app/apps/api
COPY vendor/swisseph/ephe /app/vendor/swisseph/ephe
COPY --from=swiss-build /source/vendor/swisseph/build/libswe.so /app/vendor/swisseph/build/libswe.so
COPY --from=web-build /source/apps/web/dist /app/apps/web/dist

USER 65532:65532
EXPOSE 8080
CMD ["uvicorn", "app.cloud_run:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers", "--forwarded-allow-ips=*", "--no-access-log"]
