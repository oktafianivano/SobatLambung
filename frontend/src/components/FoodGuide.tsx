import React, { useState } from 'react';
import { FOOD_CATEGORIES } from '../data/educationData';
import { Utensils, Check, AlertOctagon, Sparkles, Coffee, ShieldCheck } from 'lucide-react';

export const FoodGuide: React.FC = () => {
  const [filterType, setFilterType] = useState<'all' | 'recommended' | 'avoid'>('all');

  const filteredCategories = FOOD_CATEGORIES.filter((cat) => {
    if (filterType === 'all') return true;
    return cat.type === filterType;
  });

  return (
    <section className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-emerald-700 bg-emerald-100 px-2.5 py-1 rounded-full mb-1">
            <Utensils className="w-3.5 h-3.5" />
            Nutrisi Ramah Lambung Mahasiswa
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900">
            Panduan Makanan Anjuran vs Pantangan
          </h2>
          <p className="text-sm text-slate-600 mt-1">
            Menu praktis, terjangkau di sekitar kampus, dan aman untuk penderita maag serta GERD.
          </p>
        </div>

        {/* Filter Buttons */}
        <div className="flex flex-wrap bg-slate-100 p-1 rounded-xl border border-slate-200 self-start sm:self-auto">
          <button
            onClick={() => setFilterType('all')}
            className={`px-2.5 sm:px-3 py-1.5 rounded-lg text-[11px] sm:text-xs font-bold transition-all cursor-pointer ${
              filterType === 'all' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600'
            }`}
          >
            Semua
          </button>
          <button
            onClick={() => setFilterType('recommended')}
            className={`px-2.5 sm:px-3 py-1.5 rounded-lg text-[11px] sm:text-xs font-bold transition-all cursor-pointer ${
              filterType === 'recommended' ? 'bg-emerald-600 text-white shadow-xs' : 'text-slate-600'
            }`}
          >
            Dianjurkan (Aman)
          </button>
          <button
            onClick={() => setFilterType('avoid')}
            className={`px-2.5 sm:px-3 py-1.5 rounded-lg text-[11px] sm:text-xs font-bold transition-all cursor-pointer ${
              filterType === 'avoid' ? 'bg-rose-600 text-white shadow-xs' : 'text-slate-600'
            }`}
          >
            Pantangan (Hindari)
          </button>
        </div>
      </div>

      {/* Grid of Categories */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filteredCategories.map((cat) => (
          <div
            key={cat.id}
            className={`rounded-2xl border p-6 transition-all ${
              cat.type === 'recommended'
                ? 'bg-linear-to-b from-white to-emerald-50/30 border-emerald-200 shadow-xs'
                : 'bg-linear-to-b from-white to-rose-50/30 border-rose-200 shadow-xs'
            }`}
          >
            <div className="flex items-start justify-between gap-3 mb-3">
              <div>
                <span
                  className={`text-[11px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md ${
                    cat.type === 'recommended'
                      ? 'bg-emerald-100 text-emerald-800'
                      : 'bg-rose-100 text-rose-800'
                  }`}
                >
                  {cat.type === 'recommended' ? 'Pilihan Aman & Sehat' : 'Harap Dibatasi / Hindari'}
                </span>
                <h3 className="text-lg font-bold text-slate-900 mt-1.5">{cat.title}</h3>
              </div>
              <div
                className={`p-2 rounded-xl shrink-0 ${
                  cat.type === 'recommended' ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'
                }`}
              >
                {cat.type === 'recommended' ? <Check className="w-5 h-5" /> : <AlertOctagon className="w-5 h-5" />}
              </div>
            </div>

            <p className="text-xs text-slate-600 mb-4">{cat.description}</p>

            <div className="space-y-2.5">
              {cat.items.map((item, idx) => (
                <div
                  key={idx}
                  className={`p-3 rounded-xl border text-xs sm:text-sm flex flex-col gap-1 ${
                    cat.type === 'recommended'
                      ? 'bg-white/80 border-emerald-100 text-slate-800'
                      : 'bg-white/80 border-rose-100 text-slate-800'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span
                      className={`w-2 h-2 rounded-full ${
                        cat.type === 'recommended' ? 'bg-emerald-500' : 'bg-rose-500'
                      }`}
                    />
                    <span className="font-bold text-slate-900">{item.name}</span>
                  </div>
                  <p className="text-slate-500 text-xs pl-4 leading-relaxed">{item.reason}</p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* College Student Kost Tips Box */}
      <div className="p-5 rounded-2xl bg-teal-900 text-white flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-xl bg-teal-800 text-teal-200 shrink-0">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h4 className="font-bold text-sm text-white">Tips Anak Kos: Menu Sarapan Cepat 5 Menit</h4>
            <p className="text-xs text-teal-100/80">
              Seduh oatmeal instan dengan air hangat, tambahkan 1 buah pisang ambon & 1 sendok madu. Praktis, murah, dan melindungi dinding lambung sebelum kuliah pagi!
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};
