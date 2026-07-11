# ---- Stage 1: build the static assets ----
FROM node:22-alpine AS build

WORKDIR /app

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
