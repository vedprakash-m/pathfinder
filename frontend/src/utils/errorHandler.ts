/**
 * Unified Error Handling System for Pathfinder Frontend
 * Implements standardized error handling patterns from the tech debt remediation plan.
 * Enhanced with correlation IDs, retry logic, and comprehensive error classification.
 */

import React from 'react';
import { toast } from 'react-hot-toast';

// ==================== UTILITY FUNCTIONS ====================
function generateCorrelationId(): string {
  return `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// ==================== ENHANCED ERROR TYPES ====================
export enum ErrorType {
  NETWORK = 'network',
  AUTH = 'auth',
  VALIDATION = 'validation',
  SERVER = 'server',
  CLIENT = 'client',
  PERMISSION = 'permission',
  RATE_LIMIT = 'rate_limit',
  UNKNOWN = 'unknown'
}

export enum ErrorSeverity {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL',
}

export interface StandardError {
  type: ErrorType;
  severity: ErrorSeverity;
  message: string;
  details?: string;
  code?: string | number;
  statusCode?: number;
  timestamp: Date;
  context?: Record<string, unknown>;
  recoverable: boolean;
  retryable: boolean;
  userFriendlyMessage: string;
  correlationId: string;
  originalError?: Error;
}

export interface ErrorHandlerOptions {
  showToast?: boolean;
  logToConsole?: boolean;
  reportToService?: boolean;
  context?: Record<string, unknown>;
  fallbackMessage?: string;
  onRetry?: () => void;
  onRecover?: () => void;
}

export interface RetryOptions {
  maxRetries?: number;
  baseDelay?: number;
  maxDelay?: number;
  backoffMultiplier?: number;
  retryCondition?: (error: StandardError, attempt: number) => boolean;
  onRetry?: (error: StandardError, attempt: number) => void;
}

// Helper type for error-like objects
interface ErrorLike {
  message?: string;
  code?: string;
  name?: string;
  stack?: string;
  status?: number;
  response?: {
    status?: number;
    data?: { message?: string };
  };
  config?: {
    url?: string;
  };
}

function isErrorLike(error: unknown): error is ErrorLike {
  return typeof error === 'object' && error !== null;
}

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  if (isErrorLike(error) && error.message) return error.message;
  return 'Unknown error';
}

function getStatusCode(error: unknown): number | undefined {
  if (isErrorLike(error)) {
    return error.response?.status ?? error.status;
  }
  return undefined;
}

// ==================== ENHANCED ERROR CLASSIFICATION ====================
class ErrorClassifier {
  static classifyError(error: unknown, context?: Record<string, unknown>): StandardError {
    const correlationId = generateCorrelationId();
    const timestamp = new Date();
    const errLike = isErrorLike(error) ? error : null;
    const statusCode = getStatusCode(error);
    const message = getErrorMessage(error);

    // Network errors
    if (this.isNetworkError(error)) {
      return {
        type: ErrorType.NETWORK,
        severity: ErrorSeverity.MEDIUM,
        message: message || 'Network request failed',
        code: errLike?.code || 'NETWORK_ERROR',
        statusCode,
        timestamp,
        context,
        recoverable: true,
        retryable: true,
        userFriendlyMessage: navigator.onLine ?
          'Network request failed. Please try again.' :
          'No internet connection. Please check your connection.',
        correlationId,
        originalError: error instanceof Error ? error : undefined
      };
    }

    // Authentication errors
    if (this.isAuthError(error)) {
      return {
        type: ErrorType.AUTH,
        severity: ErrorSeverity.HIGH,
        message: message || (statusCode === 401 ? 'Authentication required' : 'Access denied'),
        code: statusCode === 401 ? 'UNAUTHORIZED' : 'FORBIDDEN',
        statusCode,
        timestamp,
        context,
        recoverable: statusCode === 401,
        retryable: false,
        userFriendlyMessage: statusCode === 401 ?
          'Please sign in to continue.' :
          'You don\'t have permission to access this resource.',
        correlationId,
        originalError: error instanceof Error ? error : undefined
      };
    }

    // Validation errors
    if (this.isValidationError(error)) {
      return {
        type: ErrorType.VALIDATION,
        severity: ErrorSeverity.LOW,
        message: errLike?.response?.data?.message || message || 'Validation failed',
        code: 'VALIDATION_ERROR',
        statusCode,
        timestamp,
        context,
        recoverable: true,
        retryable: false,
        userFriendlyMessage: 'Please check your input and try again.',
        correlationId,
        originalError: error instanceof Error ? error : undefined
      };
    }

    // Server errors
    if (this.isServerError(error)) {
      const errObj = error as { response?: { status?: number }; status?: number };
      return {
        type: ErrorType.SERVER,
        severity: ErrorSeverity.HIGH,
        message: message || 'Server error occurred',
        code: 'SERVER_ERROR',
        statusCode: errObj?.response?.status || errObj?.status,
        timestamp,
        context,
        recoverable: true,
        retryable: true,
        userFriendlyMessage: 'Server error. Please try again in a moment.',
        correlationId,
        originalError: error instanceof Error ? error : undefined
      };
    }

    // Permission errors
    if (this.isPermissionError(error)) {
      return {
        type: ErrorType.PERMISSION,
        severity: ErrorSeverity.MEDIUM,
        message: message || 'Insufficient permissions',
        code: 'PERMISSION_DENIED',
        timestamp,
        context,
        recoverable: false,
        retryable: false,
        userFriendlyMessage: 'You don\'t have permission to perform this action.',
        correlationId,
        originalError: error instanceof Error ? error : undefined
      };
    }

    // Rate limit errors
    if (this.isRateLimitError(error)) {
      return {
        type: ErrorType.RATE_LIMIT,
        severity: ErrorSeverity.MEDIUM,
        message: 'Rate limit exceeded',
        code: 'RATE_LIMIT_EXCEEDED',
        statusCode: 429,
        timestamp,
        context,
        recoverable: true,
        retryable: true,
        userFriendlyMessage: 'Too many requests. Please wait a moment and try again.',
        correlationId,
        originalError: error instanceof Error ? error : undefined
      };
    }

    // Default unknown error
    return {
      type: ErrorType.UNKNOWN,
      severity: ErrorSeverity.MEDIUM,
      message: message || 'An unexpected error occurred',
      code: 'UNKNOWN_ERROR',
      timestamp,
      context,
      recoverable: false,
      retryable: false,
      userFriendlyMessage: 'Something went wrong. Please try again.',
      correlationId,
      originalError: error instanceof Error ? error : undefined
    };
  }

  private static isNetworkError(error: unknown): boolean {
    const errLike = isErrorLike(error) ? error : null;
    return (
      errLike?.code === 'NETWORK_ERROR' ||
      errLike?.message?.includes('Network Error') ||
      errLike?.message?.includes('Failed to fetch') ||
      errLike?.name === 'NetworkError' ||
      !navigator.onLine
    );
  }

  private static isAuthError(error: unknown): boolean {
    const statusCode = getStatusCode(error);
    const errLike = isErrorLike(error) ? error : null;
    return statusCode === 401 || statusCode === 403 || errLike?.code === 'AUTH_ERROR';
  }

  private static isValidationError(error: unknown): boolean {
    const statusCode = getStatusCode(error);
    const errLike = isErrorLike(error) ? error : null;
    return statusCode === 400 || statusCode === 422 || errLike?.code === 'VALIDATION_ERROR';
  }

  private static isServerError(error: unknown): boolean {
    const statusCode = getStatusCode(error);
    return statusCode !== undefined && statusCode >= 500 && statusCode < 600;
  }

  private static isPermissionError(error: unknown): boolean {
    const errLike = isErrorLike(error) ? error : null;
    return errLike?.code === 'PERMISSION_DENIED' || errLike?.message?.includes('permission') === true;
  }

  private static isRateLimitError(error: unknown): boolean {
    const statusCode = getStatusCode(error);
    const errLike = isErrorLike(error) ? error : null;
    return statusCode === 429 || errLike?.code === 'RATE_LIMIT_EXCEEDED';
  }
}

// ==================== ERROR HANDLER CLASS ====================
export class ErrorHandler {
  private static instance: ErrorHandler;
  private errorLog: StandardError[] = [];
  private maxLogSize = 100;

  private constructor() {}

  static getInstance(): ErrorHandler {
    if (!ErrorHandler.instance) {
      ErrorHandler.instance = new ErrorHandler();
    }
    return ErrorHandler.instance;
  }

  /**
   * Handle an error with unified processing
   */
  handle(error: unknown, options: ErrorHandlerOptions = {}): StandardError {
    const classified = ErrorClassifier.classifyError(error);

    const errLike = typeof error === 'object' && error !== null ? error as ErrorLike : null;
    const standardError: StandardError = {
      type: classified.type || ErrorType.UNKNOWN,
      severity: classified.severity || ErrorSeverity.MEDIUM,
      message: classified.message || getErrorMessage(error),
      details: this.extractErrorDetails(error),
      code: errLike?.code || errLike?.status,
      timestamp: new Date(),
      context: options.context,
      recoverable: classified.recoverable ?? true,
      retryable: classified.retryable ?? true,
      userFriendlyMessage: classified.userFriendlyMessage || options.fallbackMessage || 'An error occurred',
      correlationId: classified.correlationId || generateCorrelationId(),
    };

    // Add to error log
    this.addToLog(standardError);

    // Execute handling actions
    if (options.showToast !== false) {
      this.showToast(standardError);
    }

    if (options.logToConsole !== false) {
      this.logToConsole(standardError);
    }

    if (options.reportToService) {
      this.reportToService(standardError);
    }

    return standardError;
  }

  /**
   * Handle async operations with error handling
   */
  async handleAsync<T>(
    operation: () => Promise<T>,
    options: ErrorHandlerOptions = {}
  ): Promise<{ data: T | null; error: StandardError | null }> {
    try {
      const data = await operation();
      return { data, error: null };
    } catch (error) {
      const handledError = this.handle(error, options);
      return { data: null, error: handledError };
    }
  }

  /**
   * Create a retry wrapper for operations
   */
  withRetry<T>(
    operation: () => Promise<T>,
    maxRetries: number = 3,
    delayMs: number = 1000
  ) {
    return async (options: ErrorHandlerOptions = {}): Promise<T> => {
      let lastError: unknown;

      for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
          return await operation();
        } catch (error) {
          lastError = error;

          if (attempt === maxRetries) {
            throw this.handle(error, options);
          }

          const classified = ErrorClassifier.classifyError(error);
          if (!classified.retryable) {
            throw this.handle(error, options);
          }

          // Wait before retry
          await new Promise(resolve => setTimeout(resolve, delayMs * Math.pow(2, attempt)));
        }
      }

      throw lastError as Error;
    };
  }

  /**
   * Get recent errors for debugging
   */
  getRecentErrors(limit: number = 10): StandardError[] {
    return this.errorLog.slice(-limit);
  }

  /**
   * Clear error log
   */
  clearLog(): void {
    this.errorLog = [];
  }

  /**
   * Get error statistics
   */
  getErrorStats(): Record<string, number> {
    const stats: Record<string, number> = {};

    for (const error of this.errorLog) {
      const key = `${error.type}_${error.severity}`;
      stats[key] = (stats[key] || 0) + 1;
    }

    return stats;
  }

  // ==================== PRIVATE METHODS ====================
  private extractErrorDetails(error: unknown): string {
    const details: string[] = [];
    const errLike = typeof error === 'object' && error !== null ? error as ErrorLike : null;

    if (errLike?.stack) {
      details.push(`Stack: ${errLike.stack.split('\n')[0]}`);
    }

    if (errLike?.response?.data) {
      details.push(`Response: ${JSON.stringify(errLike.response.data).substring(0, 200)}`);
    }

    if (errLike?.config?.url) {
      details.push(`URL: ${errLike.config.url}`);
    }

    return details.join(' | ');
  }

  private addToLog(error: StandardError): void {
    this.errorLog.push(error);

    // Maintain log size limit
    if (this.errorLog.length > this.maxLogSize) {
      this.errorLog = this.errorLog.slice(-this.maxLogSize);
    }
  }

  private showToast(error: StandardError): void {
    const toastOptions = {
      duration: this.getToastDuration(error.severity),
      style: this.getToastStyle(error.severity),
    };

    switch (error.severity) {
      case ErrorSeverity.LOW:
        toast(error.userFriendlyMessage, toastOptions);
        break;
      case ErrorSeverity.MEDIUM:
        toast.error(error.userFriendlyMessage, toastOptions);
        break;
      case ErrorSeverity.HIGH:
      case ErrorSeverity.CRITICAL:
        toast.error(error.userFriendlyMessage, {
          ...toastOptions,
          duration: Infinity, // Require manual dismissal
        });
        break;
    }
  }

  private logToConsole(error: StandardError): void {
    const logData = {
      ...error,
      timestamp: error.timestamp.toISOString(),
    };

    switch (error.severity) {
      case ErrorSeverity.LOW:
        console.info('🔵 Error (Low):', logData);
        break;
      case ErrorSeverity.MEDIUM:
        console.warn('🟡 Error (Medium):', logData);
        break;
      case ErrorSeverity.HIGH:
        console.error('🔴 Error (High):', logData);
        break;
      case ErrorSeverity.CRITICAL:
        console.error('💀 Error (Critical):', logData);
        break;
    }
  }

  private async reportToService(error: StandardError): Promise<void> {
    try {
      // In a real implementation, this would send to an error reporting service
      // For now, we'll just log that we would report it
      console.info('📊 Would report error to service:', {
        type: error.type,
        severity: error.severity,
        message: error.message,
        timestamp: error.timestamp,
      });
    } catch (reportingError) {
      console.error('Failed to report error:', reportingError);
    }
  }

  private getToastDuration(severity: ErrorSeverity): number {
    switch (severity) {
      case ErrorSeverity.LOW:
        return 3000;
      case ErrorSeverity.MEDIUM:
        return 5000;
      case ErrorSeverity.HIGH:
        return 8000;
      case ErrorSeverity.CRITICAL:
        return 0; // Manual dismissal
      default:
        return 4000;
    }
  }

  private getToastStyle(severity: ErrorSeverity): Record<string, string> {
    const baseStyle = {
      borderRadius: '8px',
      fontSize: '14px',
    };

    switch (severity) {
      case ErrorSeverity.LOW:
        return { ...baseStyle, background: '#3b82f6', color: 'white' };
      case ErrorSeverity.MEDIUM:
        return { ...baseStyle, background: '#f59e0b', color: 'white' };
      case ErrorSeverity.HIGH:
        return { ...baseStyle, background: '#ef4444', color: 'white' };
      case ErrorSeverity.CRITICAL:
        return {
          ...baseStyle,
          background: '#dc2626',
          color: 'white',
          fontWeight: 'bold',
          border: '2px solid #991b1b'
        };
      default:
        return baseStyle;
    }
  }
}

// ==================== CONVENIENCE FUNCTIONS ====================
export const errorHandler = ErrorHandler.getInstance();

export const handleError = (error: unknown, options?: ErrorHandlerOptions) => {
  return errorHandler.handle(error, options);
};

export const handleAsyncError = <T>(
  operation: () => Promise<T>,
  options?: ErrorHandlerOptions
) => {
  return errorHandler.handleAsync(operation, options);
};

export const withRetry = <T>(
  operation: () => Promise<T>,
  maxRetries?: number,
  delayMs?: number
) => {
  return errorHandler.withRetry(operation, maxRetries, delayMs);
};

// ==================== ERROR BOUNDARIES ====================
export const createErrorBoundaryHandler = (context: string) => {
  return (error: Error, errorInfo: React.ErrorInfo) => {
    errorHandler.handle(error, {
      context: { componentStack: errorInfo.componentStack, boundary: context },
      showToast: true,
      logToConsole: true,
      reportToService: true,
    });
  };
};

// ==================== VALIDATION HELPERS ====================
export const validateAndHandle = <T>(
  data: T,
  validator: (data: T) => boolean | string,
  options?: ErrorHandlerOptions
): { isValid: boolean; error?: StandardError } => {
  try {
    const result = validator(data);

    if (result === true) {
      return { isValid: true };
    }

    const error = errorHandler.handle(
      new Error(typeof result === 'string' ? result : 'Validation failed'),
      {
        ...options,
        context: { data, validator: validator.name }
      }
    );

    return { isValid: false, error };
  } catch (error) {
    const handledError = errorHandler.handle(error, options);
    return { isValid: false, error: handledError };
  }
};
