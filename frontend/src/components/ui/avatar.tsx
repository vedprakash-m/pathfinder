import React from 'react';

export interface AvatarProps extends React.HTMLAttributes<HTMLDivElement> {}

export const Avatar: React.FC<AvatarProps> = ({ className = '', children, ...props }) => {
  const classes = `relative flex h-10 w-10 shrink-0 overflow-hidden rounded-full ${className}`;
  
  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
};

export const AvatarImage: React.FC<React.ImgHTMLAttributes<HTMLImageElement>> = ({ 
  className = '', 
  ...props 
}) => {
  const classes = `aspect-square h-full w-full ${className}`;
  
  return <img className={classes} {...props} />;
};

export const AvatarFallback: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ 
  className = '', 
  children, 
  ...props 
}) => {
  const classes = `flex h-full w-full items-center justify-center rounded-full bg-muted ${className}`;
  
  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
};
