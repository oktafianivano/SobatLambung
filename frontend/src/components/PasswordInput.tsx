import React, { useState } from 'react';
import { Eye, EyeOff, Lock } from 'lucide-react';

interface PasswordInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  required?: boolean;
  autoComplete?: string;
  icon?: React.ReactNode;
  disabled?: boolean;
}

/**
 * Input kata sandi dengan tombol tampilkan/sembunyikan (ikon mata).
 * Dipakai ulang di modal autentikasi, reset sandi, dan halaman pengaturan.
 */
export const PasswordInput: React.FC<PasswordInputProps> = ({
  value,
  onChange,
  placeholder = 'Minimal 6 karakter',
  required = true,
  autoComplete,
  icon,
  disabled = false,
}) => {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div className="relative">
      <span className="absolute left-3 top-3 w-4 h-4 text-slate-400 pointer-events-none">
        {icon ?? <Lock className="w-4 h-4" />}
      </span>
      <input
        type={isVisible ? 'text' : 'password'}
        required={required}
        disabled={disabled}
        autoComplete={autoComplete}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full pl-9 pr-10 py-2.5 rounded-xl border border-slate-200 focus:outline-emerald-500 focus:border-emerald-500 text-sm text-slate-900 placeholder:text-slate-400 disabled:bg-slate-50 disabled:text-slate-500"
      />
      <button
        type="button"
        onClick={() => setIsVisible((prev) => !prev)}
        disabled={disabled}
        aria-label={isVisible ? 'Sembunyikan kata sandi' : 'Tampilkan kata sandi'}
        title={isVisible ? 'Sembunyikan kata sandi' : 'Tampilkan kata sandi'}
        className="absolute right-2.5 top-2.5 p-0.5 text-slate-400 hover:text-emerald-700 rounded transition-colors cursor-pointer disabled:cursor-not-allowed"
      >
        {isVisible ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
      </button>
    </div>
  );
};
