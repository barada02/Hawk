# ---- Stage 1: build the static assets ----
FROM node:22-alpine AS build

WORKDIR /app

# Backend URL is baked into the JS at BUILD time (Vite inlines import.meta.env).
# Pass it with: docker build --build-arg VITE_BACKEND_URI=https://<backend>.run.app
# (or gcloud's --build-arg). Setting it at runtime has NO effect on a static site.
ARG VITE_BACKEND_URI
ENV VITE_BACKEND_URI=${VITE_BACKEND_URI}

# Install deps first so this layer caches unless the lockfile changes.
COPY package.json package-lock.json ./
RUN npm ci

# Build the app (tsc -b && vite build -> /app/dist).
COPY . .
RUN npm run build

# ---- Stage 2: serve the static build ----
FROM node:22-alpine

WORKDIR /app

# Tiny static file server with SPA fallback support.
RUN npm install -g serve

# Only the built output is needed at runtime.
COPY --from=build /app/dist ./dist

# Cloud Run overrides PORT at runtime; 8080 is its default contract.
ENV PORT=8080
EXPOSE 8080

# -s: single-page-app mode (unknown routes -> index.html)
# -l: listen on the Cloud Run-provided $PORT
CMD ["sh", "-c", "serve -s dist -l ${PORT}"]
