import React, { useState, useEffect } from 'react';
import {
  Card,
  CardHeader,
  Text,
  Button,
  Spinner,
  Badge,
  ProgressBar,
  MessageBar,
  makeStyles,
  tokens
} from '@fluentui/react-components';
import { 
  CheckmarkCircle20Regular,
  ErrorCircle20Regular,
  Warning20Regular,
  Money20Regular,
  Cloud20Regular
} from '@fluentui/react-icons';

const useStyles = makeStyles({
  dashboard: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: tokens.spacingVerticalL,
    padding: tokens.spacingVerticalL,
  },
  card: {
    minHeight: '200px',
  },
  healthCard: {
    gridColumn: 'span 2',
  },
  metric: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: tokens.spacingVerticalS,
  },
  metricValue: {
    fontSize: tokens.fontSizeBase400,
    fontWeight: tokens.fontWeightSemibold,
  },
  statusIcon: {
    marginRight: tokens.spacingHorizontalXS,
  },
  budgetProgress: {
    marginTop: tokens.spacingVerticalS,
  },
  suggestions: {
    display: 'flex',
    flexDirection: 'column',
    gap: tokens.spacingVerticalXS,
  },
  testResult: {
    marginTop: tokens.spacingVerticalS,
    padding: tokens.spacingVerticalS,
    borderRadius: tokens.borderRadiusMedium,
    backgroundColor: tokens.colorNeutralBackground2,
  }
});

interface LLMHealth {
  status: string;
  orchestration_service: {
    enabled: boolean;
    url: string | null;
    healthy: boolean;
    fallback_mode: boolean;
  };
  usage_stats: {
    today: {
      cost: number;
      requests: number;
    };
    budget_limit: number;
    budget_remaining: number;
  };
  services: {
    direct_openai: string;
    llm_orchestration: string;
  };
}

interface LLMAnalytics {
  orchestration_analytics: any;
  local_usage: any;
  optimization_suggestions: string[];
  summary: {
    total_requests: number;
    total_cost: number;
    budget_remaining: number;
    orchestration_enabled: boolean;
  };
}

interface BudgetStatus {
  orchestration_budget: any;
  local_budget: {
    daily_limit: number;
    daily_used: number;
    daily_remaining: number;
    requests_today: number;
  };
  recommendations: string[];
}

const LLMAnalyticsDashboard: React.FC = () => {
  const styles = useStyles();
  const [health, setHealth] = useState<LLMHealth | null>(null);
  const [analytics, setAnalytics] = useState<LLMAnalytics | null>(null);
  const [budget, setBudget] = useState<BudgetStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<any>(null);
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch health status
      const healthResponse = await fetch('/api/v1/llm/health', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      
      if (!healthResponse.ok) {
        throw new Error('Failed to fetch LLM health');
      }
      
      const healthData = await healthResponse.json();
      setHealth(healthData);

      // Fetch analytics
      const analyticsResponse = await fetch('/api/v1/llm/analytics', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      
      if (analyticsResponse.ok) {
        const analyticsData = await analyticsResponse.json();
        setAnalytics(analyticsData);
      }

      // Fetch budget status
      const budgetResponse = await fetch('/api/v1/llm/budget', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      
      if (budgetResponse.ok) {
        const budgetData = await budgetResponse.json();
        setBudget(budgetData);
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch LLM data');
    } finally {
      setLoading(false);
    }
  };

  const runTest = async () => {
    try {
      setTesting(true);
      setTestResult(null);

      const response = await fetch('/api/v1/llm/test-generation', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: 'Test LLM service health and responsiveness'
        }),
      });

      if (!response.ok) {
        throw new Error('Test request failed');
      }

      const result = await response.json();
      setTestResult(result);

    } catch (err) {
      setTestResult({
        success: false,
        error: err instanceof Error ? err.message : 'Test failed'
      });
    } finally {
      setTesting(false);
    }
  };

  const getStatusIcon = (status: string, healthy: boolean) => {
    if (status === 'healthy' && healthy) {
      return <CheckmarkCircle20Regular className={styles.statusIcon} style={{ color: tokens.colorPaletteGreenForeground1 }} />;
    } else if (status === 'degraded') {
      return <Warning20Regular className={styles.statusIcon} style={{ color: tokens.colorPaletteYellowForeground1 }} />;
    } else {
      return <ErrorCircle20Regular className={styles.statusIcon} style={{ color: tokens.colorPaletteRedForeground1 }} />;
    }
  };

  const getBudgetUsagePercentage = () => {
    if (!budget?.local_budget) return 0;
    const { daily_limit, daily_used } = budget.local_budget;
    return daily_limit > 0 ? (daily_used / daily_limit) * 100 : 0;
  };

  if (loading && !health) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <Spinner label="Loading LLM analytics..." />
      </div>
    );
  }

  if (error && !health) {
    return (
      <MessageBar intent="error">
        Failed to load LLM analytics: {error}
        <Button onClick={fetchData} appearance="subtle">Retry</Button>
      </MessageBar>
    );
  }

  return (
    <div className={styles.dashboard}>
      {/* Health Status Card */}
      <Card className={`${styles.card} ${styles.healthCard}`}>
        <CardHeader
          header={
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <Cloud20Regular style={{ marginRight: tokens.spacingHorizontalS }} />
              <Text weight="semibold">LLM Service Health</Text>
            </div>
          }
        />
        <div style={{ padding: tokens.spacingVerticalM }}>
          {health && (
            <>
              <div className={styles.metric}>
                <Text>Overall Status:</Text>
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  {getStatusIcon(health.status, health.orchestration_service.healthy)}
                  <Badge
                    appearance={health.status === 'healthy' ? 'filled' : 'outline'}
                    color={health.status === 'healthy' ? 'success' : health.status === 'degraded' ? 'warning' : 'danger'}
                  >
                    {health.status.toUpperCase()}
                  </Badge>
                </div>
              </div>
              
              <div className={styles.metric}>
                <Text>Orchestration Service:</Text>
                <Badge
                  appearance={health.orchestration_service.enabled ? 'filled' : 'outline'}
                  color={health.orchestration_service.enabled && health.orchestration_service.healthy ? 'success' : 'important'}
                >
                  {health.orchestration_service.enabled ? 
                    (health.orchestration_service.healthy ? 'ACTIVE' : 'DEGRADED') : 
                    'DISABLED'
                  }
                </Badge>
              </div>

              <div className={styles.metric}>
                <Text>Direct OpenAI:</Text>
                <Badge appearance="filled" color="success">
                  AVAILABLE
                </Badge>
              </div>

              {health.orchestration_service.fallback_mode && (
                <MessageBar intent="warning">
                  Running in fallback mode - using direct OpenAI API
                </MessageBar>
              )}

              <div style={{ marginTop: tokens.spacingVerticalM }}>
                <Button
                  appearance="primary"
                  onClick={runTest}
                  disabled={testing}
                  icon={testing ? <Spinner size="tiny" /> : undefined}
                >
                  {testing ? 'Testing...' : 'Run Service Test'}
                </Button>
              </div>

              {testResult && (
                <div className={styles.testResult}>
                  <Text weight="semibold">Test Result:</Text>
                  <Text block style={{ marginTop: tokens.spacingVerticalXS }}>
                    Service: {testResult.service_used || 'Unknown'}
                  </Text>
                  <Text block>
                    Status: {testResult.success ? '✅ Success' : '❌ Failed'}
                  </Text>
                  {testResult.error && (
                    <Text block style={{ color: tokens.colorPaletteRedForeground1 }}>
                      Error: {testResult.error}
                    </Text>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </Card>

      {/* Usage Statistics Card */}
      <Card className={styles.card}>
        <CardHeader
          header={
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <Money20Regular style={{ marginRight: tokens.spacingHorizontalS }} />
              <Text weight="semibold">Usage Statistics</Text>
            </div>
          }
        />
        <div style={{ padding: tokens.spacingVerticalM }}>
          {health && (
            <>
              <div className={styles.metric}>
                <Text>Requests Today:</Text>
                <Text className={styles.metricValue}>
                  {health.usage_stats.today.requests}
                </Text>
              </div>

              <div className={styles.metric}>
                <Text>Cost Today:</Text>
                <Text className={styles.metricValue}>
                  ${health.usage_stats.today.cost.toFixed(4)}
                </Text>
              </div>

              <div className={styles.metric}>
                <Text>Daily Budget:</Text>
                <Text className={styles.metricValue}>
                  ${health.usage_stats.budget_limit.toFixed(2)}
                </Text>
              </div>

              <div className={styles.metric}>
                <Text>Remaining:</Text>
                <Text 
                  className={styles.metricValue}
                  style={{ 
                    color: health.usage_stats.budget_remaining < health.usage_stats.budget_limit * 0.2 ? 
                      tokens.colorPaletteRedForeground1 : 
                      tokens.colorPaletteGreenForeground1 
                  }}
                >
                  ${health.usage_stats.budget_remaining.toFixed(4)}
                </Text>
              </div>
            </>
          )}
        </div>
      </Card>

      {/* Budget Status Card */}
      <Card className={styles.card}>
        <CardHeader
          header={
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <Money20Regular style={{ marginRight: tokens.spacingHorizontalS }} />
              <Text weight="semibold">Budget Status</Text>
            </div>
          }
        />
        <div style={{ padding: tokens.spacingVerticalM }}>
          {budget && (
            <>
              <div className={styles.budgetProgress}>
                <Text>Daily Budget Usage</Text>
                <ProgressBar 
                  value={getBudgetUsagePercentage()} 
                  max={100}
                  color={getBudgetUsagePercentage() > 80 ? 'error' : getBudgetUsagePercentage() > 60 ? 'warning' : 'success'}
                />
                <Text size={200}>
                  {getBudgetUsagePercentage().toFixed(1)}% used
                </Text>
              </div>

              {budget.recommendations && budget.recommendations.length > 0 && (
                <div style={{ marginTop: tokens.spacingVerticalM }}>
                  <Text weight="semibold">Recommendations:</Text>
                  <div className={styles.suggestions}>
                    {budget.recommendations.map((rec, index) => (
                      <MessageBar key={index} intent="info">
                        {rec}
                      </MessageBar>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </Card>

      {/* Analytics Summary Card */}
      {analytics && (
        <Card className={styles.card}>
          <CardHeader
            header={
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <Money20Regular style={{ marginRight: tokens.spacingHorizontalS }} />
                <Text weight="semibold">Analytics Summary</Text>
              </div>
            }
          />
          <div style={{ padding: tokens.spacingVerticalM }}>
            <div className={styles.metric}>
              <Text>Total Requests:</Text>
              <Text className={styles.metricValue}>
                {analytics.summary.total_requests}
              </Text>
            </div>

            <div className={styles.metric}>
              <Text>Total Cost:</Text>
              <Text className={styles.metricValue}>
                ${analytics.summary.total_cost.toFixed(4)}
              </Text>
            </div>

            <div className={styles.metric}>
              <Text>Orchestration:</Text>
              <Badge 
                appearance="filled" 
                color={analytics.summary.orchestration_enabled ? 'success' : 'important'}
              >
                {analytics.summary.orchestration_enabled ? 'ENABLED' : 'DISABLED'}
              </Badge>
            </div>

            {analytics.optimization_suggestions && analytics.optimization_suggestions.length > 0 && (
              <div style={{ marginTop: tokens.spacingVerticalM }}>
                <Text weight="semibold">Optimization Tips:</Text>
                <div className={styles.suggestions}>
                  {analytics.optimization_suggestions.map((suggestion, index) => (
                    <MessageBar key={index} intent="info">
                      {suggestion}
                    </MessageBar>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  );
};

export default LLMAnalyticsDashboard; 