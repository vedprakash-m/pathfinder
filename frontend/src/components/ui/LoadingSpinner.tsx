import React from 'react';
import { Spinner } from '@fluentui/react-components';

interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  label?: string;
  className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'medium', 
  label = 'Loading...', 
  className = '' 
}) => {
  const sizeMap = {
    small: 'tiny',
    medium: 'medium',
    large: 'huge',
  } as const;

  return (
    <div className={`flex flex-col items-center justify-center space-y-2 ${className}`}>
      <Spinner 
        size={sizeMap[size]}
        label={label}
      />
      {label && (
        <span className="text-sm text-gray-600">{label}</span>
      )}
    </div>
  );
};
