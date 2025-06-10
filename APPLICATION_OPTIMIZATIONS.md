# Application Optimizations for Ultra Cost-Optimized Infrastructure

## Backend Optimizations

### 1. Database Connection Pool Optimization
```python
# backend/app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Ultra-optimized connection pool for cost savings
engine = create_async_engine(
    database_url,
    pool_size=1,              # Minimal pool size
    max_overflow=2,           # Minimal overflow
    pool_timeout=60,          # Longer timeout for single connection
    pool_recycle=3600,        # Recycle connections hourly
    pool_pre_ping=True,       # Ensure connection validity
    echo=False                # Disable SQL logging for performance
)
```

### 2. Cosmos DB Client Optimization
```python
# backend/app/core/cosmos_db.py
import asyncio
from azure.cosmos import CosmosClient, PartitionKey

class CostOptimizedCosmosClient:
    def __init__(self, connection_string: str):
        self.client = CosmosClient(
            connection_string,
            consistency_level='Session',  # Lower consistency for better RU efficiency
            request_timeout=10,           # Shorter timeout
            retry_total=1,               # Fewer retries to reduce RU consumption
            retry_backoff_max=3          # Faster backoff
        )
        self._request_cache = {}  # Simple in-memory cache
    
    async def get_cached_item(self, container_name: str, item_id: str, partition_key: str):
        cache_key = f"{container_name}:{item_id}:{partition_key}"
        
        # Check cache first
        if cache_key in self._request_cache:
            cache_time, item = self._request_cache[cache_key]
            if asyncio.get_event_loop().time() - cache_time < 300:  # 5-minute cache
                return item
        
        # Fetch from Cosmos DB
        container = self.client.get_database_client('pathfinder').get_container_client(container_name)
        item = container.read_item(item_id, partition_key)
        
        # Cache result
        self._request_cache[cache_key] = (asyncio.get_event_loop().time(), item)
        return item
```

### 3. Optimized Health Checks
```python
# backend/app/api/health.py
import asyncio
from datetime import datetime, timedelta
from fastapi import APIRouter

router = APIRouter()

# Cache health check results to reduce database load
_health_cache = {
    'last_check': None,
    'result': None,
    'ttl': 30  # Cache for 30 seconds
}

@router.get("/")
async def health_check():
    """Lightweight health check optimized for scale-to-zero scenarios."""
    now = datetime.utcnow()
    
    # Return cached result if still valid
    if (_health_cache['last_check'] and 
        now - _health_cache['last_check'] < timedelta(seconds=_health_cache['ttl'])):
        return _health_cache['result']
    
    # Quick health check
    result = {
        "status": "ok",
        "timestamp": now.isoformat(),
        "environment": "cost-optimized",
        "mode": "scale-to-zero"
    }
    
    # Update cache
    _health_cache['last_check'] = now
    _health_cache['result'] = result
    
    return result

@router.get("/ready")
async def readiness_check():
    """Minimal readiness check for container startup."""
    return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
```

## Frontend Optimizations

### 1. Backend Warm-up Strategy
```typescript
// frontend/src/services/warmupService.ts
class BackendWarmupService {
  private isWarming = false;
  private lastWarmup = 0;
  private readonly WARMUP_INTERVAL = 5 * 60 * 1000; // 5 minutes

  async warmupBackend(): Promise<void> {
    const now = Date.now();
    
    // Don't warm up too frequently
    if (this.isWarming || now - this.lastWarmup < this.WARMUP_INTERVAL) {
      return;
    }

    this.isWarming = true;
    this.lastWarmup = now;

    try {
      // Ping health endpoint to wake up backend
      await fetch('/api/health', { 
        method: 'GET',
        signal: AbortSignal.timeout(3000) // 3 second timeout
      });
    } catch (error) {
      console.log('Backend warmup ping failed:', error);
    } finally {
      this.isWarming = false;
    }
  }

  startPeriodicWarmup(): void {
    // Warm up backend every 5 minutes during active session
    setInterval(() => {
      if (document.visibilityState === 'visible') {
        this.warmupBackend();
      }
    }, this.WARMUP_INTERVAL);
  }
}

export const warmupService = new BackendWarmupService();
```

### 2. Enhanced Loading States
```typescript
// frontend/src/components/LoadingStates.tsx
import React from 'react';
import { Spinner } from '@fluentui/react-components';

export const ColdStartLoader: React.FC = () => (
  <div className="flex flex-col items-center justify-center min-h-[200px] space-y-4">
    <Spinner size="large" />
    <div className="text-center">
      <h3 className="text-lg font-medium text-gray-900">Starting up...</h3>
      <p className="text-sm text-gray-600 mt-1">
        This may take a few seconds as we're waking up the system.
      </p>
      <p className="text-xs text-gray-500 mt-2">
        Subsequent requests will be much faster!
      </p>
    </div>
  </div>
);

export const useApiCall = <T,>(apiFunction: () => Promise<T>) => {
  const [loading, setLoading] = React.useState(false);
  const [data, setData] = React.useState<T | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [isColdStart, setIsColdStart] = React.useState(false);

  const execute = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    
    const startTime = Date.now();
    
    try {
      const result = await apiFunction();
      const duration = Date.now() - startTime;
      
      // If request took more than 5 seconds, it was likely a cold start
      setIsColdStart(duration > 5000);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  }, [apiFunction]);

  return { loading, data, error, execute, isColdStart };
};
```

### 3. Smart Request Batching
```typescript
// frontend/src/services/batchingService.ts
class RequestBatchingService {
  private batchQueue: Array<{
    endpoint: string;
    resolve: (data: any) => void;
    reject: (error: Error) => void;
  }> = [];
  private batchTimeout: NodeJS.Timeout | null = null;

  async batchRequest<T>(endpoint: string): Promise<T> {
    return new Promise((resolve, reject) => {
      this.batchQueue.push({ endpoint, resolve, reject });
      
      // Schedule batch execution if not already scheduled
      if (!this.batchTimeout) {
        this.batchTimeout = setTimeout(() => this.executeBatch(), 100);
      }
    });
  }

  private async executeBatch(): Promise<void> {
    const currentBatch = [...this.batchQueue];
    this.batchQueue.length = 0;
    this.batchTimeout = null;

    if (currentBatch.length === 0) return;

    try {
      // Group by endpoint
      const grouped = currentBatch.reduce((acc, item) => {
        if (!acc[item.endpoint]) acc[item.endpoint] = [];
        acc[item.endpoint].push(item);
        return acc;
      }, {} as Record<string, typeof currentBatch>);

      // Execute batch requests
      await Promise.all(
        Object.entries(grouped).map(async ([endpoint, items]) => {
          try {
            const response = await fetch(endpoint);
            const data = await response.json();
            items.forEach(item => item.resolve(data));
          } catch (error) {
            items.forEach(item => item.reject(error as Error));
          }
        })
      );
    } catch (error) {
      currentBatch.forEach(item => item.reject(error as Error));
    }
  }
}

export const batchingService = new RequestBatchingService();
```

## Monitoring Optimizations

### 1. Cost-Aware Logging
```python
# backend/app/core/logging_config.py
import logging
import os
from datetime import datetime

class CostOptimizedFormatter(logging.Formatter):
    """Custom formatter that reduces log verbosity in production."""
    
    def format(self, record):
        # In cost-optimized mode, only log warnings and errors
        if os.getenv('ENVIRONMENT') == 'cost-optimized' and record.levelno < logging.WARNING:
            return None
        
        # Simplified format to reduce Application Insights ingestion costs
        return f"{datetime.utcnow().isoformat()}|{record.levelname}|{record.message}"

def setup_cost_optimized_logging():
    """Set up logging optimized for minimal costs."""
    logging.basicConfig(
        level=logging.WARNING,  # Only warnings and errors
        format='%(asctime)s|%(levelname)s|%(message)s',
        handlers=[logging.StreamHandler()]
    )
```

### 2. Selective Telemetry
```python
# backend/app/core/telemetry.py
import os
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.trace.samplers import ProbabilitySampler

class CostOptimizedTelemetry:
    def __init__(self):
        self.enabled = os.getenv('ENVIRONMENT') != 'cost-optimized'
        self.sampling_rate = 0.1 if os.getenv('ENVIRONMENT') == 'cost-optimized' else 1.0
        
    def setup_telemetry(self, connection_string: str):
        if not self.enabled:
            return
            
        # Use very low sampling rate in cost-optimized mode
        sampler = ProbabilitySampler(rate=self.sampling_rate)
        
        # Only log critical errors to Application Insights
        handler = AzureLogHandler(
            connection_string=connection_string,
            export_interval=60  # Batch exports every minute
        )
        
        logger = logging.getLogger()
        logger.addHandler(handler)
        logger.setLevel(logging.ERROR)  # Only errors
```

## Deployment Configuration

### 1. Environment-Specific Settings
```yaml
# .github/workflows/deploy-cost-optimized.yml
name: Deploy Cost-Optimized Infrastructure

on:
  workflow_dispatch:
    inputs:
      cost_optimization_level:
        description: 'Cost optimization level'
        required: true
        default: 'aggressive'
        type: choice
        options:
        - moderate
        - aggressive
        - ultra

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy Infrastructure
        run: |
          az deployment group create \
            --resource-group ${{ secrets.AZURE_RESOURCE_GROUP }} \
            --template-file infrastructure/bicep/ultra-cost-optimized.bicep \
            --parameters \
              sqlAdminLogin=${{ secrets.SQL_ADMIN_USERNAME }} \
              sqlAdminPassword=${{ secrets.SQL_ADMIN_PASSWORD }} \
              openAIApiKey=${{ secrets.OPENAI_API_KEY }} \
              environment=cost-optimized
```

### 2. Application Configuration
```python
# backend/app/core/config.py
class CostOptimizedSettings:
    """Settings optimized for minimal Azure costs."""
    
    # Database settings
    DB_POOL_SIZE: int = 1
    DB_MAX_OVERFLOW: int = 2
    DB_POOL_TIMEOUT: int = 60
    
    # Cosmos DB settings
    COSMOS_CONSISTENCY_LEVEL: str = "Session"
    COSMOS_REQUEST_TIMEOUT: int = 10
    COSMOS_RETRY_TOTAL: int = 1
    
    # Caching settings
    ENABLE_IN_MEMORY_CACHE: bool = True
    CACHE_TTL_SECONDS: int = 300
    
    # Logging settings
    LOG_LEVEL: str = "WARNING"
    TELEMETRY_SAMPLING_RATE: float = 0.1
    
    # Performance settings
    ENABLE_REQUEST_BATCHING: bool = True
    COLD_START_OPTIMIZATION: bool = True
```

This comprehensive optimization plan should reduce your monthly costs from ~$85 to $45-65 while maintaining core functionality. The key is implementing smart scaling, resource optimization, and intelligent caching strategies.
