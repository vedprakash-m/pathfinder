import React from 'react';

export interface PopoverProps {
  children: React.ReactNode;
}

export const Popover: React.FC<PopoverProps> = ({ children }) => {
  return <div>{children}</div>;
};

export const PopoverTrigger: React.FC<{ children: React.ReactNode; asChild?: boolean }> = ({ children, asChild }) => {
  if (asChild) {
    return <>{children}</>;
  }
  return <div>{children}</div>;
};

export const PopoverContent: React.FC<{ children: React.ReactNode; className?: string }> = ({ 
  children, 
  className = '' 
}) => {
  const classes = `z-50 w-72 rounded-md border bg-popover p-4 text-popover-foreground shadow-md outline-none ${className}`;
  
  return (
    <div className={classes}>
      {children}
    </div>
  );
};
