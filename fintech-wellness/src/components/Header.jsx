import { HeartPulse, Settings } from 'lucide-react';

export default function Header({ title, monitoringOn, onToggleMonitoring }) {
  return (
    <header className="flex items-center justify-between border-b border-gray-200 bg-white px-4 py-3 shadow-soft">
      <div className="flex items-center gap-2">
        <HeartPulse className="h-5 w-5 text-emerald-600" />
        <span className="text-sm font-semibold text-gray-900">
          {title}
        </span>
      </div>
      <div className="flex items-center gap-2">
        <Settings className="h-4 w-4 text-gray-400" />
        <span className="text-xs text-gray-500">
          Monitoring {monitoringOn ? 'on' : 'off'}
        </span>
        <button
          type="button"
          role="switch"
          aria-checked={monitoringOn}
          aria-label="Toggle monitoring"
          onClick={() => onToggleMonitoring(!monitoringOn)}
          className={`
            relative inline-flex h-5 w-10 items-center rounded-full transition-colors
            focus-visible:outline-none focus-visible:ring-2
            focus-visible:ring-emerald-600
            ${monitoringOn ? 'bg-emerald-600' : 'bg-gray-300'}
          `}
        >
          <span
            className={`
              absolute inline-block h-4 w-4 transform rounded-full bg-white
              transition-transform
              ${monitoringOn ? 'translate-x-6' : 'translate-x-1'}
            `}
          />
        </button>
      </div>
    </header>
  );
}
