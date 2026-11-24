
import React, { useEffect, useState } from 'react';
import { apiUrl } from '../services/api';
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

type AuthMode = 'login' | 'register' | 'forgot' | 'verify';
type ForgotStep = 'request' | 'reset';

const RESEND_COOLDOWN_SECONDS = 60;

const maskPhone = (value: string): string => {
  const digits = value.replace(/\D/g, '');
  if (!digits) return '';
  if (digits.length <= 6) return '*'.repeat(digits.length);

  const hidden = Math.max(2, digits.length - 8);
  return `${digits.slice(0, 4)}${'*'.repeat(hidden)}${digits.slice(-4)}`;
};

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

  const [pendingWa, setPendingWa] = useState('');
  const [pendingMasked, setPendingMasked] = useState('');
  const [resendCountdown, setResendCountdown] = useState(0);

  useEffect(() => {
    if (resendCountdown <= 0) return;

    const timer = setTimeout(
      () => setResendCountdown((prev) => prev - 1),
      1000
    );

    return () => clearTimeout(timer);
  }, [resendCountdown]);

  useEffect(() => {
    if (isOpen) {
      setMode(initialMode);
      setForgotStep('request');
      setErrorMessage(null);
      setSuccessMessage(null);
    }
  }, [isOpen, initialMode]);

  if (!isOpen) return null;

  const resetFeedback = () => {
    setErrorMessage(null);
    setSuccessMessage(null);
  };

  const startVerification = (
    formattedWa: string,
    masked: string,
    message?: string
  ) => {
    setPendingWa(formattedWa);
    setPendingMasked(masked || maskPhone(formattedWa));
    setOtp('');
    setResendCountdown(RESEND_COOLDOWN_SECONDS);
    setMode('verify');
    setErrorMessage(null);

    setSuccessMessage(
      message ||
        'Kode OTP 6 digit telah dikirim ke WhatsApp Anda. Masukkan kode tersebut untuk mengaktifkan akun.'
    );
  };

  const switchMode = (nextMode: AuthMode) => {
    setMode(nextMode);
    setForgotStep('request');
    setOtp('');
    setNewPassword('');
    setConfirmPassword('');
    resetFeedback();
  };

  // Request OTP untuk lupa password
  const handleForgotRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    resetFeedback();

    const phoneCheck = normalizeWhatsAppNumber(noWa);

    if (!phoneCheck.isValid) {
      setErrorMessage(phoneCheck.error || 'Nomor WhatsApp tidak valid.');
      return;
    }

    setIsLoading(true);

    try {
      const res = await fetch(apiUrl('/auth/forgot-password/request'), {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          no_wa: phoneCheck.formatted,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || 'Terjadi kesalahan.');
      }

      setForgotStep('reset');
      setSuccessMessage(
        data.message || 'Kode OTP telah dikirim ke WhatsApp Anda.'
      );
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : 'Terjadi kesalahan.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Reset password menggunakan OTP
  const handleForgotReset = async (e: React.FormEvent) => {
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

    try {
      const res = await fetch(apiUrl('/auth/forgot-password/reset'), {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          no_wa: phoneCheck.formatted,
          otp: otp.trim(),
          new_password: newPassword,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || 'Terjadi kesalahan.');
      }

      switchMode('login');
      setSuccessMessage(
        data.message || 'Kata sandi berhasil diubah. Silakan login.'
      );
      setPassword('');
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : 'Terjadi kesalahan.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Login dan registrasi
  const handleLoginOrRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    resetFeedback();

    const phoneCheck = normalizeWhatsAppNumber(noWa);

    if (!phoneCheck.isValid) {
      setErrorMessage(phoneCheck.error || 'Nomor WhatsApp tidak valid.');
      return;
    }

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

    const endpoint =
      mode === 'register' ? '/auth/register' : '/auth/login';

    const payload =
      mode === 'register'
        ? {
            nama: nama.trim(),
            no_wa: phoneCheck.formatted,
            password,
          }
        : {
            no_wa: phoneCheck.formatted,
            password,
          };

    try {
      const res = await fetch(apiUrl(endpoint), {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      // Akun belum diverifikasi
      if (res.status === 403 && mode === 'login') {
        startVerification(
          phoneCheck.formatted,
          maskPhone(phoneCheck.formatted),
          data.detail
        );
        return;
      }

      if (!res.ok) {
        throw new Error(data.detail || 'Terjadi kesalahan.');
      }

      // Registrasi membutuhkan verifikasi OTP
      if (mode === 'register' && data.requires_verification) {
        startVerification(
          phoneCheck.formatted,
          data.no_wa_masked,
          data.message
        );
        return;
      }

      // Autentikasi menggunakan HttpOnly Cookie.
      // Tidak ada token yang disimpan di JavaScript.
      if (!data.user) {
        throw new Error('Data pengguna tidak ditemukan pada respons server.');
      }

      onSuccess(data.user as UserProfile);
      onClose();
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : 'Terjadi kesalahan.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Verifikasi OTP registrasi
  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    resetFeedback();

    if (!/^\d{6}$/.test(otp.trim())) {
      setErrorMessage('Kode OTP harus terdiri dari 6 digit angka.');
      return;
    }

    setIsLoading(true);

    try {
      const res = await fetch(apiUrl('/auth/register/verify'), {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          no_wa: pendingWa,
          otp: otp.trim(),
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || 'Terjadi kesalahan.');
      }

      if (!data.user) {
        throw new Error('Data pengguna tidak ditemukan pada respons server.');
      }

      // Browser menerima cookie autentikasi secara otomatis.
      onSuccess(data.user as UserProfile);
      onClose();
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : 'Terjadi kesalahan.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Kirim ulang OTP
  const handleResendOtp = async () => {
    if (resendCountdown > 0 || isLoading) return;

    resetFeedback();
    setIsLoading(true);

    try {
      const res = await fetch(apiUrl('/auth/register/resend'), {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          no_wa: pendingWa,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || 'Terjadi kesalahan.');
      }

      setOtp('');
      setResendCountdown(RESEND_COOLDOWN_SECONDS);

      setSuccessMessage(
        data.message || 'Kode OTP baru telah dikirim ke WhatsApp Anda.'
      );
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : 'Terjadi kesalahan.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const isForgot = mode === 'forgot';

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto overscroll-contain bg-slate-900/60 backdrop-blur-xs">
      <div className="flex min-h-full items-center justify-center p-3 sm:p-4">
        <div className="relative my-4 w-full max-w-md rounded-3xl border border-slate-100 bg-white p-5 shadow-2xl sm:p-8">

          {/* Close Button */}
          <button
            onClick={onClose}
            aria-label="Tutup"
            className="absolute right-4 top-4 rounded-full p-2 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 sm:right-5 sm:top-5"
          >
            <X className="h-5 w-5" />
          </button>

          {/* Modal Header */}
          <div className="mb-5 pr-8 sm:mb-6">
            <div className="mb-2 inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-bold uppercase tracking-wider text-emerald-700">
              {mode === 'login' && 'Autentikasi Mahasiswa'}
              {mode === 'register' && 'Pendaftaran Akun Baru'}
              {mode === 'verify' && 'Verifikasi Nomor WhatsApp'}
              {isForgot &&
                (forgotStep === 'request'
                  ? 'Lupa Kata Sandi'
                  : 'Verifikasi Kode OTP')}
            </div>

            <h3 className="text-xl font-bold text-slate-900 sm:text-2xl">
              {mode === 'login' && 'Masuk ke Dasbor Sobat Lambung'}
              {mode === 'register' && 'Daftar Akun Sobat Lambung'}
              {mode === 'verify' && 'Masukkan Kode OTP'}
              {isForgot &&
                forgotStep === 'request' &&
                'Lupa Kata Sandi Anda?'}
              {isForgot &&
                forgotStep === 'reset' &&
                'Masukkan Kode OTP & Kata Sandi Baru'}
            </h3>

            <p className="mt-1 text-xs text-slate-500">
              {mode === 'login' &&
                'Masukkan nomor WhatsApp dan kata sandi Anda.'}
              {mode === 'register' &&
                'Aktifkan pengingat jam makan harian via pesan WhatsApp.'}
              {mode === 'verify' &&
                `Kode 6 digit dikirim ke WhatsApp ${
                  pendingMasked || 'Anda'
                }. Kode berlaku 10 menit.`}
              {isForgot &&
                forgotStep === 'request' &&
                'Masukkan nomor WhatsApp terdaftar. Kami akan mengirim kode OTP 6 digit melalui WhatsApp.'}
              {isForgot &&
                forgotStep === 'reset' &&
                'Kode berlaku 10 menit dan hanya dapat dipakai sekali.'}
            </p>
          </div>

          {/* Error Message */}
          {errorMessage && (
            <div className="mb-4 flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Success Message */}
          {successMessage && (
            <div className="mb-4 flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-800">
              <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
              <span>{successMessage}</span>
            </div>
          )}

          {/* Login / Register */}
          {(mode === 'login' || mode === 'register') && (
            <form onSubmit={handleLoginOrRegister} className="space-y-4">
              {mode === 'register' && (
                <div>
                  <label className="mb-1 block text-xs font-bold text-slate-700">
                    Nama Mahasiswa
                  </label>

                  <div className="relative">
                    <UserIcon className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                    <input
                      type="text"
                      required
                      placeholder="Contoh: Budi Santoso"
                      value={nama}
                      onChange={(e) => setNama(e.target.value)}
                      className="w-full rounded-xl border border-slate-200 py-2.5 pl-9 pr-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-emerald-500 focus:outline-emerald-500"
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="mb-1 block text-xs font-bold text-slate-700">
                  Nomor WhatsApp Aktif
                </label>

                <div className="relative">
                  <Phone className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                  <input
                    type="tel"
                    required
                    placeholder="08123456789 atau 628123456789"
                    value={noWa}
                    onChange={(e) => setNoWa(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 py-2.5 pl-9 pr-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-emerald-500 focus:outline-emerald-500"
                  />
                </div>

                <p className="mt-1 text-[11px] text-slate-400">
                  Nomor ini digunakan untuk login dan pengiriman broadcast pesan makan dari sistem.
                </p>
              </div>

              <div>
                <div className="mb-1 flex items-center justify-between">
                  <label className="block text-xs font-bold text-slate-700">
                    Kata Sandi
                  </label>

                  {mode === 'login' && (
                    <button
                      type="button"
                      onClick={() => switchMode('forgot')}
                      className="cursor-pointer text-[11px] font-bold text-emerald-700 hover:underline"
                    >
                      Lupa kata sandi?
                    </button>
                  )}
                </div>

                <PasswordInput
                  value={password}
                  onChange={setPassword}
                  autoComplete={
                    mode === 'login' ? 'current-password' : 'new-password'
                  }
                />
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="mt-2 flex w-full cursor-pointer items-center justify-center gap-2 rounded-xl bg-linear-to-r from-emerald-600 to-teal-600 py-3 text-sm font-bold text-white shadow-md shadow-emerald-600/30 transition-all hover:from-emerald-700 hover:to-teal-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isLoading ? (
                  'Memproses data...'
                ) : mode === 'login' ? (
                  <>
                    <LogIn className="h-4 w-4" />
                    Masuk ke Dasbor
                  </>
                ) : (
                  <>
                    <UserPlus className="h-4 w-4" />
                    Daftarkan Akun Saya
                  </>
                )}
              </button>
            </form>
          )}

          {/* Registration OTP */}
          {mode === 'verify' && (
            <form onSubmit={handleVerifyOtp} className="space-y-4">
              <div>
                <label className="mb-1 block text-xs font-bold text-slate-700">
                  Kode OTP (6 Digit)
                </label>

                <div className="relative">
                  <KeyRound className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                  <input
                    type="text"
                    inputMode="numeric"
                    autoComplete="one-time-code"
                    maxLength={6}
                    required
                    placeholder="Contoh: 123456"
                    value={otp}
                    onChange={(e) =>
                      setOtp(e.target.value.replace(/\D/g, ''))
                    }
                    className="w-full rounded-xl border border-slate-200 py-2.5 pl-9 pr-3 text-sm font-bold tracking-[0.3em] text-slate-900 placeholder:font-normal placeholder:tracking-normal placeholder:text-slate-400 focus:border-emerald-500 focus:outline-emerald-500"
                  />
                </div>

                <p className="mt-1 text-[11px] text-slate-400">
                  Cek pesan WhatsApp dari Sobat Lambung. Jangan bagikan kode ini kepada siapa pun.
                </p>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="mt-2 flex w-full cursor-pointer items-center justify-center gap-2 rounded-xl bg-linear-to-r from-emerald-600 to-teal-600 py-3 text-sm font-bold text-white shadow-md shadow-emerald-600/30 transition-all hover:from-emerald-700 hover:to-teal-700 disabled:opacity-50"
              >
                {isLoading ? (
                  'Memverifikasi kode...'
                ) : (
                  <>
                    <ShieldCheck className="h-4 w-4" />
                    Verifikasi & Aktifkan Akun
                  </>
                )}
              </button>

              <button
                type="button"
                onClick={handleResendOtp}
                disabled={resendCountdown > 0 || isLoading}
                className="w-full cursor-pointer text-xs font-bold text-emerald-700 hover:underline disabled:cursor-not-allowed disabled:text-slate-400 disabled:no-underline"
              >
                {resendCountdown > 0
                  ? `Kirim ulang kode dalam ${resendCountdown} detik`
                  : 'Kirim ulang kode OTP'}
              </button>

              <button
                type="button"
                onClick={() => switchMode('login')}
                className="flex w-full cursor-pointer items-center justify-center gap-1.5 text-xs font-bold text-slate-500 hover:text-emerald-700"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                Kembali ke halaman masuk
              </button>
            </form>
          )}

          {/* Forgot Password - Request OTP */}
          {isForgot && forgotStep === 'request' && (
            <form onSubmit={handleForgotRequest} className="space-y-4">
              <div>
                <label className="mb-1 block text-xs font-bold text-slate-700">
                  Nomor WhatsApp Terdaftar
                </label>

                <div className="relative">
                  <Phone className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                  <input
                    type="tel"
                    required
                    placeholder="08123456789 atau 628123456789"
                    value={noWa}
                    onChange={(e) => setNoWa(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 py-2.5 pl-9 pr-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-emerald-500 focus:outline-emerald-500"
                  />
                </div>

                <p className="mt-1 text-[11px] text-slate-400">
                  Kode OTP 6 digit akan dikirim melalui WhatsApp ke nomor ini.
                </p>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="mt-2 flex w-full cursor-pointer items-center justify-center gap-2 rounded-xl bg-linear-to-r from-emerald-600 to-teal-600 py-3 text-sm font-bold text-white shadow-md shadow-emerald-600/30 transition-all hover:from-emerald-700 hover:to-teal-700 disabled:opacity-50"
              >
                {isLoading ? (
                  'Mengirim kode OTP...'
                ) : (
                  <>
                    <KeyRound className="h-4 w-4" />
                    Kirim Kode OTP ke WhatsApp
                  </>
                )}
              </button>

              <button
                type="button"
                onClick={() => switchMode('login')}
                className="flex w-full cursor-pointer items-center justify-center gap-1.5 text-xs font-bold text-slate-500 hover:text-emerald-700"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                Kembali ke halaman masuk
              </button>
            </form>
          )}

          {/* Forgot Password - Reset */}
          {isForgot && forgotStep === 'reset' && (
            <form onSubmit={handleForgotReset} className="space-y-4">
              <div>
                <label className="mb-1 block text-xs font-bold text-slate-700">
                  Kode OTP (6 Digit)
                </label>

                <div className="relative">
                  <KeyRound className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                  <input
                    type="text"
                    inputMode="numeric"
                    maxLength={6}
                    required
                    placeholder="Contoh: 123456"
                    value={otp}
                    onChange={(e) =>
                      setOtp(e.target.value.replace(/\D/g, ''))
                    }
                    className="w-full rounded-xl border border-slate-200 py-2.5 pl-9 pr-3 text-sm font-bold tracking-[0.3em] text-slate-900 placeholder:font-normal placeholder:tracking-normal placeholder:text-slate-400 focus:border-emerald-500 focus:outline-emerald-500"
                  />
                </div>
              </div>

              <div>
                <label className="mb-1 block text-xs font-bold text-slate-700">
                  Kata Sandi Baru
                </label>

                <PasswordInput
                  value={newPassword}
                  onChange={setNewPassword}
                  autoComplete="new-password"
                />
              </div>

              <div>
                <label className="mb-1 block text-xs font-bold text-slate-700">
                  Ulangi Kata Sandi Baru
                </label>

                <PasswordInput
                  value={confirmPassword}
                  onChange={setConfirmPassword}
                  placeholder="Ketik ulang kata sandi baru"
                  autoComplete="new-password"
                  icon={<ShieldCheck className="h-4 w-4" />}
                />
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="mt-2 flex w-full cursor-pointer items-center justify-center gap-2 rounded-xl bg-linear-to-r from-emerald-600 to-teal-600 py-3 text-sm font-bold text-white shadow-md shadow-emerald-600/30 transition-all hover:from-emerald-700 hover:to-teal-700 disabled:opacity-50"
              >
                {isLoading ? (
                  'Menyimpan kata sandi...'
                ) : (
                  <>
                    <ShieldCheck className="h-4 w-4" />
                    Simpan Kata Sandi Baru
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
                className="flex w-full cursor-pointer items-center justify-center gap-1.5 text-xs font-bold text-slate-500 hover:text-emerald-700"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                Minta kode OTP baru
              </button>
            </form>
          )}

          {/* Switch Mode */}
          {!isForgot && mode !== 'verify' && (
            <div className="mt-4 text-center text-xs text-slate-500">
              {mode === 'login' ? (
                <span>
                  Belum punya akun?{' '}
                  <button
                    type="button"
                    onClick={() => switchMode('register')}
                    className="cursor-pointer font-bold text-emerald-700 hover:underline"
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
                    className="cursor-pointer font-bold text-emerald-700 hover:underline"
                  >
                    Masuk di sini
                  </button>
                </span>
              )}
            </div>
          )}

        </div>
      </div>
    </div>
  );
};
