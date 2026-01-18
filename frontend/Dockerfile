# Frontend Dockerfile - React + Vite with Nginx
#
# This uses a "multi-stage build" to create a small production image:
#
# Stage 1 (build): 
#   - Uses Node.js to install dependencies and build the React app
#   - Runs `npm run build` which creates optimized static files in /app/dist
#   - This stage is ~1GB but is discarded after building
#
# Stage 2 (production):
#   - Uses tiny Nginx Alpine image (~20MB)
#   - Copies ONLY the built files from Stage 1
#   - Serves static files efficiently
#
# Build: docker build -t rag-frontend ./frontend
# Run:   docker run -p 80:80 rag-frontend

# ============ Stage 1: Build ============
FROM node:18-alpine AS build

WORKDIR /app

# Copy package files first (for Docker layer caching)
COPY package*.json ./

# Install dependencies
RUN npm ci --silent

# Copy source code
COPY . .

# Build the production bundle (creates /app/dist folder)
RUN npm run build

# ============ Stage 2: Production ============
FROM nginx:alpine

# Copy built static files from the build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom nginx config (handles SPA routing)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Start Nginx in foreground (not as daemon)
CMD ["nginx", "-g", "daemon off;"]
