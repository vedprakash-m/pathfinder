import React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {}

export const Card: React.FC<CardProps> = ({ className = '', children, ...props }) => {
  const classes = `rounded-lg border bg-card text-card-foreground shadow-sm ${className}`;
  
  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
};

export const CardHeader: React.FC<CardProps> = ({ className = '', children, ...props }) => {
  const classes = `flex flex-col space-y-1.5 p-6 ${className}`;
  
  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
};

export const CardContent: React.FC<CardProps> = ({ className = '', children, ...props }) => {
  const classes = `p-6 pt-0 ${className}`;
  
  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
};
