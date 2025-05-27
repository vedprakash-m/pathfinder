import { useEffect, useState, useRef, useCallback } from 'react';
import websocketService, { MessageHandler } from '@/services/websocket';

/**
 * Custom hook for using WebSockets in React components
 * 
 * @param messageTypes Array of message types to listen for
 * @param deps Dependency array (like useEffect)
 * @returns Object with connection status and send function
 */
export function useWebSocket<T = any>(
  messageTypes: string[] = [],
  deps: any[] = []
) {
  const [isConnected, setIsConnected] = useState(websocketService.isConnectedStatus());
  const [lastMessage, setLastMessage] = useState<T | null>(null);
  const [messages, setMessages] = useState<T[]>([]);
  
  const handlers = useRef<{ [key: string]: () => void }>({});
  const messagesRef = useRef<T[]>([]);
  
  // Update messages ref when state changes
  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  // Connect to WebSocket on mount
  useEffect(() => {
    const connectWebSocket = async () => {
      try {
        await websocketService.connect();
        setIsConnected(true);
      } catch (error) {
        console.error('WebSocket connection error:', error);
        setIsConnected(false);
      }
    };
    
    if (!websocketService.isConnectedStatus()) {
      connectWebSocket();
    } else {
      setIsConnected(true);
    }
    
    // Create connection status handler
    const checkConnectionInterval = setInterval(() => {
      setIsConnected(websocketService.isConnectedStatus());
    }, 3000);
    
    return () => {
      clearInterval(checkConnectionInterval);
    };
  }, []);
  
  // Set up message handlers
  useEffect(() => {
    // Clean up any existing handlers
    Object.values(handlers.current).forEach((unsubscribe) => unsubscribe());
    handlers.current = {};
    
    // Set up new handlers for each message type
    messageTypes.forEach((type) => {
      const handler: MessageHandler<T> = (data) => {
        setLastMessage(data);
        setMessages((prevMessages) => [...prevMessages, data]);
      };
      
      handlers.current[type] = websocketService.on<T>(type, handler);
    });
    
    return () => {
      // Clean up handlers on unmount or when deps change
      Object.values(handlers.current).forEach((unsubscribe) => unsubscribe());
    };
  }, [...deps, ...messageTypes]);
  
  // Send message function
  const send = useCallback((type: string, payload: any, roomId?: string) => {
    websocketService.send(type, payload, roomId);
  }, []);
  
  // Join room function
  const joinRoom = useCallback((roomId: string) => {
    websocketService.joinRoom(roomId);
  }, []);
  
  // Leave room function
  const leaveRoom = useCallback((roomId: string) => {
    websocketService.leaveRoom(roomId);
  }, []);
  
  // Clear messages function
  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);
  
  return {
    isConnected,
    lastMessage,
    messages,
    send,
    joinRoom,
    leaveRoom,
    clearMessages,
  };
}

export default useWebSocket;
