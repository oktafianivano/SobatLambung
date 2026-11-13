import React, { useState } from 'react';
import { EDUCATION_ARTICLES } from '../data/educationData';
import { HeartPulse, Flame, AlertCircle, CheckCircle2, XCircle, ArrowUpRight, BookOpen } from 'lucide-react';

export const GerdGastritisGuide: React.FC = () => {
  const [selectedTopic, setSelectedTopic] = useState<'gastritis' | 'gerd'>('gastritis');
  const activeArticle = EDUCATION_ARTICLES.find((a) => a.id === selectedTopic) || EDUCATION_ARTICLES[0];

  return (
    <section className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-emerald-700 bg-emerald-100 px-2.5 py-1 rounded-full mb-1">
            <BookOpen className="w-3.5 h-3.5" />
            Modul Web Publik (Edukasi Medis)
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900">
            Pahami Perbedaan Gastritis (Maag) & GERD
          </h2>
          <p className="text-sm text-slate-600 mt-1">
            Dua keluhan lambung paling lazim di kalangan mahasiswa yang sering tertukar penanganannya.
          </p>
        </div>

        {/* Toggle between Gastritis and GERD */}
        <div className="flex w-full sm:w-auto bg-slate-100 p-1.5 rounded-xl border border-slate-200 shrink-0">
          <button
            onClick={() => setSelectedTopic('gastritis')}
            className={`flex-1 sm:flex-none justify-center px-2 sm:px-4 py-2 rounded-lg text-[11px] sm:text-sm font-bold transition-all flex items-center gap-1.5 sm:gap-2 cursor-pointer ${
              selectedTopic === 'gastritis'
                ? 'bg-white text-emerald-800 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <HeartPulse className="w-4 h-4 shrink-0 text-emerald-600" />
            Gastritis (Maag)
          </button>
          <button
            onClick={() => setSelectedTopic('gerd')}
            className={`flex-1 sm:flex-none justify-center px-2 sm:px-4 py-2 rounded-lg text-[11px] sm:text-sm font-bold transition-all flex items-center gap-1.5 sm:gap-2 cursor-pointer ${
              selectedTopic === 'gerd'
                ? 'bg-white text-rose-700 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Flame className="w-4 h-4 shrink-0 text-rose-500" />
            GERD (Reflux)
          </button>
        </div>
      </div>

      {/* Main Educational Card */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="p-6 sm:p-8 bg-linear-to-r from-slate-50 to-emerald-50/40 border-b border-slate-200">
          <div className="flex items-center gap-2 text-xs font-semibold text-emerald-700 mb-1">
            <span>{activeArticle.subtitle}</span>
          </div>
          <h3 className="text-2xl font-bold text-slate-900 mb-3">{activeArticle.title}</h3>
          <p className="text-sm sm:text-base text-slate-700 leading-relaxed max-w-4xl">
            {activeArticle.definition}
          </p>
        </div>

        <div className="p-6 sm:p-8 grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Column 1: Typical College Triggers */}
          <div className="space-y-4">
            <h4 className="text-sm font-bold uppercase tracking-wider text-amber-700 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-amber-600" />
              Penyebab Utama pada Mahasiswa
            </h4>
            <ul className="space-y-3">
              {activeArticle.studentCauses.map((cause, idx) => (
                <li key={idx} className="flex items-start gap-3 p-3 rounded-xl bg-amber-50/60 border border-amber-200/60 text-xs sm:text-sm text-slate-800">
                  <div className="w-5 h-5 rounded-full bg-amber-200 text-amber-900 flex items-center justify-center shrink-0 text-xs font-bold mt-0.5">
                    {idx + 1}
                  </div>
                  <span>{cause}</span>
                </li>
              ))}
            </ul>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-600">
              <span className="font-semibold text-slate-800">Gejala Khas yang Dirasakan:</span>
              <ul className="mt-2 space-y-1 list-disc list-inside">
                {activeArticle.symptoms.map((symptom, idx) => (
                  <li key={idx}>{symptom}</li>
                ))}
              </ul>
            </div>
          </div>

          {/* Column 2: Medical Tips & Best Practices */}
          <div className="space-y-4">
            <h4 className="text-sm font-bold uppercase tracking-wider text-emerald-700 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              Anjuran Medis & Tips Pemulihan
            </h4>
            <div className="space-y-3">
              {activeArticle.medicalTips.map((tip, idx) => (
                <div key={idx} className="flex items-start gap-3 p-3.5 rounded-xl bg-emerald-50/70 border border-emerald-200/70 text-xs sm:text-sm text-slate-800">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <span>{tip}</span>
                </div>
              ))}
            </div>

            {/* Quick Dos and Donts Comparison */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
              <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200">
                <p className="font-bold text-xs text-emerald-800 flex items-center gap-1.5 mb-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> LAKUKAN (DO)
                </p>
                <p className="text-[11px] text-emerald-950 leading-relaxed">
                  Kunyah perlahan 25-30 kali, makan tepat waktu, dan minum air hangat setelah makan.
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200">
                <p className="font-bold text-xs text-rose-800 flex items-center gap-1.5 mb-2">
                  <XCircle className="w-3.5 h-3.5 text-rose-600" /> HINDARI (DON'T)
                </p>
                <p className="text-[11px] text-rose-950 leading-relaxed">
                  Langsung tidur setelah makan, kopi sachet saat perut kosong, dan seblak ekstra pedas.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
