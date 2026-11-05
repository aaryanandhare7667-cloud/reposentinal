import React from 'react';

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  icon: Icon,
  className = '',
  disabled = false,
  onClick,
  type = 'button',
  ...props
}) {
  const baseStyles = 'inline-flex items-center justify-center font-medium transition-colors focus:outline-none focus:ring-1 focus:ring-brand-500 disabled:opacity-50 disabled:cursor-not-allowed select-none rounded';

  const sizes = {
    sm: 'text-xs px-2.5 py-1 gap-1.5',
    md: 'text-xs px-3.5 py-1.5 gap-2',
    lg: 'text-sm px-4 py-2 gap-2.5',
  };

  const variants = {
    primary: 'bg-brand-600 hover:bg-brand-500 active:bg-brand-700 text-white border border-brand-500/50 shadow-sm',
    secondary: 'bg-bg-elevated hover:bg-bg-hover active:bg-bg-active text-text-primary border border-border',
    outline: 'bg-transparent hover:bg-bg-surface text-text-secondary hover:text-text-primary border border-border',
    danger: 'bg-red-950/50 hover:bg-red-900/60 active:bg-red-900 text-red-300 border border-red-500/50',
    ghost: 'bg-transparent hover:bg-bg-surface text-text-secondary hover:text-text-primary',
    verified: 'bg-emerald-950/40 hover:bg-emerald-900/50 text-emerald-300 border border-emerald-500/60',
  };

  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={`${baseStyles} ${sizes[size]} ${variants[variant]} ${className}`}
      {...props}
    >
      {Icon && <Icon className={size === 'sm' ? 'w-3.5 h-3.5' : 'w-4 h-4'} />}
      <span>{children}</span>
    </button>
  );
}
