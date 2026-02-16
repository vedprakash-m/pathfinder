/**
 * Universal Error Boundary Components for React
 * Implements standardized error boundary patterns from the tech debt remediation plan.
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { motion } from 'framer-motion';
import {
  Card,
  Button,
  Title1,
  Title2,
  Body1,
  Body2,
  MessageBar,
} from '@fluentui/react-components';
import {
  ExclamationTriangleIcon,
  ArrowPathIcon,
  HomeIcon,
  BugAntIcon,
} from '@heroicons/react/24/outline';
import { errorHandler } from '@/utils/errorHandler';

// ==================== ERROR BOUNDARY PROPS ====================
interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  level?: 'page' | 'component' | 'section';
  showDetails?: boolean;
  allowRetry?: boolean;
  context?: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorId?: string;
  retryCount: number;
}

// ==================== MAIN ERROR BOUNDARY ====================
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private maxRetries = 3;

  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      retryCount: 0,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
      errorId: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Handle the error with our unified error handler
    const handledError = errorHandler.handle(error, {
      context: {
        ...errorInfo,
        boundary: this.props.context || 'ErrorBoundary',
        level: this.props.level || 'component',
      },
      showToast: false, // Don't show toast since we have UI feedback
      logToConsole: true,
      reportToService: true,
    });

    // Call custom error handler if provided
    this.props.onError?.(error, errorInfo);

    // Log error details for debugging
    console.group(`🚨 Error Boundary Caught Error (${this.props.level || 'component'})`);
    console.error('Error:', error);
    console.error('Component Stack:', errorInfo.componentStack);
    console.error('Handled Error:', handledError);
    console.groupEnd();
  }

  handleRetry = () => {
    if (this.state.retryCount < this.maxRetries) {
      this.setState(prevState => ({
        hasError: false,
        error: undefined,
        errorId: undefined,
        retryCount: prevState.retryCount + 1,
      }));
    }
  };

  handleReset = () => {
    this.setState({
      hasError: false,
      error: undefined,
      errorId: undefined,
      retryCount: 0,
    });
  };

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Render appropriate error UI based on level
      switch (this.props.level) {
        case 'page':
          return <PageErrorFallback {...this.getErrorProps()} />;
        case 'section':
          return <SectionErrorFallback {...this.getErrorProps()} />;
        case 'component':
        default:
          return <ComponentErrorFallback {...this.getErrorProps()} />;
      }
    }

    return this.props.children;
  }

  private getErrorProps() {
    return {
      error: this.state.error,
      errorId: this.state.errorId,
      retryCount: this.state.retryCount,
      maxRetries: this.maxRetries,
      onRetry: this.handleRetry,
      onReset: this.handleReset,
      showDetails: this.props.showDetails,
      allowRetry: this.props.allowRetry !== false,
    };
  }
}

// ==================== ERROR FALLBACK COMPONENTS ====================
interface ErrorFallbackProps {
  error?: Error;
  errorId?: string;
  retryCount: number;
  maxRetries: number;
  onRetry: () => void;
  onReset: () => void;
  showDetails?: boolean;
  allowRetry?: boolean;
}

// Page-level error fallback (full page error)
const PageErrorFallback: React.FC<ErrorFallbackProps> = ({
  error,
  errorId,
  retryCount,
  maxRetries,
  onRetry,
  onReset,
  showDetails,
  allowRetry,
}) => (
  <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50 flex items-center justify-center p-4">
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className="max-w-lg w-full"
    >
      <Card className="p-8">
        <div className="text-center">
          {/* Error Icon */}
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.1, type: 'spring', stiffness: 200 }}
            className="w-16 h-16 bg-red-100 rounded-full mx-auto mb-6 flex items-center justify-center"
          >
            <ExclamationTriangleIcon className="w-8 h-8 text-red-600" />
          </motion.div>

          {/* Error Content */}
          <Title1 className="text-gray-900 mb-4">Oops! Something went wrong</Title1>
          <Body1 className="text-gray-600 mb-6">
            We're sorry, but something unexpected happened. Our team has been notified and we're working on a fix.
          </Body1>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3 justify-center mb-6">
            {allowRetry && retryCount < maxRetries && (
              <Button
                appearance="primary"
                icon={<ArrowPathIcon className="w-4 h-4" />}
                onClick={onRetry}
              >
                Try Again ({maxRetries - retryCount} left)
              </Button>
            )}

            <Button
              appearance="outline"
              icon={<HomeIcon className="w-4 h-4" />}
              onClick={() => window.location.href = '/'}
            >
              Go Home
            </Button>

            <Button
              appearance="subtle"
              icon={<ArrowPathIcon className="w-4 h-4" />}
              onClick={onReset}
            >
              Reset
            </Button>
          </div>

          {/* Error Details (Debug Mode) */}
          {showDetails && error && (
            <details className="text-left">
              <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700 mb-2">
                Show Technical Details
              </summary>
              <div className="bg-gray-50 p-4 rounded-lg text-xs font-mono">
                <div className="mb-2">
                  <strong>Error ID:</strong> {errorId}
                </div>
                <div className="mb-2">
                  <strong>Message:</strong> {error.message}
                </div>
                {error.stack && (
                  <div>
                    <strong>Stack Trace:</strong>
                    <pre className="mt-1 whitespace-pre-wrap">{error.stack}</pre>
                  </div>
                )}
              </div>
            </details>
          )}
        </div>
      </Card>
    </motion.div>
  </div>
);

// Section-level error fallback (part of page)
const SectionErrorFallback: React.FC<ErrorFallbackProps> = ({
  error,
  errorId,
  retryCount,
  maxRetries,
  onRetry,
  onReset,
  showDetails,
  allowRetry,
}) => (
  <Card className="p-6 my-4 border-l-4 border-l-orange-400">
    <div className="flex items-start gap-4">
      <div className="flex-shrink-0">
        <ExclamationTriangleIcon className="w-6 h-6 text-orange-600" />
      </div>

      <div className="flex-1">
        <Title2 className="text-gray-900 mb-2">Section Error</Title2>
        <Body2 className="text-gray-600 mb-4">
          This section couldn't load properly. You can try refreshing it or continue using other parts of the page.
        </Body2>

        <div className="flex gap-2">
          {allowRetry && retryCount < maxRetries && (
            <Button
              size="small"
              appearance="primary"
              icon={<ArrowPathIcon className="w-4 h-4" />}
              onClick={onRetry}
            >
              Retry
            </Button>
          )}

          <Button
            size="small"
            appearance="subtle"
            onClick={onReset}
          >
            Reset Section
          </Button>
        </div>

        {showDetails && error && (
          <details className="mt-4">
            <summary className="cursor-pointer text-xs text-gray-500 hover:text-gray-700">
              Technical Details
            </summary>
            <div className="mt-2 bg-gray-50 p-3 rounded text-xs">
              <div><strong>ID:</strong> {errorId}</div>
              <div><strong>Error:</strong> {error.message}</div>
            </div>
          </details>
        )}
      </div>
    </div>
  </Card>
);

// Component-level error fallback (inline error)
const ComponentErrorFallback: React.FC<ErrorFallbackProps> = ({
  retryCount,
  maxRetries,
  onRetry,
  allowRetry,
}) => (
  <div className="p-4 border border-red-200 bg-red-50 rounded-lg">
    <div className="flex items-center gap-3">
      <BugAntIcon className="w-5 h-5 text-red-600" />
      <div className="flex-1">
        <Body2 className="text-red-800">Component failed to load</Body2>
      </div>
      {allowRetry && retryCount < maxRetries && (
        <Button
          size="small"
          appearance="outline"
          icon={<ArrowPathIcon className="w-4 h-4" />}
          onClick={onRetry}
        >
          Retry
        </Button>
      )}
    </div>
  </div>
);

// ==================== SPECIALIZED ERROR BOUNDARIES ====================

// API Error Boundary for API-related errors
export const ApiErrorBoundary: React.FC<Omit<ErrorBoundaryProps, 'level'>> = (props) => (
  <ErrorBoundary {...props} level="section" context="API" />
);

// Route Error Boundary for page-level routing errors
export const RouteErrorBoundary: React.FC<Omit<ErrorBoundaryProps, 'level'>> = (props) => (
  <ErrorBoundary {...props} level="page" context="Route" />
);

// Form Error Boundary for form-related errors
export const FormErrorBoundary: React.FC<Omit<ErrorBoundaryProps, 'level'>> = (props) => (
  <ErrorBoundary {...props} level="component" context="Form" />
);

// ==================== HOC FOR ERROR BOUNDARIES ====================
export const withErrorBoundary = <P extends object>(
  WrappedComponent: React.ComponentType<P>,
  errorBoundaryProps?: Partial<ErrorBoundaryProps>
) => {
  const WithErrorBoundaryComponent = (props: P) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <WrappedComponent {...props} />
    </ErrorBoundary>
  );

  WithErrorBoundaryComponent.displayName = `withErrorBoundary(${WrappedComponent.displayName || WrappedComponent.name})`;

  return WithErrorBoundaryComponent;
};

// ==================== HOOKS ====================

// Hook for manual error reporting
export const useErrorHandler = () => {
  const reportError = (error: Error, context?: Record<string, unknown>) => {
    errorHandler.handle(error, {
      context,
      showToast: true,
      logToConsole: true,
      reportToService: true,
    });
  };

  const reportAsyncError = async <T,>(
    operation: () => Promise<T>,
    context?: Record<string, unknown>
  ): Promise<{ data: T | null; error: Error | null }> => {
    try {
      const data = await operation();
      return { data, error: null };
    } catch (error) {
      reportError(error as Error, context);
      return { data: null, error: error as Error };
    }
  };

  return { reportError, reportAsyncError };
};

// Hook for error statistics
export const useErrorStats = () => {
  const getStats = () => errorHandler.getErrorStats();
  const getRecentErrors = (limit?: number) => errorHandler.getRecentErrors(limit);
  const clearLog = () => errorHandler.clearLog();

  return { getStats, getRecentErrors, clearLog };
};

// ==================== UTILITIES ====================

// Create a timeout-aware error boundary component
export const WithTimeoutComponent: React.FC<{
  component: ReactNode;
  timeoutMs?: number;
  fallback?: ReactNode;
}> = ({ component, timeoutMs = 10000, fallback }) => {
  const [hasTimedOut, setHasTimedOut] = React.useState(false);

  React.useEffect(() => {
    const timer = setTimeout(() => {
      setHasTimedOut(true);
    }, timeoutMs);

    return () => clearTimeout(timer);
  }, [timeoutMs]);

  if (hasTimedOut) {
    return fallback || (
      <MessageBar intent="warning">
        This component is taking longer than expected to load.
      </MessageBar>
    );
  }

  return <ErrorBoundary level="component">{component}</ErrorBoundary>;
};
