import React from 'react';
import { QrCode, CheckCircle2, Download, Link2 } from 'lucide-react';
import Qr from "../assets/qr-code.png"

interface KeychainPreviewProps {
  onScanSuccess: () => void;
}

export const KeychainPreview: React.FC<KeychainPreviewProps> = ({ onScanSuccess }) => {
  const handleDownloadQr = () => {
    const link = document.createElement("a");
    link.href = Qr;
    link.download = "sobat-lambung-qr.png";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleCopyLink = async () => {
    const url = window.location.origin;

    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(url);
      } else {
        const textArea = document.createElement("textarea");
        textArea.value = url;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand("copy");
        document.body.removeChild(textArea);
      }
      alert("Link berhasil disalin ke clipboard!");
    } catch (error) {
      console.error("Gagal menyalin:", error);
      alert("Gagal menyalin. Silakan salin manual: " + url);
    }
  };

  return (
    <section className="space-y-6">
      <div className="border-b border-slate-200 pb-5">
        <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-emerald-700 bg-emerald-100 px-2.5 py-1 rounded-full mb-1">
          <QrCode className="w-3.5 h-3.5" />
          Promosi & Berbagi
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900">
          Bagikan Sobat Lambung
        </h2>
        <p className="text-sm text-slate-600 mt-1">
          Ajak teman mahasiswa lainnya untuk hidup sehat dan atur jadwal makan dengan Sobat Lambung.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        {/* Visual of the Share QR */}
        <div className="lg:col-span-5 flex flex-col items-center">
          <div className="w-full max-w-72 bg-white rounded-3xl p-6 sm:p-8 shadow-xl border border-slate-200 flex flex-col items-center text-center">
            <h3 className="font-bold text-slate-900 mb-4">Scan untuk Berbagi</h3>

            {/* QR Code Graphic */}
            <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-100 mb-4">
              <div className="w-40 h-40 bg-white rounded-lg p-2 shadow-inner flex items-center justify-center overflow-hidden">
                <img
                  src={Qr}
                  alt="QR Code Sobat Lambung"
                  className="w-full h-full object-contain"
                />
              </div>
            </div>

            <p className="text-[10px] font-bold text-emerald-800 uppercase tracking-wider mb-2">
              SobatLambung.id
            </p>

            <button
              onClick={handleDownloadQr}
              className="mt-2 w-full flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-bold py-3 px-4 rounded-xl transition-colors cursor-pointer"
              aria-label="Download barcode QR code"
            >
              <Download className="w-4 h-4" />
              Download Barcode
            </button>

            <button
              onClick={handleCopyLink}
              className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-emerald-700 hover:underline cursor-pointer"
            >
              <Link2 className="w-3.5 h-3.5" />
              Salin Link Web
            </button>

            <p className="mt-3 text-[10px] leading-relaxed text-slate-500">
              Klik download untuk menyimpan gambar QR code ke perangkatmu.
            </p>
          </div>
        </div>

        {/* Benefits & Specifications */}
        <div className="lg:col-span-7 space-y-4">
          <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-4">
            <h3 className="text-lg font-bold text-slate-900">
              Ajak Temanmu Sehat Bersama
            </h3>
            <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
              Kesehatan lambung adalah kunci produktivitas mahasiswa. Jangan biarkan temanmu terkena maag atau GERD akibat pola makan yang tidak teratur.
            </p>

            <div className="space-y-3">
              <div className="flex items-start gap-3 p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs sm:text-sm">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold text-slate-900">Eduksi Mudah Diakses: </span>
                  Bagikan informasi mengenai pencegahan GERD dan gastritis dengan cepat.
                </div>
              </div>

              <div className="flex items-start gap-3 p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs sm:text-sm">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold text-slate-900">Pengingat Makan Komunal: </span>
                  Mulai kebiasaan makan teratur bareng teman-teman kos atau kelompok studi kamu.
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
