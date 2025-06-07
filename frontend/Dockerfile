# Multi-stage build for production-ready React frontend
FROM node:18-alpine AS base

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./
COPY pnpm-lock.yaml ./

# Install pnpm
RUN npm install -g pnpm

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy source code
COPY . .

# Build stage
FROM base AS build

# Accept build arguments
ARG VITE_AUTH0_DOMAIN=dev-jwnud3v8ghqnyygr.us.auth0.com
ARG VITE_AUTH0_CLIENT_ID=KXu3KpGiyRHHHgiXX90sHuNC4rfYRcNn
ARG VITE_AUTH0_AUDIENCE=https://pathfinder-api.com
ARG VITE_API_URL=https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io
ARG ENVIRONMENT=production

# Set environment variables from build args
ENV NODE_ENV=production
ENV VITE_AUTH0_DOMAIN=${VITE_AUTH0_DOMAIN}
ENV VITE_AUTH0_CLIENT_ID=${VITE_AUTH0_CLIENT_ID}
ENV VITE_AUTH0_AUDIENCE=${VITE_AUTH0_AUDIENCE}
ENV VITE_API_URL=${VITE_API_URL}
ENV ENVIRONMENT=${ENVIRONMENT}

# Build the application
RUN pnpm run build

# Production stage
FROM nginx:alpine AS production

# Install curl for health checks
RUN apk add --no-cache curl

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy built application from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom entrypoint script for runtime environment variable replacement
COPY entrypoint.sh /entrypoint.sh

# Create non-root user and set up directories
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001 && \
    mkdir -p /tmp/nginx && \
    chown -R nextjs:nodejs /usr/share/nginx/html && \
    chown -R nextjs:nodejs /tmp/nginx && \
    touch /tmp/nginx/nginx.pid && \
    chown nextjs:nodejs /tmp/nginx/nginx.pid && \
    chmod +x /entrypoint.sh

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/ || exit 1

# Use custom entrypoint that handles runtime environment variable replacement
ENTRYPOINT ["/entrypoint.sh"]