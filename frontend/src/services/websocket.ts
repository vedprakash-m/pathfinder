import { WebSocketMessage } from '@/types';

// Types for WebSocket events
export type MessageHandler<T = unknown> = (data: T) => void;

interface WebSocketHandlers {
  [key: string]: MessageHandler[];
}

export class WebSocketService {
  private socket: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 2000; // ms
  private reconnectTimeoutId: number | null = null;
  private handlers: WebSocketHandlers = {};
  private isConnected = false;
  private queue: string[] = []; // Queue messages if socket isn't connected

  constructor(private baseUrl: string = '') {
    this.baseUrl = baseUrl || (window.location.protocol === 'https:'
      ? `wss://${window.location.host}/ws`
      : `ws://${window.location.host}/ws`);
  }

  // Connect to WebSocket server
  connect(token?: string): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.socket?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      let url = this.baseUrl;
      if (token) {
        url += `?token=${token}`;
      } else {
        // Get token from localStorage
        const authToken = localStorage.getItem('auth_token');
        if (authToken) {
          url += `?token=${authToken}`;
        }
      }

      try {
        this.socket = new WebSocket(url);

        this.socket.onopen = () => {
          this.isConnected = true;
          this.reconnectAttempts = 0;
          console.log('WebSocket connected');

          // Send any queued messages
          while (this.queue.length > 0) {
            const message = this.queue.shift();
            if (message) this.sendRaw(message);
          }

          resolve();
        };

        this.socket.onclose = (event) => {
          this.isConnected = false;
          console.log(`WebSocket disconnected: ${event.code} ${event.reason}`);

          if (!event.wasClean) {
            this.attemptReconnect();
          }
        };

        this.socket.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };

        this.socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };
      } catch (error) {
        console.error('Error connecting to WebSocket:', error);
        reject(error);
      }
    });
  }

  // Disconnect from WebSocket server
  disconnect(): void {
    if (this.reconnectTimeoutId) {
      window.clearTimeout(this.reconnectTimeoutId);
      this.reconnectTimeoutId = null;
    }

    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }

    this.isConnected = false;
    this.queue = []; // Clear the queue
  }

  // Attempt to reconnect
  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts - 1);

      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms`);

      this.reconnectTimeoutId = window.setTimeout(() => {
        this.connect()
          .catch(() => {
            // Error handling is done inside connect()
          });
      }, delay);
    } else {
      console.error('Maximum reconnection attempts reached');
    }
  }

  // Send a message
  send<T = unknown>(type: string, payload: T, roomId?: string): void {
    const message: WebSocketMessage<T> = {
      type: 'trip_update', // Default type, can be overridden
      message_type: type,
      data: payload,
      payload,
      room_id: roomId,
      timestamp: new Date().toISOString()
    };

    this.sendRaw(JSON.stringify(message));
  }

  // Send a raw string message
  private sendRaw(message: string): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(message);
    } else {
      // Queue the message to send when connected
      this.queue.push(message);

      // If socket isn't connecting or connected, try to connect
      if (!this.socket ||
          (this.socket.readyState !== WebSocket.CONNECTING &&
           this.socket.readyState !== WebSocket.OPEN)) {
        this.connect().catch(console.error);
      }
    }
  }

  // Register a message handler
  on<T = unknown>(type: string, callback: MessageHandler<T>): () => void {
    if (!this.handlers[type]) {
      this.handlers[type] = [];
    }

    this.handlers[type].push(callback as MessageHandler);

    // Return unsubscribe function
    return () => {
      this.handlers[type] = this.handlers[type].filter(cb => cb !== callback);
    };
  }

  // Remove a message handler
  off(type: string, callback?: MessageHandler): void {
    if (!callback) {
      delete this.handlers[type];
    } else if (this.handlers[type]) {
      this.handlers[type] = this.handlers[type].filter(cb => cb !== callback);
    }
  }

  // Handle incoming messages
  private handleMessage(data: WebSocketMessage): void {
    if (data.message_type && this.handlers[data.message_type]) {
      this.handlers[data.message_type].forEach(callback => {
        try {
          callback(data.payload);
        } catch (error) {
          console.error(`Error in ${data.message_type} handler:`, error);
        }
      });
    }

    // Also trigger any 'all' message handlers
    if (this.handlers['all']) {
      this.handlers['all'].forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('Error in "all" handler:', error);
        }
      });
    }
  }

  // Check if WebSocket is connected
  isConnectedStatus(): boolean {
    return this.isConnected;
  }

  // Join a room
  joinRoom(roomId: string): void {
    this.send('join_room', { room_id: roomId }, roomId);
  }

  // Leave a room
  leaveRoom(roomId: string): void {
    this.send('leave_room', { room_id: roomId }, roomId);
  }
}

// Create singleton instance
const websocketService = new WebSocketService();
export default websocketService;
