import React, { useState } from 'react';
import { HeartPulse, QrCode, Bell, ShieldCheck, ArrowRight, AlertTriangle, Coffee, Flame, CheckCircle2 } from 'lucide-react';
import { UserProfile } from '../types';

interface HeroEducationProps {
  currentUser: UserProfile | null;
  onOpenAuth: (mode: 'login' | 'register') => void;
  onNavigateTab: (tab: string) => void;
}

export const HeroEducation: React.FC<HeroEducationProps> = ({
  currentUser,
  onOpenAuth,
  onNavigateTab,
}) => {
  const [selectedQuizAnswer, setSelectedQuizAnswer] = useState<number | null>(null);

  const quizOptions = [
    { text: 'Sering skip sarapan karena buru-buru kelas pagi 07:00', risk: 'Tinggi (Rentan Gastritis Akut)' },
    { text: 'Langsung rebahan atau tidur di kasur kos setelah makan mie/nasi', risk: 'Sangat Tinggi (Pemicu Utama Reflux GERD)' },
    { text: 'Minum es kopi susu pekat saat perut masih kosong', risk: 'Tinggi (Merangsang Sekresi Asam HCl Ekstrem)' },
    { text: 'Makan tepat waktu 3x sehari dan jeda 2-3 jam sebelum tidur', risk: 'Rendah (Pola Lambung Sehat)' },
  ];

  return (
    <div className="space-y-12">
      {/* Hero Banner */}
      <section className="relative overflow-hidden rounded-3xl bg-linear-to-br from-emerald-800 via-teal-900 to-slate-900 text-white p-6 sm:p-10 lg:p-14 shadow-xl">
        {/* Decorative background glow */}
        <div className="absolute -right-20 -top-20 w-80 h-80 rounded-full bg-emerald-500/20 blur-3xl pointer-events-none" />
        <div className="absolute -left-20 -bottom-20 w-80 h-80 rounded-full bg-teal-500/20 blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 backdrop-blur-md border border-white/20 text-xs font-medium text-emerald-200 mb-6">
            <QrCode className="w-4 h-4 text-emerald-300" />
            <span>Inovasi Pendamping Kesehatan Mahasiswa</span>
          </div>

          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight leading-tight text-white mb-4">
            Lindungi Lambung Mahasiswa, Kuliah Bebas Maag & GERD.
          </h1>

          <p className="text-emerald-100/90 text-base sm:text-lg mb-8 leading-relaxed">
            Sobat Lambung hadir sebagai pendamping kesehatan untuk mahasiswa aktif. Akses panduan gizi dan edukasi medis, serta aktifkan pengingat jam makan otomatis via WhatsApp langsung ke ponselmu.
          </p>

          <div className="flex flex-wrap items-center gap-3">
            {currentUser ? (
              <button
                onClick={() => onNavigateTab('dashboard')}
                className="px-6 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-sm transition-all shadow-lg shadow-emerald-500/30 flex items-center gap-2 cursor-pointer"
              >
                <Bell className="w-4 h-4 text-slate-950" />
                Buka Dasbor Alarm Pengingat
                <ArrowRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={() => onOpenAuth('register')}
                className="px-6 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-sm transition-all shadow-lg shadow-emerald-500/30 flex items-center gap-2 cursor-pointer"
              >
                <Bell className="w-4 h-4 text-slate-950" />
                Daftar & Aktifkan Alarm WhatsApp
                <ArrowRight className="w-4 h-4" />
              </button>
            )}

            <button
              onClick={() => onNavigateTab('share')}
              className="px-5 py-3 rounded-xl bg-white/10 hover:bg-white/15 text-white font-medium text-sm border border-white/20 backdrop-blur-sm transition-colors flex items-center gap-2 cursor-pointer"
            >
              <QrCode className="w-4 h-4 text-emerald-300" />
              Bagikan Aplikasi
            </button>

            <button
              onClick={() => onNavigateTab('food')}
              className="px-5 py-3 rounded-xl bg-transparent hover:bg-white/5 text-emerald-200 font-medium text-sm transition-colors flex items-center gap-2 cursor-pointer"
            >
              Menu Aman Lambung
            </button>
          </div>
        </div>

        {/* Feature Highlights Grid in Hero */}
        <div className="mt-10 pt-8 border-t border-white/10 grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-300 shrink-0">
              <QrCode className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-semibold text-sm text-white">Promosi Digital Mudah</h4>
              <p className="text-xs text-emerald-100/70">Bagikan Sobat Lambung ke sesama mahasiswa dengan sekali scan.</p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-300 shrink-0">
              <Bell className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-semibold text-sm text-white">Alarm WhatsApp Standar Medis</h4>
              <p className="text-xs text-emerald-100/70">Jadwal 07:00, 12:00, 18:30 WIB dengan rekomendasi menu ramah lambung.</p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-300 shrink-0">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-semibold text-sm text-white">Privat & Kendali Penuh</h4>
              <p className="text-xs text-emerald-100/70">Cukup satu sakelar toggle on/off di dasbor pengguna untuk mengontrol pesan.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Mini Interactive Self-Check for College Students */}
      <section className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-xs">
        <div className="flex items-center gap-2.5 text-amber-600 font-semibold text-sm mb-2">
          <AlertTriangle className="w-4 h-4" />
          <span>Skrining Singkat Kebiasaan Makan Mahasiswa</span>
        </div>
        <h2 className="text-xl sm:text-2xl font-bold text-slate-800 mb-2">
          Manakah Kebiasaan yang Paling Sering Terjadi di Kehidupan Kampusmu?
        </h2>
        <p className="text-sm text-slate-600 mb-6">
          Klik salah satu opsi untuk melihat tingkat risiko gangguan asam lambung yang mungkin sedang mengintai:
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
          {quizOptions.map((opt, idx) => (
            <button
              key={idx}
              onClick={() => setSelectedQuizAnswer(idx)}
              className={`p-4 rounded-xl border text-left transition-all flex items-start gap-3 cursor-pointer ${
                selectedQuizAnswer === idx
                  ? 'border-emerald-500 bg-emerald-50/70 ring-2 ring-emerald-500/20'
                  : 'border-slate-200 hover:border-slate-300 bg-slate-50/50'
              }`}
            >
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 text-xs font-bold ${
                  selectedQuizAnswer === idx
                    ? 'bg-emerald-600 text-white'
                    : 'bg-slate-200 text-slate-700'
                }`}
              >
                {String.fromCharCode(65 + idx)}
              </div>
              <div>
                <p className="text-xs sm:text-sm font-medium text-slate-800 leading-snug">{opt.text}</p>
                {selectedQuizAnswer === idx && (
                  <p className="mt-2 text-xs font-semibold text-emerald-800 bg-emerald-100/80 px-2 py-1 rounded inline-block">
                    Kategori Risiko: {opt.risk}
                  </p>
                )}
              </div>
            </button>
          ))}
        </div>

        {selectedQuizAnswer !== null && (
          <div className="mt-4 p-4 rounded-xl bg-slate-100 border border-slate-200 text-xs text-slate-700 flex items-start gap-3">
            <HeartPulse className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold text-slate-900">Solusi Sobat Lambung: </span>
              Kunci utama penyembuhan maag & GERD bagi mahasiswa adalah <strong>Keteraturan Jadwal Makan</strong>. Dengan mengaktifkan pengingat otomatis di jam 07:00, 12:00, dan 18:30 WIB, kamu tidak akan lagi lupa makan di sela kesibukan tugas kampus.
            </div>
          </div>
        )}
      </section>
    </div>
  );
};
