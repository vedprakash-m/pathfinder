export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  status?: string;
  errors?: Array<{
    field?: string;
    message: string;
  }>;
}

export interface PaginatedResponse<T = any> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ErrorResponse {
  message: string;
  code?: string;
  details?: Record<string, any>;
}

export interface SearchRequest {
  query: string;
  filters?: Record<string, any>;
  page?: number;
  page_size?: number;
}

export interface WebSocketMessage<T = any> {
  message_type: string;
  payload: T;
  room_id?: string;
  sender_id?: string;
  timestamp: string;
}

export interface ApiErrorResponse {
  status: number;
  message: string;
  error_code?: string;
  timestamp?: string;
  path?: string;
  details?: Record<string, any>;
}

export interface ExportRequest {
  format: 'pdf' | 'json' | 'csv';
  include_details?: boolean;
  sections?: string[];
}