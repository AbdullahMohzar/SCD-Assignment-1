# ==========================================
# Stage 1: Build stage
# ==========================================
FROM node:22.12.0-alpine3.21 AS builder

WORKDIR /app

# Copy dependency manifests first for layer caching
COPY package.json ./
RUN npm install

# Copy source code and build production static bundle
COPY tsconfig.json vite.config.ts index.html ./
COPY src/ src/
RUN npm run build

# ==========================================
# Stage 2: Runtime stage
# ==========================================
FROM nginx:1.27.3-alpine AS runner

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy built artifacts from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom nginx reverse proxy configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Give nginx permissions
RUN touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid /var/cache/nginx /usr/share/nginx/html

# Expose HTTP port
EXPOSE 80

# Healthcheck probe (§3.1)
HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:80/health || exit 1

# Exec form CMD (§3.1)
CMD ["nginx", "-g", "daemon off;"]
