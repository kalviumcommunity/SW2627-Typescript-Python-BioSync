import type { ButtonHTMLAttributes, ReactNode } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'outline'
  icon?: ReactNode
  children: ReactNode
}

export function Button({ variant = 'primary', icon, children, className = '', type = 'button', ...props }: ButtonProps) {
  const base = 'inline-flex items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500/30 disabled:opacity-60'
  const variants = {
    primary: 'bg-brand-600 text-white hover:bg-brand-700',
    secondary: 'bg-slate-100 text-slate-800 hover:bg-slate-200',
    ghost: 'bg-transparent text-slate-700 hover:bg-slate-100',
    outline: 'border border-slate-200 bg-white text-slate-800 hover:bg-slate-50'
  }

  return (
    <button type={type} className={`${base} ${variants[variant]} ${className}`} {...props}>
      {icon}
      {children}
    </button>
  )
}
