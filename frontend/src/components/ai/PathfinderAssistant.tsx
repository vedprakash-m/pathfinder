import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, ThumbsUp, ThumbsDown, X } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
  interactionId?: string;
  responseCards?: ResponseCard[];
}

interface CardContent {
  text?: string;
  items?: string[];
  data?: Record<string, unknown>;
}

interface ResponseCard {
  id: string;
  card_type: string;
  title: string;
  content: CardContent;
  actions?: Array<{
    label: string;
    action: string;
  }>;
  is_dismissed: boolean;
}

interface TripContextData {
  id?: string;
  name?: string;
  destination?: string;
  start_date?: string;
  end_date?: string;
  status?: string;
  participants?: Array<{ id: string; name: string }>;
}

interface AssistantActionData {
  card_id?: string;
  card_type?: string;
  action_value?: string;
  context?: Record<string, unknown>;
}

interface PathfinderAssistantProps {
  context?: {
    trip_id?: string;
    family_id?: string;
    current_page?: string;
    trip_data?: TripContextData;
  };
  className?: string;
  onAssistantAction?: (action: string, data: AssistantActionData) => void;
}

export const PathfinderAssistant: React.FC<PathfinderAssistantProps> = ({
  context = {},
  className = '',
  onAssistantAction
}) => {
  const { token } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (message: string) => {
    if (!message.trim() || isLoading) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      content: message,
      isUser: true,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/v1/assistant/mention', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: `@pathfinder ${message}`,
          context: {
            ...context,
            current_page: window.location.pathname
          },
          trip_id: context.trip_id,
          family_id: context.family_id
        })
      });

      if (!response.ok) {
        throw new Error('Failed to get assistant response');
      }

      const data = await response.json();

      if (data.success) {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: data.data.response,
          isUser: false,
          timestamp: new Date(),
          interactionId: data.data.interaction_id,
          responseCards: data.data.response_cards
        };

        setMessages(prev => [...prev, assistantMessage]);
      } else {
        throw new Error(data.message || 'Unknown error');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Sorry, I encountered an issue. Please try again.',
        isUser: false,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(inputValue);
    }
  };

  const handleFeedback = async (interactionId: string, rating: number) => {
    try {
      await fetch('/api/v1/assistant/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          interaction_id: interactionId,
          rating
        })
      });
    } catch (error) {
      console.error('Error submitting feedback:', error);
    }
  };

  const handleCardAction = (action: string, cardData: AssistantActionData) => {
    if (onAssistantAction) {
      onAssistantAction(action, cardData);
    }
  };

  const dismissCard = async (cardId: string) => {
    try {
      await fetch(`/api/v1/assistant/cards/${cardId}/dismiss`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        }
      });

      // Update messages to mark card as dismissed
      setMessages(prev => prev.map(msg => ({
        ...msg,
        responseCards: msg.responseCards?.map(card =>
          card.id === cardId ? { ...card, is_dismissed: true } : card
        )
      })));
    } catch (error) {
      console.error('Error dismissing card:', error);
    }
  };

  const MessageCard: React.FC<{ message: Message }> = ({ message }) => (
    <div className={`flex ${message.isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`flex max-w-xs lg:max-w-md ${message.isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        <div className={`flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center ${
          message.isUser ? 'bg-blue-500 ml-2' : 'bg-gray-600 mr-2'
        }`}>
          {message.isUser ? <User className="h-4 w-4 text-white" /> : <Bot className="h-4 w-4 text-white" />}
        </div>
        <div className={`px-4 py-2 rounded-lg ${
          message.isUser
            ? 'bg-blue-500 text-white'
            : 'bg-gray-100 text-gray-900 border'
        }`}>
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          <p className="text-xs opacity-70 mt-1">
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </p>

          {/* Feedback buttons for assistant messages */}
          {!message.isUser && message.interactionId && (
            <div className="flex items-center mt-2 space-x-2">
              <button
                onClick={() => handleFeedback(message.interactionId!, 5)}
                className="p-1 hover:bg-gray-200 rounded transition-colors"
                title="Helpful"
              >
                <ThumbsUp className="h-3 w-3 text-gray-500" />
              </button>
              <button
                onClick={() => handleFeedback(message.interactionId!, 1)}
                className="p-1 hover:bg-gray-200 rounded transition-colors"
                title="Not helpful"
              >
                <ThumbsDown className="h-3 w-3 text-gray-500" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const ResponseCardComponent: React.FC<{ card: ResponseCard }> = ({ card }) => {
    if (card.is_dismissed) return null;

    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-3">
        <div className="flex justify-between items-start mb-2">
          <h4 className="font-medium text-blue-900">{card.title}</h4>
          <button
            onClick={() => dismissCard(card.id)}
            className="text-blue-400 hover:text-blue-600 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {card.content.text && (
          <p className="text-blue-800 text-sm mb-3">{card.content.text}</p>
        )}

        {card.actions && card.actions.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {card.actions.map((action, index) => (
              <button
                key={index}
                onClick={() => handleCardAction(action.action, card)}
                className="px-3 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 transition-colors"
              >
                {action.label}
              </button>
            ))}
          </div>
        )}
      </div>
    );
  };

  if (!isExpanded) {
    return (
      <div className={`fixed bottom-4 right-4 z-50 ${className}`}>
        <button
          onClick={() => setIsExpanded(true)}
          className="bg-blue-500 hover:bg-blue-600 text-white p-3 rounded-full shadow-lg transition-colors"
          title="Open Pathfinder Assistant"
        >
          <Bot className="h-6 w-6" />
        </button>
      </div>
    );
  }

  return (
    <div className={`fixed bottom-4 right-4 w-80 h-96 bg-white border border-gray-300 rounded-lg shadow-xl z-50 flex flex-col ${className}`}>
      {/* Header */}
      <div className="bg-blue-500 text-white p-3 rounded-t-lg flex justify-between items-center">
        <div className="flex items-center space-x-2">
          <Bot className="h-5 w-5" />
          <span className="font-medium">Pathfinder Assistant</span>
        </div>
        <button
          onClick={() => setIsExpanded(false)}
          className="text-white hover:text-gray-200 transition-colors"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 py-8">
            <Bot className="h-12 w-12 mx-auto mb-3 text-gray-300" />
            <p className="text-sm">Hi! I'm your Pathfinder Assistant.</p>
            <p className="text-xs mt-1">Ask me anything about trip planning!</p>
          </div>
        )}

        {messages.map((message) => (
          <div key={message.id}>
            <MessageCard message={message} />
            {/* Response cards */}
            {message.responseCards && message.responseCards.map((card) => (
              <ResponseCardComponent key={card.id} card={card} />
            ))}
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start mb-4">
            <div className="flex flex-row">
              <div className="flex-shrink-0 h-8 w-8 rounded-full bg-gray-600 mr-2 flex items-center justify-center">
                <Bot className="h-4 w-4 text-white" />
              </div>
              <div className="bg-gray-100 border px-4 py-2 rounded-lg">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t p-3">
        <div className="flex space-x-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading}
          />
          <button
            onClick={() => handleSendMessage(inputValue)}
            disabled={isLoading || !inputValue.trim()}
            className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 text-white px-3 py-2 rounded-md transition-colors"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
