# --- Tahap build ---
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# URL backend ditanam saat build (Vite membaca env berawalan VITE_).
# Kosongkan untuk deployment same-origin (nginx mem-proxy /api -> backend).
ARG VITE_API_URL=
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# --- Tahap runtime ---
FROM nginx:1.27-alpine

# Nilai default untuk Docker Compose. Di Railway, timpa lewat service
# variables:
#   BACKEND_URL=http://<service>.railway.internal:8000
#   NGINX_RESOLVER=[fd12::10] ipv6=on
# atau BACKEND_URL=https://<backend>.up.railway.app (proxy server-side).
ENV BACKEND_URL=http://backend:8000 \
    NGINX_RESOLVER="127.0.0.11 ipv6=off" \
    NGINX_ENVSUBST_FILTER="^(BACKEND_URL|NGINX_RESOLVER)$"

# Entrypoint resmi nginx akan menjalankan envsubst dan menulis
# /etc/nginx/conf.d/default.conf dari template ini saat container start.
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q --spider http://127.0.0.1/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
