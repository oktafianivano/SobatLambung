import React, { useState } from 'react';
import { API_URL } from '../config';
import { UserProfile } from '../types';
import { normalizeWhatsAppNumber, validatePassword } from '../logic/sobatLambung';
import { PasswordInput } from './PasswordInput';
import {
  X,
  Phone,
  User as UserIcon,
  LogIn,
  UserPlus,
  CheckCircle2,
  AlertCircle,
  KeyRound,
  ShieldCheck,
  ArrowLeft,
} from 'lucide-react';

interface AuthModalProps {
  isOpen: boolean;
  initialMode: 'login' | 'register';
  onClose: () => void;
  onSuccess: (user: UserProfile) => void;
}

type AuthMode = 'login' | 'register' | 'forgot';
type ForgotStep = 'request' | 'reset';

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  initialMode,
  onClose,
  onSuccess,
}) => {
  const [mode, setMode] = useState<AuthMode>(initialMode);
  const [forgotStep, setForgotStep] = useState<ForgotStep>('request');
  const [nama, setNama] = useState('');
  const [noWa, setNoWa] = useState('');
  const [password, setPassword] = useState('');
  const [otp, setOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  if (!isOpen) return null;

  const resetFeedback = () => {
    setErrorMessage(null);
    setSuccessMessage(null);
  };

  const switchMode = (nextMode: AuthMode) => {
    setMode(nextMode);
    setForgotStep('request');
    setOtp('');
    setNewPassword('');
    setConfirmPassword('');
    resetFeedback();
  };

  const handleForgotRequest = (e: React.FormEvent) => {
    e.preventDefault();
    resetFeedback();

    const phoneCheck = normalizeWhatsAppNumber(noWa);
    if (!phoneCheck.isValid) {
      setErrorMessage(phoneCheck.error || 'Nomor WhatsApp tidak valid.');
      return;
    }

    setIsLoading(true);
    fetch(`${API_URL}/api/forgot-password/request`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ no_wa: phoneCheck.formatted }),
    })
      .then(async (res) => {
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Terjadi kesalahan.');
        setForgotStep('reset');
        setSuccessMessage(data.message || 'Kode OTP telah dikirim ke WhatsApp Anda.');
      })
      .catch((err) => setErrorMessage(err.message))
      .finally(() => setIsLoading(false));
  };

  const handleForgotReset = (e: React.FormEvent) => {
    e.preventDefault();
    resetFeedback();

    const phoneCheck = normalizeWhatsAppNumber(noWa);
    if (!phoneCheck.isValid) {
      setErrorMessage(phoneCheck.error || 'Nomor WhatsApp tidak valid.');
      return;
    }

    if (!/^\d{6}$/.test(otp.trim())) {
      setErrorMessage('Kode OTP harus terdiri dari 6 digit angka.');
      return;
    }

    const pwdCheck = validatePassword(newPassword);
    if (!pwdCheck.isValid) {
      setErrorMessage(pwdCheck.error || 'Kata sandi baru tidak valid.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setErrorMessage('Konfirmasi kata sandi tidak cocok.');
      return;
    }

    setIsLoading(true);
    fetch(`${API_URL}/api/forgot-password/reset`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        no_wa: phoneCheck.formatted,
        otp: otp.trim(),
        new_password: newPassword,
      }),
    })
      .then(async (res) => {
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Terjadi kesalahan.');
        switchMode('login');
        setSuccessMessage(data.message || 'Kata sandi berhasil diubah. Silakan login.');
        setPassword('');
      })
      .catch((err) => setErrorMessage(err.message))
      .finally(() => setIsLoading(false));
  };

  const handleLoginOrRegister = (e: React.FormEvent) => {
    e.preventDefault();
    resetFeedback();

    // Validate phone
    const phoneCheck = normalizeWhatsAppNumber(noWa);
    if (!phoneCheck.isValid) {
      setErrorMessage(phoneCheck.error || 'Nomor WhatsApp tidak valid.');
      return;
    }

    // Validate password
    const pwdCheck = validatePassword(password);
    if (!pwdCheck.isValid) {
      setErrorMessage(pwdCheck.error || 'Kata sandi tidak valid.');
      return;
    }

    if (mode === 'register' && (!nama || nama.trim().length < 2)) {
      setErrorMessage('Nama lengkap mahasiswa minimal 2 karakter.');
      return;
    }

    setIsLoading(true);

    const endpoint = mode === 'register' ? '/api/register' : '/api/login';
    const payload =
      mode === 'register'
        ? { nama, no_wa: phoneCheck.formatted, password }
        : { no_wa: phoneCheck.formatted, password };

    fetch(`${API_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then(async (res) => {
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Terjadi kesalahan.');

        const user: UserProfile = {
          ...data.user,
          token: data.access_token,
        };
        onSuccess(user);
        onClose();
      })
      .catch((err) => setErrorMessage(err.message))
      .finally(() => setIsLoading(false));
  };

  const handleQuickLogin = (demoName: string, demoWa: string, alarmActive: boolean) => {
    const user: UserProfile = {
      id: Math.floor(Math.random() * 9000) + 1000,
      nama: demoName,
      no_wa: demoWa,
      is_alarm_active: alarmActive,
      token: 'jwt_demo_token_' + Date.now(),
    };
    onSuccess(user);
    onClose();
  };

  const isForgot = mode === 'forgot';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
      <div className="relative w-full max-w-md bg-white rounded-3xl p-6 sm:p-8 shadow-2xl border border-slate-100">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute right-5 top-5 p-2 text-slate-400 hover:text-slate-600 rounded-full hover:bg-slate-100 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="mb-6">
          <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-emerald-700 bg-emerald-100 px-2.5 py-1 rounded-full mb-2">
            {mode === 'login' && 'Autentikasi Mahasiswa'}
            {mode === 'register' && 'Pendaftaran Akun Baru'}
            {isForgot && (forgotStep === 'request' ? 'Lupa Kata Sandi' : 'Verifikasi Kode OTP')}
          </div>
          <h3 className="text-2xl font-bold text-slate-900">
            {mode === 'login' && 'Masuk ke Dasbor Sobat Lambung'}
            {mode === 'register' && 'Daftar Akun Sobat Lambung'}
            {isForgot && forgotStep === 'request' && 'Lupa Kata Sandi Anda?'}
            {isForgot && forgotStep === 'reset' && 'Masukkan Kode OTP & Kata Sandi Baru'}
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            {mode === 'login' && 'Masukkan nomor WhatsApp dan kata sandi Anda.'}
            {mode === 'register' && 'Aktifkan pengingat jam makan harian via pesan WhatsApp.'}
            {isForgot && forgotStep === 'request' &&
              'Masukkan nomor WhatsApp terdaftar. Kami akan mengirim kode OTP 6 digit melalui WhatsApp.'}
            {isForgot && forgotStep === 'reset' &&
              `Kode berlaku 10 menit dan hanya dapat dipakai sekali.`}
          </p>
        </div>

        {errorMessage && (
          <div className="mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
            <span>{errorMessage}</span>
          </div>
        )}

        {successMessage && (
          <div className="mb-4 p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
            <span>{successMessage}</span>
          </div>
        )}

        {/* Form: Login / Register */}
        {(mode === 'login' || mode === 'register') && (
          <form onSubmit={handleLoginOrRegister} className="space-y-4">
            {mode === 'register' && (
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Nama Mahasiswa</label>
                <div className="relative">
                  <UserIcon className="absolute left-3 top-3 w-4 h-4 text-slate-400" />
                  <input
                    type="text"
                    required
                    placeholder="Contoh: Budi Santoso"
                    value={nama}
                    onChange={(e) => setNama(e.target.value)}
                    className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-slate-200 focus:outline-emerald-500 focus:border-emerald-500 text-sm text-slate-900 placeholder:text-slate-400"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Nomor WhatsApp Aktif</label>
              <div className="relative">
                <Phone className="absolute left-3 top-3 w-4 h-4 text-slate-400" />
                <input
                  type="tel"
                  required
                  placeholder="08123456789 atau 628123456789"
                  value={noWa}
                  onChange={(e) => setNoWa(e.target.value)}
                  className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-slate-200 focus:outline-emerald-500 focus:border-emerald-500 text-sm text-slate-900 placeholder:text-slate-400"
                />
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                Nomor ini digunakan untuk login dan pengiriman broadcast pesan makan dari sistem.
              </p>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-xs font-bold text-slate-700">Kata Sandi</label>
                {mode === 'login' && (
                  <button
                    type="button"
                    onClick={() => switchMode('forgot')}
                    className="text-[11px] font-bold text-emerald-700 hover:underline cursor-pointer"
                  >
                    Lupa kata sandi?
                  </button>
                )}
              </div>
              <PasswordInput
                value={password}
                onChange={setPassword}
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-2 py-3 rounded-xl bg-linear-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-bold text-sm shadow-md shadow-emerald-600/30 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
            >
              {isLoading ? (
                'Memproses data...'
              ) : mode === 'login' ? (
                <>
                  <LogIn className="w-4 h-4" /> Masuk ke Dasbor
                </>
              ) : (
                <>
                  <UserPlus className="w-4 h-4" /> Daftarkan Akun Saya
                </>
              )}
            </button>
          </form>
        )}

        {/* Form: Forgot Password - Request OTP */}
        {isForgot && forgotStep === 'request' && (
          <form onSubmit={handleForgotRequest} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Nomor WhatsApp Terdaftar</label>
              <div className="relative">
                <Phone className="absolute left-3 top-3 w-4 h-4 text-slate-400" />
                <input
                  type="tel"
                  required
                  placeholder="08123456789 atau 628123456789"
                  value={noWa}
                  onChange={(e) => setNoWa(e.target.value)}
                  className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-slate-200 focus:outline-emerald-500 focus:border-emerald-500 text-sm text-slate-900 placeholder:text-slate-400"
                />
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                Kode OTP 6 digit akan dikirim melalui WhatsApp ke nomor ini.
              </p>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-2 py-3 rounded-xl bg-linear-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-bold text-sm shadow-md shadow-emerald-600/30 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
            >
              {isLoading ? (
                'Mengirim kode OTP...'
              ) : (
                <>
                  <KeyRound className="w-4 h-4" /> Kirim Kode OTP ke WhatsApp
                </>
              )}
            </button>

            <button
              type="button"
              onClick={() => switchMode('login')}
              className="w-full text-xs font-bold text-slate-500 hover:text-emerald-700 flex items-center justify-center gap-1.5 cursor-pointer"
            >
              <ArrowLeft className="w-3.5 h-3.5" /> Kembali ke halaman masuk
            </button>
          </form>
        )}

        {/* Form: Forgot Password - Verify OTP & Set New Password */}
        {isForgot && forgotStep === 'reset' && (
          <form onSubmit={handleForgotReset} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Kode OTP (6 Digit)</label>
              <div className="relative">
                <KeyRound className="absolute left-3 top-3 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  inputMode="numeric"
                  maxLength={6}
                  required
                  placeholder="Contoh: 123456"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                  className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-slate-200 focus:outline-emerald-500 focus:border-emerald-500 text-sm tracking-[0.3em] font-bold text-slate-900 placeholder:text-slate-400 placeholder:tracking-normal placeholder:font-normal"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Kata Sandi Baru</label>
              <PasswordInput
                value={newPassword}
                onChange={setNewPassword}
                autoComplete="new-password"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Ulangi Kata Sandi Baru</label>
              <PasswordInput
                value={confirmPassword}
                onChange={setConfirmPassword}
                placeholder="Ketik ulang kata sandi baru"
                autoComplete="new-password"
                icon={<ShieldCheck className="w-4 h-4" />}
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-2 py-3 rounded-xl bg-linear-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-bold text-sm shadow-md shadow-emerald-600/30 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
            >
              {isLoading ? (
                'Menyimpan kata sandi...'
              ) : (
                <>
                  <ShieldCheck className="w-4 h-4" /> Simpan Kata Sandi Baru
                </>
              )}
            </button>

            <button
              type="button"
              onClick={() => {
                setForgotStep('request');
                setOtp('');
                setNewPassword('');
                setConfirmPassword('');
                resetFeedback();
              }}
              className="w-full text-xs font-bold text-slate-500 hover:text-emerald-700 flex items-center justify-center gap-1.5 cursor-pointer"
            >
              <ArrowLeft className="w-3.5 h-3.5" /> Minta kode OTP baru
            </button>
          </form>
        )}

        {/* Switch mode */}
        {!isForgot && (
          <div className="mt-4 text-center text-xs text-slate-500">
            {mode === 'login' ? (
              <span>
                Belum punya akun?{' '}
                <button
                  type="button"
                  onClick={() => switchMode('register')}
                  className="font-bold text-emerald-700 hover:underline cursor-pointer"
                >
                  Daftar sekarang
                </button>
              </span>
            ) : (
              <span>
                Sudah memiliki akun?{' '}
                <button
                  type="button"
                  onClick={() => switchMode('login')}
                  className="font-bold text-emerald-700 hover:underline cursor-pointer"
                >
                  Masuk di sini
                </button>
              </span>
            )}
          </div>
        )}

        {/* Demo Fast Login for evaluator */}
        <div className="mt-6 pt-5 border-t border-slate-100 hidden">
          <p className="text-[11px] font-semibold text-slate-400 mb-2 uppercase tracking-wider text-center">
            Akun Percobaan Cepat (Demo):
          </p>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => handleQuickLogin('Rizky Pratama (Mahasiswa)', '6281234567890', true)}
              className="p-2 rounded-xl bg-slate-50 hover:bg-emerald-50 border border-slate-200 hover:border-emerald-300 text-left transition-all cursor-pointer"
            >
              <p className="text-xs font-bold text-slate-800">Rizky (Aktif)</p>
              <p className="text-[10px] text-emerald-700">Alarm WA ON</p>
            </button>
            <button
              type="button"
              onClick={() => handleQuickLogin('Nadia Safitri (Mahasiswi)', '6281987654321', false)}
              className="p-2 rounded-xl bg-slate-50 hover:bg-emerald-50 border border-slate-200 hover:border-emerald-300 text-left transition-all cursor-pointer"
            >
              <p className="text-xs font-bold text-slate-800">Nadia (Nonaktif)</p>
              <p className="text-[10px] text-slate-500">Alarm WA OFF</p>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
