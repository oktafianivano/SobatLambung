import { useEffect, useState } from 'react';

import {
  STATIC_SCHEDULES,
  applyScheduleOverride,
  type ScheduleApiItem,
  type ScheduleItem,
} from '../logic/sobatLambung';
import { apiUrl } from '../services/api';

/**
 * Mengambil jadwal pengingat terbaru dari backend.
 *
 * Nilai awal langsung memakai jadwal lokal supaya UI tidak kosong atau
 * berkedip saat request pertama masih berjalan. Kalau request gagal (offline,
 * backend restart, CORS), jadwal lokal tetap dipakai sehingga tampilan tidak
 * pernah rusak.
 *
 * Sumber jam tetap satu: `backend/app/reminder_config.py`.
 */
export function useSchedules(): ScheduleItem[] {
  const [schedules, setSchedules] = useState<ScheduleItem[]>(STATIC_SCHEDULES);

  useEffect(() => {
    const controller = new AbortController();

    const load = async () => {
      try {
        const response = await fetch(apiUrl('/schedules'), {
          signal: controller.signal,
          headers: { Accept: 'application/json' },
        });
        if (!response.ok) return;

        const payload: unknown = await response.json();
        if (!Array.isArray(payload)) return;

        setSchedules(
          applyScheduleOverride(STATIC_SCHEDULES, payload as ScheduleApiItem[]),
        );
      } catch {
        // Biarkan fallback STATIC_SCHEDULES; jangan ganggu UI.
      }
    };

    void load();

    return () => controller.abort();
  }, []);

  return schedules;
}
