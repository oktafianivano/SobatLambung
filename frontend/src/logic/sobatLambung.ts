/**
 * Pure business logic for Sobat Lambung application.
 * Decoupled from UI components for unit testing and reliability.
 */

export interface ScheduleItem {
  id: 'breakfast' | 'lunch' | 'dinner';
  time: string;
  hour: number;
  minute: number;
  label: string;
  shortDesc: string;
  medicalRationale: string;
  recommendedMenus: string[];
}

export const STATIC_SCHEDULES: ScheduleItem[] = [
  {
    id: 'breakfast',
    time: '07:30 WIB',
    hour: 7,
    minute: 30,
    label: 'Sarapan Pagi Ramah Lambung',
    shortDesc: 'Menetralkan lonjakan asam lambung setelah puasa malam.',
    medicalRationale: 'Asam klorida (HCl) di lambung mencapai keasaman tinggi di pagi hari. Sarapan berserat larut dan rendah asam mencegah erosi dinding mukosa lambung.',
    recommendedMenus: [
      'Bubur ayam tanpa sambal & kuah kuning gurih ringan',
      'Oatmeal hangat dengan irisan pisang ambon & madu murni',
      'Roti gandum bakar + telur rebus setengah matang / telur orak-arik rendah minyak',
    ],
  },
  {
    id: 'lunch',
    time: '12:00 WIB',
    hour: 12,
    minute: 0,
    label: 'Makan Siang & Jeda Kuliah',
    shortDesc: 'Menjaga pasokan glukosa otak dan mencegah sindrom dyspepsia.',
    medicalRationale: 'Jam 12 siang adalah fase sekresi enzim pencernaan kedua. Jangan tunda makan siang dengan alasan praktikum/nugas agar terhindar dari perih ulu hati dan kembung.',
    recommendedMenus: [
      'Nasi putih pulen + sup wortel labu siam + ayam kukus bumbu jahe',
      'Ikan nila kukus / salmon panggang bumbu kunyit + tahu sutra kukus',
      'Kentang tumbuk (mashed potato) + telur rebus + tumis buncis muda non-pedas',
    ],
  },
  {
    id: 'dinner',
    time: '18:30 WIB',
    hour: 18,
    minute: 30,
    label: 'Makan Malam Tepat Waktu',
    shortDesc: 'Beri jeda minimal 2-3 jam sebelum tidur untuk mencegah reflux GERD.',
    medicalRationale: 'Makan malam lebih awal (maksimal 19:00) mencegah asam lambung naik ke esofagus saat berbaring tidur, melindungi sfingter LES dan pita suara.',
    recommendedMenus: [
      'Nasi tim ayam jamur rendah lemak + sayur bening bayam jagung',
      'Sup makaroni ayam fillet sayuran hangat + tempe panggang',
      'Bubur kacang hijau kuah santan encer rendah gula (atau air jahe hangat)',
    ],
  },
];

/**
 * Normalizes Indonesian WhatsApp numbers to 628... format.
 */
export function normalizeWhatsAppNumber(rawPhone: string): { isValid: boolean; formatted: string; error?: string } {
  if (!rawPhone) {
    return { isValid: false, formatted: '', error: 'Nomor WhatsApp wajib diisi' };
  }

  // Remove spaces, dashes, parentheses
  let cleaned = rawPhone.replace(/[\s\-\(\)\.]/g, '');

  // Handle leading +
  if (cleaned.startsWith('+')) {
    cleaned = cleaned.substring(1);
  }

  // Handle leading 0 (e.g. 0812...)
  if (cleaned.startsWith('0')) {
    cleaned = '62' + cleaned.substring(1);
  }

  // Handle starting with 8 (e.g. 812...)
  if (cleaned.startsWith('8')) {
    cleaned = '62' + cleaned;
  }

  // Check valid length: Indonesian numbers are usually 10 to 14 digits after 62
  const regex = /^628[1-9][0-9]{7,11}$/;
  if (!regex.test(cleaned)) {
    return {
      isValid: false,
      formatted: cleaned,
      error: 'Format nomor WhatsApp tidak valid. Contoh: 08123456789 atau 628123456789',
    };
  }

  return { isValid: true, formatted: cleaned };
}

/**
 * Validates student password according to security criteria.
 */
export function validatePassword(password: string): { isValid: boolean; error?: string } {
  if (!password) {
    return { isValid: false, error: 'Kata sandi wajib diisi' };
  }
  if (password.length < 6) {
    return { isValid: false, error: 'Kata sandi minimal 6 karakter' };
  }
  return { isValid: true };
}

/**
 * Formats a WhatsApp message exactly as dispatched by Fonnte to students.
 */
export function generateWhatsAppReminderMessage(userName: string, scheduleId: 'breakfast' | 'lunch' | 'dinner'): string {
  const schedule = STATIC_SCHEDULES.find((s) => s.id === scheduleId) || STATIC_SCHEDULES[0];
  const menuList = schedule.recommendedMenus.map((m) => `  • ${m}`).join('\n');

  return `Halo *${userName}*! 👋
Pengingat dari *Sobat Lambung* 🥣

*${schedule.label} (${schedule.time})*

🍽️ *Rekomendasi Menu Mahasiswa Ramah Lambung:*
${menuList}

💡 *Pesan Medis Sobat Lambung:*
${schedule.medicalRationale}

_Tetap konsisten jaga jam makan di tengah padatnya kuliah & praktikum ya!_ ✨`;
}

/**
 * Calculates current meal status or next upcoming static alarm.
 */
export function getNextStaticAlarm(currentHour: number, currentMinute: number): ScheduleItem {
  const nowMinutes = currentHour * 60 + currentMinute;
  for (const item of STATIC_SCHEDULES) {
    const itemMinutes = item.hour * 60 + item.minute;
    if (itemMinutes > nowMinutes) {
      return item;
    }
  }
  // Default wrap around to tomorrow breakfast
  return STATIC_SCHEDULES[0];
}
