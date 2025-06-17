# End-to-End Testing Guide

This document provides comprehensive guidance for running and maintaining the Pathfinder application's End-to-End (E2E) testing suite.

## Overview

The E2E testing suite provides comprehensive validation of the Pathfinder application by testing complete user workflows in an isolated environment. It uses Docker Compose to orchestrate all services and Playwright for browser automation.

### Architecture

- **Backend**: FastAPI application with test database
- **Frontend**: React/Vite application served via Nginx
- **Database**: MongoDB instance dedicated to E2E testing
- **Cache**: Redis for session management
- **Mock Services**: Authentication service for local testing
- **Test Runner**: Playwright with multi-browser support

## Prerequisites

### System Requirements

- Docker and Docker Compose installed
- Node.js 18+ (for local development and debugging)
- At least 4GB available RAM
- Available ports: 3000, 8000, 27017, 6379, 8081, 9080

### First-Time Setup

1. **Clone and navigate to the project root**:
   ```bash
   cd /path/to/pathfinder
   ```

2. **Ensure Docker is running**:
   ```bash
   docker --version
   docker-compose --version
   ```

3. **Make the E2E script executable**:
   ```bash
   chmod +x scripts/run-e2e-tests.sh
   ```

## Running E2E Tests

### Quick Start (Recommended)

Run the complete E2E suite with automatic setup and cleanup:

```bash
./scripts/run-e2e-tests.sh
```

This script will:
- Build and start all required services
- Wait for services to be healthy
- Initialize test data
- Run all E2E tests
- Generate reports
- Clean up resources

### Manual Orchestration

For debugging or custom workflows:

1. **Start E2E environment**:
   ```bash
   docker-compose -f docker-compose.e2e.yml up -d
   ```

2. **Wait for services to be ready** (check health):
   ```bash
   cd tests/e2e
   node scripts/health-check.js
   ```

3. **Initialize test data**:
   ```bash
   node scripts/setup-test-data.js
   ```

4. **Run tests**:
   ```bash
   npm test
   ```

5. **Clean up**:
   ```bash
   node scripts/cleanup-test-data.js
   docker-compose -f docker-compose.e2e.yml down -v
   ```

### Running Specific Tests

**Run specific test suites**:
```bash
# Authentication tests only
npx playwright test auth

# Trip management tests only
npx playwright test trips

# API integration tests only
npx playwright test api

# Complete workflows only
npx playwright test workflows
```

**Run tests in specific browsers**:
```bash
# Chrome only
npx playwright test --project=chromium

# Firefox only
npx playwright test --project=firefox

# Mobile simulation
npx playwright test --project=mobile
```

**Debug mode (headed browser)**:
```bash
npx playwright test --debug
```

## Test Structure

### Test Organization

```
tests/e2e/
├── tests/
│   ├── setup.spec.ts              # Environment validation
│   ├── auth/
│   │   └── auth-flow.spec.ts      # Login, logout, session management
│   ├── trips/
│   │   └── trip-management.spec.ts # CRUD operations, validation
│   ├── families/
│   │   └── family-management.spec.ts # Family features, invitations
│   ├── api/
│   │   └── api-integration.spec.ts # API endpoints, error handling
│   └── workflows/
│       └── complete-workflows.spec.ts # End-to-end user journeys
├── utils/
│   └── test-helpers.ts            # Shared utilities and fixtures
└── scripts/
    ├── health-check.js            # Service health validation
    ├── setup-test-data.js         # Test data initialization
    ├── cleanup-test-data.js       # Test data cleanup
    └── mongodb-init.js            # Database setup
```

### Test Categories

1. **Setup Tests** (`setup.spec.ts`)
   - Service availability validation
   - Database connectivity
   - Environment configuration

2. **Authentication Tests** (`auth/auth-flow.spec.ts`)
   - User login and logout flows
   - Session persistence
   - Authentication error handling
   - Token validation

3. **Trip Management Tests** (`trips/trip-management.spec.ts`)
   - Create, read, update, delete trips
   - Form validation
   - Search and filtering
   - Data persistence

4. **Family Management Tests** (`families/family-management.spec.ts`)
   - Family creation and management
   - Member invitations
   - Permission handling
   - Family preferences

5. **API Integration Tests** (`api/api-integration.spec.ts`)
   - REST endpoint validation
   - CORS handling
   - Error response formats
   - Rate limiting
   - Request/response payloads

6. **Complete Workflows** (`workflows/complete-workflows.spec.ts`)
   - Multi-user scenarios
   - Complex business flows
   - Cross-feature integration
   - Session management across flows

## Test Data Management

### Test Isolation

Each test run uses a completely isolated environment:
- Dedicated MongoDB database (`pathfinder_e2e_test`)
- Fresh Redis cache
- Isolated Docker network
- Clean state between test runs

### Data Setup and Cleanup

**Automatic cleanup**: Test data is automatically cleaned up after each run.

**Manual cleanup** (if needed):
```bash
cd tests/e2e
node scripts/cleanup-test-data.js
```

**Custom test data**:
Modify `scripts/setup-test-data.js` to add specific test scenarios.

### Database Management

**View test database** (while tests are running):
- MongoDB Express: http://localhost:8081
- Database: `pathfinder_e2e_test`

**Reset database**:
```bash
cd tests/e2e
node scripts/mongodb-init.js
```

## Debugging and Troubleshooting

### Common Issues

1. **Port conflicts**:
   ```bash
   # Check what's using the ports
   lsof -i :3000,8000,27017,6379,8081,9080
   
   # Stop conflicting services or modify docker-compose.e2e.yml
   ```

2. **Services not starting**:
   ```bash
   # Check Docker logs
   docker-compose -f docker-compose.e2e.yml logs
   
   # Check specific service
   docker-compose -f docker-compose.e2e.yml logs backend
   ```

3. **Tests timing out**:
   - Increase timeouts in `playwright.config.ts`
   - Check service health with `node scripts/health-check.js`
   - Verify Docker resource allocation

4. **Database connection issues**:
   ```bash
   # Test MongoDB connectivity
   docker-compose -f docker-compose.e2e.yml exec mongodb mongosh --eval "db.adminCommand('ping')"
   ```

### Debug Mode

**Run tests with browser visible**:
```bash
cd tests/e2e
npx playwright test --debug --project=chromium
```

**Playwright Inspector**:
```bash
npx playwright test --debug auth/auth-flow.spec.ts
```

**Verbose logging**:
```bash
DEBUG=pw:api npx playwright test
```

### Test Reports

After running tests, reports are available at:
- HTML Report: `tests/e2e/playwright-report/index.html`
- JUnit XML: `tests/e2e/results.xml`
- Test artifacts: `tests/e2e/test-results/`

Open the HTML report:
```bash
npx playwright show-report
```

## Configuration

### Environment Variables

Key configuration options in `docker-compose.e2e.yml`:

- `MONGODB_URI`: Database connection string
- `REDIS_URL`: Cache connection string
- `NODE_ENV`: Set to `test` for E2E environment
- `AUTH_MOCK_ENABLED`: Enables mock authentication service

### Playwright Configuration

Main configuration in `tests/e2e/playwright.config.ts`:

- **Browsers**: Chromium, Firefox, Safari, Mobile
- **Timeouts**: Test and action timeouts
- **Retries**: Automatic retry on failure
- **Parallel execution**: Configurable worker count
- **Reporting**: Multiple report formats

### Custom Configuration

**Modify test timeouts**:
```typescript
// In playwright.config.ts
timeout: 60000, // 60 seconds per test
```

**Add new browsers**:
```typescript
// In playwright.config.ts
projects: [
  // Add Edge browser
  {
    name: 'msedge',
    use: { ...devices['Desktop Edge'] },
  },
]
```

## Extending the Test Suite

### Adding New Tests

1. **Create test file** in appropriate directory:
   ```bash
   touch tests/e2e/tests/new-feature/new-feature.spec.ts
   ```

2. **Use test helpers**:
   ```typescript
   import { test, expect } from '@playwright/test';
   import { TestHelpers } from '../../utils/test-helpers';
   
   test.describe('New Feature', () => {
     test('should work correctly', async ({ page }) => {
       const helpers = new TestHelpers(page);
       await helpers.login('testuser@example.com', 'password');
       // Your test logic here
     });
   });
   ```

3. **Update test data setup** if needed in `scripts/setup-test-data.js`

### Adding New Services

1. **Update `docker-compose.e2e.yml`** with new service
2. **Add health check** in `scripts/health-check.js`
3. **Update documentation**

### Custom Test Utilities

Add shared utilities to `utils/test-helpers.ts`:

```typescript
export class TestHelpers {
  async customAction() {
    // Implement reusable test actions
  }
}
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests
on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run E2E Tests
        run: |
          chmod +x scripts/run-e2e-tests.sh
          ./scripts/run-e2e-tests.sh
      - name: Upload Test Results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: tests/e2e/playwright-report/
```

### Azure DevOps Example

```yaml
- task: Bash@3
  displayName: 'Run E2E Tests'
  inputs:
    targetType: 'inline'
    script: |
      chmod +x scripts/run-e2e-tests.sh
      ./scripts/run-e2e-tests.sh

- task: PublishTestResults@2
  condition: always()
  inputs:
    testResultsFormat: 'JUnit'
    testResultsFiles: 'tests/e2e/results.xml'
```

## Performance Considerations

### Optimization Tips

1. **Parallel execution**: Configure worker count based on available resources
2. **Test data**: Use minimal test data sets
3. **Service startup**: Optimize Docker images for faster startup
4. **Network isolation**: Use Docker networks for better performance

### Resource Usage

- **Memory**: ~2-4GB during test execution
- **CPU**: Scales with worker count
- **Disk**: ~500MB for images and test artifacts
- **Network**: Isolated Docker network

## Best Practices

### Test Writing

1. **Independent tests**: Each test should be self-contained
2. **Clear naming**: Use descriptive test and suite names
3. **Proper cleanup**: Use test helpers for consistent cleanup
4. **Error handling**: Test both success and failure scenarios
5. **Performance**: Avoid unnecessary waits and operations

### Maintenance

1. **Regular updates**: Keep dependencies and browsers updated
2. **Test data**: Regularly review and clean test data
3. **Documentation**: Update this guide when adding features
4. **Monitoring**: Monitor test execution times and failure rates

### Development Workflow

1. **Local testing**: Run E2E tests before committing
2. **Feature testing**: Add E2E tests for new features
3. **Regression testing**: Ensure existing tests pass
4. **Code review**: Include E2E test changes in reviews

## Support and Troubleshooting

### Common Commands

```bash
# Full test run
./scripts/run-e2e-tests.sh

# Quick health check
cd tests/e2e && node scripts/health-check.js

# View logs
docker-compose -f docker-compose.e2e.yml logs

# Clean everything
docker-compose -f docker-compose.e2e.yml down -v
docker system prune -f
```

### Getting Help

1. Check this documentation
2. Review Playwright documentation: https://playwright.dev
3. Check Docker Compose logs for service issues
4. Verify system prerequisites and port availability

### Contributing

When contributing to the E2E test suite:

1. Follow existing test patterns
2. Add documentation for new features
3. Ensure tests are deterministic and reliable
4. Test your changes locally before submitting
5. Update this guide if adding new capabilities

## Appendix

### Service URLs (During E2E Testing)

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- MongoDB Express: http://localhost:8081
- Mock Auth: http://localhost:9080
- MongoDB: localhost:27017
- Redis: localhost:6379

### File Locations

- E2E Configuration: `tests/e2e/playwright.config.ts`
- Docker Compose: `docker-compose.e2e.yml`
- Test Scripts: `tests/e2e/scripts/`
- Test Utilities: `tests/e2e/utils/test-helpers.ts`
- Main E2E Script: `scripts/run-e2e-tests.sh`

### Dependencies

- **Playwright**: Browser automation and testing framework
- **Docker**: Container orchestration
- **MongoDB**: Document database for test data
- **Redis**: In-memory cache for session management
- **Node.js**: JavaScript runtime for test execution
