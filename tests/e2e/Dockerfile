FROM mcr.microsoft.com/playwright:v1.40.0-focal

WORKDIR /app

# Install Node.js dependencies
COPY package*.json ./
RUN npm ci

# Copy test files
COPY . .

# Install additional testing utilities
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    mongodb-clients \
    && rm -rf /var/lib/apt/lists/*

# Create directories for reports and results
RUN mkdir -p /app/playwright-report /app/test-results

# Set permissions
RUN chmod +x /app/scripts/*.sh || true

# Default command runs all E2E tests
CMD ["npm", "run", "test:e2e"]
