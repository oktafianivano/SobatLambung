import React, { useState } from 'react';
import { UserProfile } from './types';
import { Navbar } from './components/Navbar';
import { HeroEducation } from './components/HeroEducation';
import { GerdGastritisGuide } from './components/GerdGastritisGuide';
import { FoodGuide } from './components/FoodGuide';
import { KeychainPreview } from './components/KeychainPreview';
import { Dashboard } from './components/Dashboard';
import { AuthModal } from './components/AuthModal';
import { AccountSettings } from './components/AccountSettings';
import {
  HeartPulse,
  Bell,
  QrCode,
  Utensils,
  ShieldCheck,
  ArrowRight,
  Lock,
} from 'lucide-react';

export default function App() {
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [activeTab, setActiveTab] = useState<string>('landing');
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');

  const handleOpenAuth = (mode: 'login' | 'register') => {
    setAuthMode(mode);
    setAuthModalOpen(true);
  };

  const handleAuthSuccess = (user: UserProfile) => {
    setCurrentUser(user);
    setActiveTab('dashboard');
  };

  const handleLogout = () => {
    setCurrentUser(null);
    setActiveTab('landing');
  };

  return (
    <div className="min-h-dvh bg-slate-50 flex flex-col font-sans text-slate-800 antialiased overflow-x-clip selection:bg-emerald-500 selection:text-white">
      <Navbar
        currentUser={currentUser}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onOpenAuth={handleOpenAuth}
        onLogout={handleLogout}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-10 transition-opacity duration-300 ease-in-out">
        {activeTab === 'landing' && (
          <div className="space-y-16 animate-in fade-in duration-500">
            <HeroEducation
              currentUser={currentUser}
              onOpenAuth={handleOpenAuth}
              onNavigateTab={(tab) => setActiveTab(tab)}
            />
            <GerdGastritisGuide />
            <div className="bg-linear-to-r from-emerald-800 to-teal-900 rounded-3xl p-6 sm:p-8 text-white flex flex-col sm:flex-row sm:items-center justify-between gap-6 shadow-md">
              <div>
                <span className="text-xs uppercase font-bold tracking-wider px-2.5 py-1 rounded bg-white/20 text-emerald-200">Nutrisi Mahasiswa</span>
                <h3 className="text-xl sm:text-2xl font-bold mt-2">Bingung Pilih Makanan yang Tidak Memicu Maag & GERD?</h3>
              </div>
              <button onClick={() => setActiveTab('food')} className="w-full sm:w-auto justify-center px-5 py-3 rounded-xl bg-white text-emerald-950 font-bold text-xs sm:text-sm shadow-md hover:bg-emerald-50 transition-colors shrink-0 flex items-center gap-2 cursor-pointer">
                <Utensils className="w-4 h-4 text-emerald-700" /> Lihat Panduan Makanan <ArrowRight className="w-4 h-4" />
              </button>
            </div>
            <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 flex flex-col sm:flex-row sm:items-center justify-between gap-6 shadow-xs">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-2xl bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0"><QrCode className="w-6 h-6" /></div>
                <div>
                  <h3 className="text-lg font-bold text-slate-900">Ajak Teman Sehat Bersama</h3>
                  <p className="text-xs sm:text-sm text-slate-600 mt-1 max-w-2xl">Bagikan fitur Sobat Lambung ke teman-temanmu agar mereka juga bisa menjaga kesehatan lambung di masa kuliah.</p>
                </div>
              </div>
              <button onClick={() => setActiveTab('share')} className="w-full sm:w-auto justify-center px-5 py-2.5 rounded-xl border border-slate-300 hover:border-slate-400 text-slate-800 font-semibold text-xs sm:text-sm bg-slate-50 transition-colors shrink-0 cursor-pointer flex items-center gap-2">
                Bagikan ke Teman <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {activeTab === 'food' && <div className="animate-in fade-in duration-500"><FoodGuide /></div>}
        {activeTab === 'share' && <div className="animate-in fade-in duration-500"><KeychainPreview onScanSuccess={() => setActiveTab('landing')} /></div>}
        
        {activeTab === 'dashboard' && (
          <div className="animate-in fade-in duration-500">
            {currentUser ? (
              <Dashboard currentUser={currentUser} onUpdateUser={setCurrentUser} onOpenAuth={handleOpenAuth} />
            ) : (
              <div className="relative min-h-105 sm:min-h-150 rounded-3xl overflow-hidden border border-slate-200">
                {/* 1. Background Blurred Preview - Rendering real dashboard layout */}
                <div className="absolute inset-0 blur-sm opacity-30 select-none pointer-events-none grayscale-50">
                  <div className="p-4 sm:p-6 space-y-6">
                    <div className="h-24 bg-emerald-800 rounded-2xl w-full" />
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {[1, 2, 3].map((i) => (
                        <div key={i} className="h-64 bg-slate-300 rounded-2xl" />
                      ))}
                    </div>
                    <div className="h-96 bg-slate-200 rounded-2xl w-full" />
                  </div>
                </div>

                {/* 2. Floating Glassmorphism Card Overlay */}
                <div className="absolute inset-0 z-10 flex items-center justify-center p-3 sm:p-6">
                  <div className="bg-white/85 backdrop-blur-md p-5 sm:p-10 rounded-3xl border border-white/50 shadow-2xl text-center max-w-lg w-full">
                    <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-3xl bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto mb-4 sm:mb-6">
                      <Lock className="w-8 h-8 sm:w-10 sm:h-10" />
                    </div>
                    <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 mb-2 sm:mb-4">Dasbor Terkunci</h2>
                    <p className="text-sm sm:text-lg text-slate-600 mb-5 sm:mb-8">
                      Masuk atau daftar untuk membuka fitur pengingat makan WhatsApp otomatis dan pantau kesehatan lambungmu.
                    </p>
                    <div className="flex flex-col sm:flex-row gap-2.5 sm:gap-4 justify-center">
                      <button
                        onClick={() => handleOpenAuth('login')}
                        className="px-6 sm:px-10 py-3 sm:py-4 rounded-2xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-sm transition-all shadow-lg"
                      >
                        Masuk
                      </button>
                      <button
                        onClick={() => handleOpenAuth('register')}
                        className="px-6 sm:px-10 py-3 sm:py-4 rounded-2xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm transition-all shadow-lg"
                      >
                        Daftar Sekarang
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="animate-in fade-in duration-500">
            {currentUser ? (
              <AccountSettings currentUser={currentUser} onUpdateUser={setCurrentUser} onLogout={handleLogout} />
            ) : (
              <div className="max-w-md mx-auto bg-white rounded-3xl border border-slate-200 p-8 text-center shadow-sm">
                <div className="w-14 h-14 rounded-2xl bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto mb-4">
                  <ShieldCheck className="w-7 h-7" />
                </div>
                <h2 className="text-xl font-bold text-slate-900 mb-2">Pengaturan Terkunci</h2>
                <p className="text-sm text-slate-600 mb-6">Masuk ke akun Anda terlebih dahulu untuk mengubah profil dan kata sandi.</p>
                <button onClick={() => handleOpenAuth('login')} className="w-full py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-md shadow-emerald-600/30 transition-all">Masuk ke Akun</button>
              </div>
            )}
          </div>
        )}
      </main>

      <AuthModal isOpen={authModalOpen} initialMode={authMode} onClose={() => setAuthModalOpen(false)} onSuccess={handleAuthSuccess} />
      
      <footer className="mt-auto bg-slate-900 text-slate-400 border-t border-slate-800 py-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
            <div className="flex flex-wrap items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-emerald-600 text-white flex items-center justify-center"><HeartPulse className="w-4 h-4" /></div>
              <span className="font-bold text-white text-base">Sobat Lambung</span>
              <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded">Solusi Kesehatan Mahasiswa</span>
            </div>
            <div className="flex flex-wrap gap-4 text-xs">
              <button onClick={() => setActiveTab('landing')} className="hover:text-white transition-colors cursor-pointer">Edukasi</button>
              <button onClick={() => setActiveTab('food')} className="hover:text-white transition-colors cursor-pointer">Menu Makanan</button>
              <button onClick={() => setActiveTab('share')} className="hover:text-white transition-colors cursor-pointer">Bagikan ke Teman</button>
              <button onClick={() => setActiveTab('dashboard')} className="hover:text-white transition-colors cursor-pointer">Dasbor Mahasiswa</button>
            </div>
          </div>
          <div className="text-[11px] text-slate-500 leading-relaxed space-y-2">
            <p><strong>Disclaimer Medis:</strong> Sobat Lambung adalah inovasi produk edukasi kesehatan hibrida dan sistem pengingat pola makan teratur untuk mahasiswa. Informasi yang disajikan bukan pengganti diagnosis atau resep obat dari dokter spesialis pencernaan (Gastroenterolog).</p>
            <p>© 2026 Sobat Lambung. Solusi cerdas untuk hidup lebih sehat dan teratur bagi mahasiswa.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
