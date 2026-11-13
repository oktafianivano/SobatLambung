import React, { useEffect, useState } from 'react';
import { apiUrl } from '../services/api';
import { UserProfile } from '../types';
import { normalizeWhatsAppNumber, validatePassword } from '../logic/sobatLambung';
import { PasswordInput } from './PasswordInput';
import {
  Phone,
  User as UserIcon,
  ShieldCheck,
  Save,
  KeyRound,
  LogOut,
  CheckCircle2,
  AlertCircle,
  Info,
  Lock,
  Settings2,
} from 'lucide-react';

interface AccountSettingsProps {
  currentUser: UserProfile;
  onUpdateUser: (updatedUser: UserProfile) => void;
  onLogout: () => void;
}

type Feedback = { type: 'success' | 'error'; text: string } | null;

export const AccountSettings: React.FC<AccountSettingsProps> = ({
  currentUser,
  onUpdateUser,
  onLogout,
}) => {
  // Form profil
  const [nama, setNama] = useState(currentUser.nama);
  const [noWa, setNoWa] = useState(currentUser.no_wa);
  const [profilePassword, setProfilePassword] = useState('');
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [profileFeedback, setProfileFeedback] = useState<Feedback>(null);

  // Form keamanan
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSavingPassword, setIsSavingPassword] = useState(false);
  const [passwordFeedback, setPasswordFeedback] = useState<Feedback>(null);

  useEffect(() => {
    setNama(currentUser.nama);
    setNoWa(currentUser.no_wa);
  }, [currentUser.id, currentUser.nama, currentUser.no_wa]);

  const handleSaveProfile = (e: React.FormEvent) => {
    e.preventDefault();
    setProfileFeedback(null);

    if (!currentUser.token) {
      setProfileFeedback({ type: 'error', text: 'Sesi login tidak ditemukan. Silakan login ulang.' });
      return;
    }

    if (!nama.trim() || nama.trim().length < 2) {
      setProfileFeedback({ type: 'error', text: 'Nama lengkap minimal 2 karakter.' });
      return;
    }

    const phoneCheck = normalizeWhatsAppNumber(noWa);
    if (!phoneCheck.isValid) {
      setProfileFeedback({ type: 'error', text: phoneCheck.error || 'Nomor WhatsApp tidak valid.' });
      return;
    }

    if (!profilePassword) {
      setProfileFeedback({ type: 'error', text: 'Masukkan kata sandi saat ini untuk mengonfirmasi perubahan.' });
      return;
    }

    setIsSavingProfile(true);
    fetch(apiUrl('/user/profile'), {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${currentUser.token}`,
      },
      body: JSON.stringify({
        nama: nama.trim(),
        no_wa: phoneCheck.formatted,
        current_password: profilePassword,
      }),
    })
      .then(async (res) => {
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Gagal menyimpan perubahan profil.');

        onUpdateUser({ ...data, token: currentUser.token });
        setProfilePassword('');
        setProfileFeedback({ type: 'success', text: 'Profil berhasil diperbarui.' });
      })
      .catch((err) => setProfileFeedback({ type: 'error', text: err.message }))
      .finally(() => setIsSavingProfile(false));
  };

  const handleChangePassword = (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordFeedback(null);

    if (!currentUser.token) {
      setPasswordFeedback({ type: 'error', text: 'Sesi login tidak ditemukan. Silakan login ulang.' });
      return;
    }

    if (!currentPassword) {
      setPasswordFeedback({ type: 'error', text: 'Masukkan kata sandi saat ini.' });
      return;
    }

    const pwdCheck = validatePassword(newPassword);
    if (!pwdCheck.isValid) {
      setPasswordFeedback({ type: 'error', text: pwdCheck.error || 'Kata sandi baru tidak valid.' });
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordFeedback({ type: 'error', text: 'Konfirmasi kata sandi baru tidak cocok.' });
      return;
    }

    setIsSavingPassword(true);
    fetch(apiUrl('/user/change-password'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${currentUser.token}`,
      },
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    })
      .then(async (res) => {
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Gagal memperbarui kata sandi.');

        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
        if (data.access_token) {
          onUpdateUser({ ...currentUser, token: data.access_token });
        }
        setPasswordFeedback({ type: 'success', text: data.message || 'Kata sandi berhasil diperbarui.' });
      })
      .catch((err) => setPasswordFeedback({ type: 'error', text: err.message }))
      .finally(() => setIsSavingPassword(false));
  };

  const feedbackBox = (feedback: Feedback) => {
    if (!feedback) return null;
    const isSuccess = feedback.type === 'success';
    return (
      <div
        className={`p-3 rounded-xl border text-xs flex items-center gap-2 ${
          isSuccess
            ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
            : 'bg-rose-50 border-rose-200 text-rose-800'
        }`}
      >
        {isSuccess ? (
          <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
        ) : (
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
        )}
        <span>{feedback.text}</span>
      </div>
    );
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-linear-to-r from-emerald-900 via-teal-900 to-slate-900 rounded-3xl p-6 sm:p-8 text-white shadow-lg">
        <div className="flex flex-col sm:flex-row sm:items-center gap-5">
          <div className="w-16 h-16 rounded-2xl bg-white/15 border border-white/20 flex items-center justify-center text-2xl font-extrabold">
            {currentUser.nama.charAt(0).toUpperCase()}
          </div>
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-semibold mb-2">
              <Settings2 className="w-3.5 h-3.5" />
              <span>Pengaturan Akun</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold break-words">{currentUser.nama}</h1>
            <p className="text-emerald-100/80 text-xs sm:text-sm mt-1 break-all">
              Nomor WhatsApp Terhubung: <span className="font-mono font-bold text-white">+{currentUser.no_wa}</span>
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Profil */}
        <section className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-xs space-y-5">
          <div className="flex items-start gap-3 border-b border-slate-100 pb-4">
            <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
              <UserIcon className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">Informasi Profil</h2>
              <p className="text-xs text-slate-500">
                Perbarui nama tampilan dan nomor WhatsApp tujuan pengingat.
              </p>
            </div>
          </div>

          {feedbackBox(profileFeedback)}

          <form onSubmit={handleSaveProfile} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Nama Lengkap</label>
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

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Nomor WhatsApp</label>
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
                Nomor ini dipakai untuk login dan menerima pengingat makan dari sistem.
              </p>
            </div>

            <div className="pt-3 border-t border-slate-100 space-y-2">
              <label className="block text-xs font-bold text-slate-700">
                Konfirmasi Kata Sandi Saat Ini
              </label>
              <PasswordInput
                value={profilePassword}
                onChange={setProfilePassword}
                placeholder="Masukkan kata sandi Anda"
                autoComplete="current-password"
                icon={<Lock className="w-4 h-4" />}
              />
              <p className="text-[11px] text-slate-400 flex items-start gap-1">
                <Info className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                Demi keamanan, perubahan nama dan nomor WhatsApp wajib dikonfirmasi dengan kata sandi Anda.
              </p>
            </div>

            <button
              type="submit"
              disabled={isSavingProfile}
              className="w-full py-3 rounded-xl bg-linear-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-bold text-sm shadow-md shadow-emerald-600/30 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              {isSavingProfile ? 'Menyimpan...' : 'Simpan Perubahan Profil'}
            </button>
          </form>
        </section>

        {/* Keamanan */}
        <section className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-xs space-y-5">
          <div className="flex items-start gap-3 border-b border-slate-100 pb-4">
            <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">Keamanan Akun</h2>
              <p className="text-xs text-slate-500">
                Ganti kata sandi secara berkala agar akun tetap aman.
              </p>
            </div>
          </div>

          {feedbackBox(passwordFeedback)}

          <form onSubmit={handleChangePassword} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Kata Sandi Saat Ini</label>
              <PasswordInput
                value={currentPassword}
                onChange={setCurrentPassword}
                placeholder="Masukkan kata sandi saat ini"
                autoComplete="current-password"
                icon={<Lock className="w-4 h-4" />}
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Kata Sandi Baru</label>
              <PasswordInput
                value={newPassword}
                onChange={setNewPassword}
                placeholder="Minimal 6 karakter"
                autoComplete="new-password"
                icon={<KeyRound className="w-4 h-4" />}
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
              disabled={isSavingPassword}
              className="w-full py-3 rounded-xl bg-linear-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-bold text-sm shadow-md shadow-emerald-600/30 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
            >
              <ShieldCheck className="w-4 h-4" />
              {isSavingPassword ? 'Memperbarui...' : 'Perbarui Kata Sandi'}
            </button>
          </form>

          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-[11px] text-slate-600 space-y-1">
            <p className="font-bold text-slate-700">Tips keamanan:</p>
            <ul className="list-disc list-inside space-y-0.5">
              <li>Gunakan kombinasi huruf, angka, dan simbol.</li>
              <li>Jangan bagikan kata sandi atau kode OTP kepada siapa pun.</li>
              <li>Kata sandi baru tidak boleh sama dengan kata sandi lama.</li>
            </ul>
          </div>
        </section>
      </div>

      {/* Sesi */}
      <section className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-slate-900">Sesi Perangkat Ini</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Keluar dari akun pada perangkat ini. Anda perlu login kembali untuk mengakses dasbor.
          </p>
        </div>
        <button
          type="button"
          onClick={onLogout}
          className="px-5 py-2.5 rounded-xl border border-rose-200 bg-rose-50 hover:bg-rose-100 text-rose-700 font-bold text-xs flex items-center justify-center gap-2 transition-colors cursor-pointer shrink-0"
        >
          <LogOut className="w-4 h-4" />
          Keluar dari Akun
        </button>
      </section>
    </div>
  );
};
