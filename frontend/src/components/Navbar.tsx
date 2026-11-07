import React from 'react';
import { UserProfile } from '../types';
import { Bell, HeartPulse, QrCode, Utensils, Terminal, LogIn, LogOut, User as UserIcon } from 'lucide-react';

interface NavbarProps {
  currentUser: UserProfile | null;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onOpenAuth: (mode: 'login' | 'register') => void;
  onLogout: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentUser,
  activeTab,
  setActiveTab,
  onOpenAuth,
  onLogout,
}) => {
  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-emerald-100 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo */}
          <div
            onClick={() => setActiveTab('landing')}
            className="flex items-center gap-2.5 cursor-pointer group"
          >
            <div className="w-10 h-10 rounded-xl bg-linear-to-tr from-emerald-600 to-teal-500 flex items-center justify-center text-white shadow-md shadow-emerald-500/20 group-hover:scale-105 transition-transform">
              <HeartPulse className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-lg text-slate-800 tracking-tight">Sobat Lambung</span>
                <span className="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800">
                  Praktis
                </span>
              </div>
              <p className="text-[11px] text-slate-500 -mt-0.5">Edukasi & Pengingat Jam Makan Mahasiswa</p>
            </div>
          </div>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-1 text-sm font-medium">
            <button
              onClick={() => setActiveTab('landing')}
              className={`px-3 py-2 rounded-lg transition-colors flex items-center gap-1.5 ${
                activeTab === 'landing'
                  ? 'text-emerald-700 bg-emerald-50'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <HeartPulse className="w-4 h-4 text-emerald-600" />
              Edukasi Medis
            </button>

            <button
              onClick={() => setActiveTab('food')}
              className={`px-3 py-2 rounded-lg transition-colors flex items-center gap-1.5 ${
                activeTab === 'food'
                  ? 'text-emerald-700 bg-emerald-50'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <Utensils className="w-4 h-4 text-emerald-600" />
              Menu Aman Lambung
            </button>

             <button
              onClick={() => setActiveTab('share')}
              className={`px-3 py-2 rounded-lg transition-colors flex items-center gap-1.5 ${
                activeTab === 'share'
                  ? 'text-emerald-700 bg-emerald-50'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <QrCode className="w-4 h-4 text-emerald-600" />
              Bagikan Aplikasi
            </button>

            <button
              onClick={() => setActiveTab('dashboard')}
              className={`px-3 py-2 rounded-lg transition-colors flex items-center gap-1.5 ${
                activeTab === 'dashboard'
                  ? 'text-emerald-700 bg-emerald-50'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <Bell className="w-4 h-4 text-emerald-600" />
              Dasbor Alarm WA
              {currentUser?.is_alarm_active && (
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              )}
            </button>

            </nav>

          {/* Right Action: Auth Buttons */}
          <div className="flex items-center gap-2">
            {currentUser ? (
              <div className="flex items-center gap-1 bg-emerald-50/80 border border-emerald-200/70 rounded-xl p-1.5">
                <button
                  type="button"
                  onClick={() => setActiveTab('settings')}
                  title="Buka pengaturan akun"
                  className={`flex items-center gap-2 rounded-lg px-1 py-0.5 transition-colors cursor-pointer hover:bg-emerald-100/70 ${
                    activeTab === 'settings' ? 'bg-emerald-100' : ''
                  }`}
                >
                  <div className="w-8 h-8 rounded-lg bg-emerald-600 text-white flex items-center justify-center font-bold text-xs">
                    {currentUser.nama.charAt(0).toUpperCase()}
                  </div>
                  <div className="hidden sm:block text-left">
                    <p className="text-xs font-semibold text-slate-800 leading-tight truncate max-w-30">
                      {currentUser.nama}
                    </p>
                    <p className="text-[10px] text-emerald-700">
                      WA: {currentUser.is_alarm_active ? '● Aktif' : '○ Mati'}
                    </p>
                  </div>
                </button>
                <button
                  onClick={onLogout}
                  title="Keluar dari akun"
                  className="ml-1 p-1 text-slate-400 hover:text-rose-600 transition-colors cursor-pointer"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => onOpenAuth('login')}
                  className="px-3.5 py-1.5 text-xs font-semibold text-slate-700 hover:text-emerald-700 hover:bg-emerald-50 rounded-lg transition-colors flex items-center gap-1"
                >
                  <LogIn className="w-3.5 h-3.5" />
                  Masuk
                </button>
                <button
                  onClick={() => onOpenAuth('register')}
                  className="px-3.5 py-1.5 text-xs font-semibold text-white bg-linear-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 rounded-lg shadow-xs shadow-emerald-600/30 transition-all flex items-center gap-1"
                >
                  <UserIcon className="w-3.5 h-3.5" />
                  Daftar Akun
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Mobile secondary tab strip */}
        <div className="flex md:hidden overflow-x-auto py-2 gap-1 border-t border-slate-100 text-xs no-scrollbar">
          <button
            onClick={() => setActiveTab('landing')}
            className={`whitespace-nowrap px-2.5 py-1.5 rounded-md ${
              activeTab === 'landing' ? 'bg-emerald-100 text-emerald-800 font-semibold' : 'text-slate-600'
            }`}
          >
            Edukasi
          </button>
          <button
            onClick={() => setActiveTab('food')}
            className={`whitespace-nowrap px-2.5 py-1.5 rounded-md ${
              activeTab === 'food' ? 'bg-emerald-100 text-emerald-800 font-semibold' : 'text-slate-600'
            }`}
          >
            Menu Lambung
          </button>
          <button
            onClick={() => setActiveTab('share')}
            className={`whitespace-nowrap px-2.5 py-1.5 rounded-md ${
              activeTab === 'share' ? 'bg-emerald-100 text-emerald-800 font-semibold' : 'text-slate-600'
            }`}
          >
            Bagikan Aplikasi
          </button>
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`whitespace-nowrap px-2.5 py-1.5 rounded-md ${
              activeTab === 'dashboard' ? 'bg-emerald-100 text-emerald-800 font-semibold' : 'text-slate-600'
            }`}
          >
            Dasbor Alarm WA
          </button>
          {currentUser && (
            <button
              onClick={() => setActiveTab('settings')}
              className={`whitespace-nowrap px-2.5 py-1.5 rounded-md ${
                activeTab === 'settings' ? 'bg-emerald-100 text-emerald-800 font-semibold' : 'text-slate-600'
              }`}
            >
              Pengaturan Akun
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
