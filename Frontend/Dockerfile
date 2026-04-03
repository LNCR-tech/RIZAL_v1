FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
# Make npm installs more resilient in flaky networks and faster in CI/builds.
ENV npm_config_audit=false \
    npm_config_fund=false \
    npm_config_fetch_retries=5 \
    npm_config_fetch_retry_mintimeout=10000 \
    npm_config_fetch_retry_maxtimeout=120000

RUN npm ci --no-audit --no-fund

COPY . .

ARG VITE_API_BASE_URL=/__backend__
ARG VITE_API_TIMEOUT_MS=15000

ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_API_TIMEOUT_MS=${VITE_API_TIMEOUT_MS}

RUN npm run build

FROM nginx:1.27-alpine AS runtime

COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY runtime-config.js.template /opt/aura/runtime-config.js.template
COPY docker-entrypoint.d/40-runtime-config.sh /docker-entrypoint.d/40-runtime-config.sh
RUN chmod +x /docker-entrypoint.d/40-runtime-config.sh
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
