import React, { useState } from 'react';
import { generateWhatsAppReminderMessage, STATIC_SCHEDULES } from '../logic/sobatLambung';
import { Send, CheckCheck, Smartphone, ShieldCheck, RefreshCw, AlertCircle, Sparkles } from 'lucide-react';

interface WhatsAppPhoneMockupProps {
  userName: string;
  isAlarmActive: boolean;
  userPhone: string;
}

export const WhatsAppPhoneMockup: React.FC<WhatsAppPhoneMockupProps> = ({
  userName,
  isAlarmActive,
  userPhone,
}) => {
  const [selectedMeal, setSelectedMeal] = useState<'breakfast' | 'lunch' | 'dinner'>('breakfast');
  const [simulatedMessages, setSimulatedMessages] = useState<
    { id: string; time: string; text: string; meal: string }[]
  >([
    {
      id: 'init-1',
      time: '07:30',
      text: generateWhatsAppReminderMessage(userName || 'Mahasiswa', 'breakfast'),
      meal: 'breakfast',
    },
  ]);
  const [notice, setNotice] = useState<string | null>(null);

  return (
    <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-xs space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
        <div>
          <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-emerald-700 bg-emerald-100 px-2.5 py-0.5 rounded-full mb-1">
            <Smartphone className="w-3.5 h-3.5" />
            Simulasi Live WhatsApp Gateway (Fonnte)
          </div>
          <h3 className="text-xl font-bold text-slate-900">
            Pratinjau Pesan yang Diterima di Ponsel Mahasiswa
          </h3>
          <p className="text-xs text-slate-500">
            Format pesan resmi dari sistem backend Cron Job (APScheduler) ke nomor WhatsApp target.
          </p>
        </div>

        {/* Action Trigger */}
        <div className="flex items-center gap-2">
          <div className="px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 shadow-xs bg-slate-100 text-slate-500 border border-slate-200">
            <Sparkles className="w-3.5 h-3.5" />
            Simulasi Pengingat Aktif
          </div>
        </div>
      </div>

      {notice && (
        <div
          className={`p-3 rounded-xl text-xs font-medium flex items-center gap-2 ${
            notice.startsWith('✅')
              ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
              : 'bg-amber-50 text-amber-800 border border-amber-200'
          }`}
        >
          {notice.startsWith('✅') ? (
            <CheckCheck className="w-4 h-4 text-emerald-600 shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
          )}
          <span>{notice}</span>
        </div>
      )}

      {/* Select Meal template tabs */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-bold text-slate-500">Pilih Jadwal Medis:</span>
        {STATIC_SCHEDULES.map((sched) => (
          <button
            key={sched.id}
            onClick={() => setSelectedMeal(sched.id)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              selectedMeal === sched.id
                ? 'bg-emerald-800 text-white shadow-xs'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            {sched.time} - {sched.label.split(' ')[0]}
          </button>
        ))}
      </div>

      {/* Phone Screen Mockup */}
      <div className="w-full max-w-md mx-auto bg-slate-900 rounded-[2rem] sm:rounded-[2.5rem] p-2 sm:p-3 shadow-2xl border-4 border-slate-800">
        {/* Phone Notch / Speaker */}
        <div className="w-28 sm:w-36 h-4 bg-slate-800 mx-auto rounded-b-xl mb-2 flex items-center justify-center">
          <div className="w-8 h-1 bg-slate-700 rounded-full"></div>
        </div>

        {/* WhatsApp App Container */}
        <div className="bg-[#efeae2] rounded-3xl sm:rounded-4xl overflow-hidden min-h-95 sm:min-h-115 sm:max-h-130 flex flex-col">
          {/* WhatsApp Header */}
          <div className="bg-[#008069] text-white px-3 sm:px-4 py-3 flex items-center justify-between gap-2 shadow-sm">
            <div className="flex min-w-0 items-center gap-2.5">
              <div className="w-9 h-9 shrink-0 rounded-full bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold text-sm shadow-xs">
                🥣
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-1.5">
                  <p className="font-bold text-sm leading-tight text-white truncate">Sobat Lambung</p>
                  <span className="shrink-0 text-[9px] bg-emerald-700 px-1.5 py-0.2 rounded-full font-semibold">Resmi</span>
                </div>
                <p className="text-[10px] text-emerald-100 truncate">Akun Pengingat Kesehatan Mahasiswa</p>
              </div>
            </div>
            <div className="hidden sm:block shrink-0 text-[10px] font-mono text-emerald-200 bg-[#006e5a] px-2 py-0.5 rounded">
              Fonnte API
            </div>
          </div>

          {/* Chat Messages Body */}
          <div className="flex-1 p-3 overflow-y-auto space-y-3 font-sans text-xs">
            {/* Encryption notice */}
            <div className="bg-[#ffeecd] text-[#54656f] text-[10px] text-center p-1.5 rounded-lg max-w-[85%] mx-auto shadow-2xs">
              🔒 Pesan dikirim otomatis terjadwal oleh server Sobat Lambung via WhatsApp Gateway.
            </div>

            {simulatedMessages.map((msg) => (
              <div
                key={msg.id}
                className="bg-white rounded-lg p-3 max-w-[92%] shadow-xs ml-auto border border-slate-200/50 space-y-2"
              >
                <div className="whitespace-pre-line text-slate-800 leading-relaxed font-sans">
                  {msg.text}
                </div>
                <div className="flex items-center justify-end gap-1 text-[10px] text-slate-400">
                  <span>{msg.time}</span>
                  <CheckCheck className="w-3.5 h-3.5 text-blue-500" />
                </div>
              </div>
            ))}
          </div>

          {/* Fake Input Bar */}
          <div className="bg-[#f0f2f5] p-2 flex items-center gap-2 border-t border-slate-200">
            <div className="flex-1 bg-white rounded-full px-3 py-1.5 text-[11px] text-slate-400">
              Ketik balasan (layanan broadcast satu arah)...
            </div>
            <div className="w-8 h-8 rounded-full bg-[#008069] text-white flex items-center justify-center">
              <Send className="w-3.5 h-3.5" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
