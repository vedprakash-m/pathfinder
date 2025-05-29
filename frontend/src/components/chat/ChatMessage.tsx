import React from 'react';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Card } from '@/components/ui/card';
import { formatDistanceToNow } from 'date-fns';

export interface ChatMessageProps {
  id: string;
  content: string;
  sender: {
    id: string;
    name: string;
    avatar?: string;
  };
  timestamp: Date;
  isOwn: boolean;
  type?: 'text' | 'system' | 'activity' | 'poll';
  metadata?: {
    activity?: {
      id: string;
      title: string;
      description: string;
    };
    poll?: {
      id: string;
      question: string;
      options: Array<{
        id: string;
        text: string;
        votes: number;
      }>;
      userVote?: string;
    };
  };
}

export const ChatMessage: React.FC<ChatMessageProps> = ({
  content,
  sender,
  timestamp,
  isOwn,
  type = 'text',
  metadata
}) => {
  const formatTime = (date: Date) => {
    return formatDistanceToNow(date, { addSuffix: true });
  };

  const renderSystemMessage = () => (
    <div className="flex justify-center my-2">
      <div className="bg-muted px-3 py-1 rounded-full text-sm text-muted-foreground">
        {content}
      </div>
    </div>
  );

  const renderActivityMessage = () => (
    <Card className="p-4 my-2 border-l-4 border-l-blue-500">
      <div className="flex items-start space-x-3">
        <Avatar className="w-8 h-8">
          <AvatarImage src={sender.avatar} />
          <AvatarFallback>
            {sender.name.split(' ').map(n => n[0]).join('')}
          </AvatarFallback>
        </Avatar>
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-1">
            <span className="font-medium text-sm">{sender.name}</span>
            <span className="text-xs text-muted-foreground">{formatTime(timestamp)}</span>
          </div>
          <div className="text-sm text-muted-foreground mb-2">{content}</div>
          {metadata?.activity && (
            <div className="bg-blue-50 p-3 rounded-lg">
              <h4 className="font-medium text-blue-900">{metadata.activity.title}</h4>
              <p className="text-sm text-blue-700 mt-1">{metadata.activity.description}</p>
            </div>
          )}
        </div>
      </div>
    </Card>
  );

  const renderPollMessage = () => (
    <Card className="p-4 my-2 border-l-4 border-l-green-500">
      <div className="flex items-start space-x-3">
        <Avatar className="w-8 h-8">
          <AvatarImage src={sender.avatar} />
          <AvatarFallback>
            {sender.name.split(' ').map(n => n[0]).join('')}
          </AvatarFallback>
        </Avatar>
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-1">
            <span className="font-medium text-sm">{sender.name}</span>
            <span className="text-xs text-muted-foreground">{formatTime(timestamp)}</span>
          </div>
          <div className="text-sm text-muted-foreground mb-2">{content}</div>
          {metadata?.poll && (
            <div className="bg-green-50 p-3 rounded-lg">
              <h4 className="font-medium text-green-900 mb-2">{metadata.poll.question}</h4>
              <div className="space-y-2">
                {metadata.poll.options.map((option) => (
                  <div key={option.id} className="flex items-center justify-between">
                    <span className="text-sm text-green-700">{option.text}</span>
                    <span className="text-xs text-green-600">{option.votes} votes</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </Card>
  );

  const renderTextMessage = () => (
    <div className={`flex ${isOwn ? 'justify-end' : 'justify-start'} my-2`}>
      <div className={`flex ${isOwn ? 'flex-row-reverse' : 'flex-row'} items-start space-x-3 max-w-[70%]`}>
        {!isOwn && (
          <Avatar className="w-8 h-8">
            <AvatarImage src={sender.avatar} />
            <AvatarFallback>
              {sender.name.split(' ').map(n => n[0]).join('')}
            </AvatarFallback>
          </Avatar>
        )}
        <div className={`${isOwn ? 'mr-3' : ''}`}>
          {!isOwn && (
            <div className="text-xs text-muted-foreground mb-1">{sender.name}</div>
          )}
          <div
            className={`px-3 py-2 rounded-lg ${
              isOwn
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted'
            }`}
          >
            <div className="text-sm">{content}</div>
          </div>
          <div className={`text-xs text-muted-foreground mt-1 ${isOwn ? 'text-right' : 'text-left'}`}>
            {formatTime(timestamp)}
          </div>
        </div>
      </div>
    </div>
  );

  switch (type) {
    case 'system':
      return renderSystemMessage();
    case 'activity':
      return renderActivityMessage();
    case 'poll':
      return renderPollMessage();
    default:
      return renderTextMessage();
  }
};
