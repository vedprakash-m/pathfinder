import React, { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card } from '@/components/ui/card';
import { 
  Send, 
  Smile, 
  Paperclip, 
  Calendar, 
  Vote,
  X 
} from 'lucide-react';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface ChatInputProps {
  onSendMessage: (content: string, type?: 'text' | 'activity' | 'poll', metadata?: any) => void;
  disabled?: boolean;
  placeholder?: string;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  disabled = false,
  placeholder = "Type a message..."
}) => {
  const [message, setMessage] = useState('');
  const [isActivityMode, setIsActivityMode] = useState(false);
  const [isPollMode, setIsPollMode] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Activity state
  const [activityTitle, setActivityTitle] = useState('');
  const [activityDescription, setActivityDescription] = useState('');

  // Poll state
  const [pollQuestion, setPollQuestion] = useState('');
  const [pollOptions, setPollOptions] = useState(['', '']);

  const handleSend = () => {
    if (!message.trim() && !isActivityMode && !isPollMode) return;

    if (isActivityMode) {
      if (!activityTitle.trim() || !activityDescription.trim()) return;
      
      onSendMessage(message || `Suggested activity: ${activityTitle}`, 'activity', {
        activity: {
          id: Date.now().toString(),
          title: activityTitle,
          description: activityDescription
        }
      });
      
      setActivityTitle('');
      setActivityDescription('');
      setIsActivityMode(false);
    } else if (isPollMode) {
      if (!pollQuestion.trim() || pollOptions.filter(opt => opt.trim()).length < 2) return;
      
      onSendMessage(message || `Created poll: ${pollQuestion}`, 'poll', {
        poll: {
          id: Date.now().toString(),
          question: pollQuestion,
          options: pollOptions.filter(opt => opt.trim()).map((opt, index) => ({
            id: index.toString(),
            text: opt.trim(),
            votes: 0
          }))
        }
      });
      
      setPollQuestion('');
      setPollOptions(['', '']);
      setIsPollMode(false);
    } else {
      onSendMessage(message, 'text');
    }

    setMessage('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
    
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px';
    }
  };

  const addPollOption = () => {
    if (pollOptions.length < 6) {
      setPollOptions([...pollOptions, '']);
    }
  };

  const removePollOption = (index: number) => {
    if (pollOptions.length > 2) {
      setPollOptions(pollOptions.filter((_, i) => i !== index));
    }
  };

  const updatePollOption = (index: number, value: string) => {
    const newOptions = [...pollOptions];
    newOptions[index] = value;
    setPollOptions(newOptions);
  };

  const resetModes = () => {
    setIsActivityMode(false);
    setIsPollMode(false);
    setActivityTitle('');
    setActivityDescription('');
    setPollQuestion('');
    setPollOptions(['', '']);
  };

  return (
    <Card className="p-4 border-t">
      {/* Activity Mode Panel */}
      {isActivityMode && (
        <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-medium text-blue-900">Suggest Activity</h4>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsActivityMode(false)}
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
          <div className="space-y-2">
            <div>
              <Label htmlFor="activity-title">Activity Title</Label>
              <Input
                id="activity-title"
                value={activityTitle}
                onChange={(e) => setActivityTitle(e.target.value)}
                placeholder="e.g., Visit Central Park"
              />
            </div>
            <div>
              <Label htmlFor="activity-description">Description</Label>
              <Textarea
                id="activity-description"
                value={activityDescription}
                onChange={(e) => setActivityDescription(e.target.value)}
                placeholder="What makes this activity great for our group?"
                rows={2}
              />
            </div>
          </div>
        </div>
      )}

      {/* Poll Mode Panel */}
      {isPollMode && (
        <div className="mb-4 p-3 bg-green-50 rounded-lg border border-green-200">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-medium text-green-900">Create Poll</h4>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsPollMode(false)}
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
          <div className="space-y-2">
            <div>
              <Label htmlFor="poll-question">Question</Label>
              <Input
                id="poll-question"
                value={pollQuestion}
                onChange={(e) => setPollQuestion(e.target.value)}
                placeholder="What would you like to vote on?"
              />
            </div>
            <div>
              <Label>Options</Label>
              {pollOptions.map((option, index) => (
                <div key={index} className="flex items-center space-x-2 mt-1">
                  <Input
                    value={option}
                    onChange={(e) => updatePollOption(index, e.target.value)}
                    placeholder={`Option ${index + 1}`}
                  />
                  {pollOptions.length > 2 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removePollOption(index)}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              ))}
              {pollOptions.length < 6 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={addPollOption}
                  className="mt-2"
                >
                  Add Option
                </Button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Main Input Area */}
      <div className="flex items-end space-x-2">
        <div className="flex-1">
          <Textarea
            ref={textareaRef}
            value={message}
            onChange={handleTextareaChange}
            onKeyPress={handleKeyPress}
            placeholder={
              isActivityMode 
                ? "Add a message about this activity..." 
                : isPollMode 
                ? "Add a message about this poll..."
                : placeholder
            }
            disabled={disabled}
            className="min-h-[40px] max-h-[120px] resize-none"
            rows={1}
          />
        </div>

        {/* Action Buttons */}
        <div className="flex space-x-1">
          {/* Activity Button */}
          <Popover>
            <PopoverTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                disabled={disabled}
                className={isActivityMode ? 'bg-blue-100' : ''}
              >
                <Calendar className="w-4 h-4" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-80">
              <div className="space-y-2">
                <h4 className="font-medium">Suggest Activity</h4>
                <p className="text-sm text-muted-foreground">
                  Propose an activity for the group to consider
                </p>
                <Button
                  onClick={() => {
                    resetModes();
                    setIsActivityMode(true);
                  }}
                  className="w-full"
                >
                  Create Activity Suggestion
                </Button>
              </div>
            </PopoverContent>
          </Popover>

          {/* Poll Button */}
          <Popover>
            <PopoverTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                disabled={disabled}
                className={isPollMode ? 'bg-green-100' : ''}
              >
                <Vote className="w-4 h-4" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-80">
              <div className="space-y-2">
                <h4 className="font-medium">Create Poll</h4>
                <p className="text-sm text-muted-foreground">
                  Let the group vote on decisions
                </p>
                <Button
                  onClick={() => {
                    resetModes();
                    setIsPollMode(true);
                  }}
                  className="w-full"
                >
                  Create Poll
                </Button>
              </div>
            </PopoverContent>
          </Popover>

          {/* Emoji Button (future feature) */}
          <Button
            variant="ghost"
            size="sm"
            disabled
            className="opacity-50"
          >
            <Smile className="w-4 h-4" />
          </Button>

          {/* Attachment Button (future feature) */}
          <Button
            variant="ghost"
            size="sm"
            disabled
            className="opacity-50"
          >
            <Paperclip className="w-4 h-4" />
          </Button>

          {/* Send Button */}
          <Button
            onClick={handleSend}
            disabled={disabled || (!message.trim() && !isActivityMode && !isPollMode)}
            size="sm"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </Card>
  );
};
