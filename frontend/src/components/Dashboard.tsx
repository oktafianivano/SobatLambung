import { apiUrl } from '../services/api';
import React, { useState } from 'react';
import { UserProfile } from '../types';
import { STATIC_SCHEDULES } from '../logic/sobatLambung';
import { WhatsAppPhoneMockup } from './WhatsAppPhoneMockup';
import {
  Bell,
  BellOff,
  Clock,
  ShieldCheck,
  CheckCircle2,
  Lock,
  Utensils,
  Smartphone,
  Info,
  CalendarCheck
} from 'lucide-react';

interface DashboardProps {
  currentUser: UserProfile;
  onUpdateUser: (updatedUser: UserProfile) => void;
  onOpenAuth: (mode: 'login' | 'register') => void;
}

export const Dashboard: React.FC<DashboardProps> = ({
  currentUser,
  onUpdateUser,
  onOpenAuth,
}) => {
  const [isUpdating, setIsUpdating] = useState(false);
  const [isSendingTest, setIsSendingTest] = useState(false);
  const [toggleFeedback, setToggleFeedback] = useState<string | null>(null);

  const handleSendTestNotification = async () => {
    setIsSendingTest(true);
    setToggleFeedback(null);
    try {
      const response = await fetch(`${apiUrl('/user/test-notification')}?meal_key=breakfast`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${currentUser.token}`,
          'Content-Type': 'application/json'
        },
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Gagal mengirim test');
      
      setToggleFeedback('✅ Pesan tes berhasil dikirim ke WhatsApp Anda!');
    } catch (err: any) {
      setToggleFeedback(`❌ Error: ${err.message}`);
    } finally {
      setIsSendingTest(false);
      setTimeout(() => setToggleFeedback(null), 5000);
    }
  };

  const handleToggleAlarm = () => {
    setIsUpdating(true);
    const newStatus = !currentUser.is_alarm_active;

    // Simulate backend PUT /api/user/toggle-alarm
    setTimeout(() => {
      setIsUpdating(false);
      onUpdateUser({
        ...currentUser,
        is_alarm_active: newStatus,
      });
      setToggleFeedback(
        newStatus
          ? 'Layanan pengingat WhatsApp diaktifkan! Server Cron Job akan mengirim pesan setiap jam makan.'
          : 'Layanan pengingat dinonaktifkan. Anda tidak akan menerima pesan broadcast sampai diaktifkan kembali.'
      );
      setTimeout(() => setToggleFeedback(null), 3500);
    }, 300);
  };

  return (
    <div className="space-y-8">
      {/* Dashboard Top Header & Welcome */}
      <div className="bg-linear-to-r from-emerald-900 via-teal-900 to-slate-900 rounded-3xl p-6 sm:p-8 text-white shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-semibold mb-2">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Dasbor Privat Mahasiswa Terverifikasi</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
              Halo, {currentUser.nama}! 👋
            </h1>
            <p className="text-emerald-100/80 text-xs sm:text-sm mt-1">
              Nomor WhatsApp Terhubung: <span className="font-mono font-bold text-white">+{currentUser.no_wa}</span>
            </p>
          </div>

          {/* Big Interactive Toggle Switch */}
          <div className="bg-white/10 backdrop-blur-md border border-white/20 p-4 sm:p-5 rounded-2xl flex flex-col gap-4 min-w-70">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-xs font-bold text-white uppercase tracking-wider">
                  Status Alarm Pengingat
                </p>
                <p className="text-[11px] text-emerald-200 mt-0.5">
                  {currentUser.is_alarm_active ? '● Mengirim Pesan WhatsApp' : '○ Dinonaktifkan'}
                </p>
              </div>

              <button
                onClick={handleToggleAlarm}
                disabled={isUpdating}
                className={`relative inline-flex h-8 w-16 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-hidden ${
                  currentUser.is_alarm_active ? 'bg-emerald-500' : 'bg-slate-600'
                }`}
              >
                <span className="sr-only">Toggle Alarm WhatsApp</span>
                <span
                  className={`pointer-events-none inline-block h-7 w-7 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                    currentUser.is_alarm_active ? 'translate-x-8' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>
            
            <button
              onClick={handleSendTestNotification}
              disabled={isSendingTest || !currentUser.is_alarm_active}
              className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-[10px] font-bold rounded-lg transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              {isSendingTest ? 'Mengirim...' : 'Kirim Tes Notifikasi WA'}
            </button>
          </div>
        </div>

        {toggleFeedback && (
          <div className="mt-4 p-3 rounded-xl bg-white/15 text-xs text-emerald-100 flex items-center gap-2 border border-white/20 animate-fade-in">
            <Info className="w-4 h-4 shrink-0 text-emerald-300" />
            <span>{toggleFeedback}</span>
          </div>
        )}
      </div>

      {/* Static Alarm Schedule Section */}
      <section className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-xs space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4">
          <div>
            <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-emerald-700 bg-emerald-100 px-2.5 py-0.5 rounded-full mb-1">
              <Clock className="w-3.5 h-3.5" />
              Sesuai Standar Medis Gastroentero-Hepatologi
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-slate-900">
              Jadwal Alarm Makan Harian (Statis)
            </h2>
            <p className="text-xs sm:text-sm text-slate-500">
              Jadwal ini dikontrol penuh oleh sistem secara otomatis dan tidak dapat diubah mahasiswa demi konsistensi ritme sirkadian lambung.
            </p>
          </div>

          <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs font-semibold self-start sm:self-auto">
            <Lock className="w-3.5 h-3.5 text-amber-600" />
            <span>Jadwal Terkunci (Sistem Sentral)</span>
          </div>
        </div>

        {/* 3 Static Time Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {STATIC_SCHEDULES.map((item) => (
            <div
              key={item.id}
              className="rounded-2xl border border-slate-200 bg-linear-to-b from-slate-50/60 to-white p-5 flex flex-col justify-between hover:border-emerald-300 transition-all shadow-xs"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-bold px-2.5 py-1 rounded-lg bg-emerald-100 text-emerald-800 font-mono">
                    {item.time}
                  </span>
                  <div className="flex items-center gap-1 text-[11px] text-slate-400 font-medium">
                    <Lock className="w-3 h-3 text-slate-400" />
                    <span>Statis</span>
                  </div>
                </div>

                <h3 className="font-bold text-base text-slate-900 mb-1">{item.label}</h3>
                <p className="text-xs text-slate-600 mb-4">{item.shortDesc}</p>

                <div className="p-3 rounded-xl bg-emerald-50/60 border border-emerald-100 mb-4">
                  <p className="text-[11px] font-bold text-emerald-900 mb-1 flex items-center gap-1">
                    <Utensils className="w-3 h-3 text-emerald-700" />
                    Rekomendasi Menu Mahasiswa:
                  </p>
                  <ul className="text-[11px] text-slate-700 space-y-1 list-disc list-inside">
                    {item.recommendedMenus.map((menu, mIdx) => (
                      <li key={mIdx} className="leading-snug">{menu}</li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100 text-[11px] text-slate-500">
                <span className="font-semibold text-slate-700">Rasional Medis: </span>
                {item.medicalRationale}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* WhatsApp Delivery Simulation Phone Mockup */}
      <WhatsAppPhoneMockup
        userName={currentUser.nama}
        isAlarmActive={currentUser.is_alarm_active}
        userPhone={currentUser.no_wa}
      />
    </div>
  );
};
