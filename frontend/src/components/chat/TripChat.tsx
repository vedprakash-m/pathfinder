import React, { useState, useEffect, useRef } from 'react';
import { Card, CardHeader, Title3, Body1, Body2 } from '@fluentui/react-components';
import { motion } from 'framer-motion';
import { ChatMessage, ChatMessageProps } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { useAuthStore } from '@/store';
import webSocketService from '@/services/websocket';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { UsersIcon, WifiIcon } from '@heroicons/react/24/outline';

interface OnlineUser {
  user_id: string;
  user_name: string;
  family_id: string;
  status: string;
}

interface TripChatProps {
  tripId: string;
  tripName: string;
}

export const TripChat: React.FC<TripChatProps> = ({ tripId, tripName }) => {
  const { user } = useAuthStore();
  const [messages, setMessages] = useState<ChatMessageProps[]>([]);
  const [onlineUsers, setOnlineUsers] = useState<OnlineUser[]>([]);
  const [typingUsers, setTypingUsers] = useState<Array<{ user_id: string; user_name: string }>>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // WebSocket connection and message handling
  useEffect(() => {
    if (!user || !tripId) return;

    const connectToChat = async () => {
      setIsConnecting(true);
      try {
        // Connect to WebSocket
        await webSocketService.connect();
        
        // Join trip room
        webSocketService.joinRoom(tripId);

        // Set up message listeners
        webSocketService.on('message', (messageData: any) => {
          const newMessage: ChatMessageProps = {
            id: messageData.id || Date.now().toString(),
            content: messageData.content || messageData.text || '',
            sender: {
              id: messageData.user_id || messageData.sender_id,
              name: messageData.user_name || messageData.sender_name || 'Unknown User',
              avatar: messageData.avatar,
            },
            timestamp: new Date(messageData.timestamp || Date.now()),
            isOwn: messageData.user_id === user.id || messageData.sender_id === user.id,
            type: messageData.message_type || messageData.type || 'text',
            metadata: messageData.metadata,
          };
          
          setMessages(prev => [...prev, newMessage]);
        });

        webSocketService.on('message_history', (data: any) => {
          const historyMessages: ChatMessageProps[] = data.messages.map((msg: any) => ({
            id: msg.id,
            content: msg.content,
            sender: {
              id: msg.user_id,
              name: msg.user_name,
              avatar: msg.avatar,
            },
            timestamp: new Date(msg.timestamp),
            isOwn: msg.user_id === user.id,
            type: msg.message_type || 'text',
            metadata: msg.metadata,
          }));
          
          setMessages(historyMessages);
        });

        webSocketService.on('presence_update', (data: any) => {
          setOnlineUsers(data.online_users || []);
        });

        webSocketService.on('typing_indicator', (data: any) => {
          setTypingUsers(data.typing_users || []);
        });

        webSocketService.on('connected', () => {
          setIsConnected(true);
          setIsConnecting(false);
        });

        webSocketService.on('disconnected', () => {
          setIsConnected(false);
        });

        webSocketService.on('error', (error: any) => {
          console.error('WebSocket error:', error);
          setIsConnecting(false);
        });

      } catch (error) {
        console.error('Failed to connect to chat:', error);
        setIsConnecting(false);
      }
    };

    connectToChat();

    // Cleanup on unmount
    return () => {
      if (webSocketService.isConnectedStatus()) {
        webSocketService.leaveRoom(tripId);
        webSocketService.disconnect();
      }
    };
  }, [user, tripId]);

  const handleSendMessage = (content: string, type?: 'text' | 'activity' | 'poll', metadata?: any) => {
    if (!content.trim() || !isConnected) return;

    const messageData = {
      text: content,
      type: type || 'text',
      metadata: metadata || {},
      trip_id: tripId,
    };

    webSocketService.send('send_message', messageData, tripId);
  };

  if (isConnecting) {
    return (
      <div className="flex flex-col h-full items-center justify-center py-8">
        <LoadingSpinner size="large" />
        <Body1 className="text-neutral-600 mt-4">Connecting to chat...</Body1>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="grid lg:grid-cols-4 gap-6 h-full"
    >
      {/* Chat Messages */}
      <div className="lg:col-span-3">
        <Card className="h-full flex flex-col">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Title3>Trip Chat</Title3>
                <div className="flex items-center gap-2">
                  <WifiIcon className={`w-4 h-4 ${isConnected ? 'text-green-600' : 'text-red-600'}`} />
                  <Badge variant={isConnected ? 'default' : 'destructive'}>
                    {isConnected ? 'Connected' : 'Disconnected'}
                  </Badge>
                </div>
              </div>
              <Body2 className="text-neutral-600">{tripName}</Body2>
            </div>
          </CardHeader>

          {/* Messages Container */}
          <div 
            ref={chatContainerRef}
            className="flex-1 p-4 overflow-y-auto max-h-96 space-y-2"
            style={{ minHeight: '400px' }}
          >
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center py-8">
                <div className="w-16 h-16 bg-primary-50 rounded-full flex items-center justify-center mb-4">
                  <svg className="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                </div>
                <Body1 className="text-neutral-600 mb-2">No messages yet</Body1>
                <Body2 className="text-neutral-500">Start the conversation about your trip!</Body2>
              </div>
            ) : (
              <>
                {messages.map((message) => (
                  <ChatMessage key={message.id} {...message} />
                ))}
                
                {/* Typing Indicators */}
                {typingUsers.length > 0 && (
                  <div className="flex items-center gap-2 text-sm text-neutral-500 py-2">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                    <span>
                      {typingUsers.map(u => u.user_name).join(', ')} 
                      {typingUsers.length === 1 ? ' is' : ' are'} typing...
                    </span>
                  </div>
                )}
              </>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Chat Input */}
          <div className="border-t">
            <ChatInput
              onSendMessage={handleSendMessage}
              disabled={!isConnected}
              placeholder={isConnected ? "Type a message..." : "Connecting..."}
            />
          </div>
        </Card>
      </div>

      {/* Online Users Sidebar */}
      <div className="lg:col-span-1">
        <Card className="h-full">
          <CardHeader>
            <div className="flex items-center gap-2">
              <UsersIcon className="w-5 h-5 text-neutral-600" />
              <Title3>Online Now</Title3>
              <Badge>{onlineUsers.length}</Badge>
            </div>
          </CardHeader>
          <div className="p-4">
            {onlineUsers.length === 0 ? (
              <div className="text-center py-4">
                <Body2 className="text-neutral-500">No one online</Body2>
              </div>
            ) : (
              <div className="space-y-3">
                {onlineUsers.map((onlineUser) => (
                  <div key={onlineUser.user_id} className="flex items-center gap-3">
                    <Avatar className="w-8 h-8">
                      <AvatarFallback>
                        {onlineUser.user_name.split(' ').map(n => n[0]).join('')}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1">
                      <Body2 className="font-medium">
                        {onlineUser.user_name}
                        {onlineUser.user_id === user?.id && ' (You)'}
                      </Body2>
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        <Body2 className="text-xs text-neutral-500 capitalize">
                          {onlineUser.status}
                        </Body2>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Card>
      </div>
    </motion.div>
  );
};
