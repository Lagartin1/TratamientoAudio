import { Audio } from '../../../models/audio.model';

export function buildPopupTemplate(audio: Audio): string {
  const badgeColor = 'bg-red-100 text-red-800 border-red-200';

  return `
    <div class="p-4 bg-white text-slate-800 rounded-2xl shadow-xl border border-slate-200/80 font-sans min-w-[190px]">
      <div class="flex justify-between items-center mb-3 border-b border-slate-100 pb-2">
        <span class="text-[10px] uppercase font-bold tracking-wider text-slate-400">Muestra Registrada</span>
        <span class="text-xs bg-slate-100 px-2 py-0.5 rounded-md font-mono text-slate-600 font-semibold">#${audio.id}</span>
      </div>
      <div class="mb-3">
        <span class="text-xs text-slate-400 block mb-0.5">Intensidad Acústica</span>
        <div class="flex items-baseline space-x-1">
          <span class="text-2xl font-black tracking-tight text-slate-900">${audio.decibels}</span>
          <span class="text-xs font-bold text-slate-400">dB</span>
        </div>
      </div>
      <div class="space-y-2 pt-1">
        <div class="flex items-center justify-between text-xs">
          <span class="text-slate-500 font-medium">Origen:</span>
          <span class="px-2 py-0.5 rounded-full text-[11px] font-semibold border ${badgeColor}">
            ${audio.categoria}
          </span>
        </div>
        ${audio.tipo_ave ? `
          <div class="flex items-center justify-between text-xs bg-emerald-50 border border-emerald-200 p-2 rounded-xl mt-1">
            <span class="text-emerald-700 font-semibold">🐦 Especie:</span>
            <span class="text-emerald-800 font-extrabold italic">${audio.tipo_ave}</span>
          </div>
        ` : ''}
      </div>
    </div>
  `;
}