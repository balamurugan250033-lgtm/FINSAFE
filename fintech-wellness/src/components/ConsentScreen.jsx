import { useState } from 'react';
import { Check } from 'lucide-react';

const ToggleSwitch = ({ checked, onChange, labeled = true }) => {
  const toggle = () => onChange(!checked);
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={labeled ? 'Toggle monitoring' : 'Toggle'}
      onClick={toggle}
      className={`
        relative inline-flex h-6 w-11 items-center rounded-full transition-colors
        focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2
        focus-visible:ring-emerald-600
        ${checked ? 'bg-emerald-600' : 'bg-gray-300'}
      `}
    >
      <span
        className={`
          inline-block h-5 w-5 transform rounded-full bg-white shadow
          transition-transform
          ${checked ? 'translate-x-5' : 'translate-x-1'}
        `}
      >
        {checked && (
          <Check className="absolute inset-0 m-auto h-3.5 w-3.5 text-emerald-600" />
        )}
      </span>
    </button>
  );
};

export default function ConsentScreen({ onAccept }) {
  const [enabled, setEnabled] = useState(false);
  const [interacted, setInteracted] = useState(false);

  const handleToggle = (next) => {
    setEnabled(next);
    setInteracted(true);
  };

  const handleContinue = () => {
    onAccept(enabled);
  };

  return (
    <div className="flex min-h-full flex-col items-center justify-center gap-8 px-6 py-12">
      <div className="w-full max-w-sm space-y-6 text-center">
        <h1 className="text-2xl font-semibold text-gray-900">
          Financial Wellness Monitoring
        </h1>
        <p className="text-sm text-gray-600">
          We can monitor your transaction patterns to alert you early if we
          notice signs of financial stress — you stay in control.
        </p>

        <div className="flex items-center justify-center gap-3 pt-2">
          <span
            className={`text-sm font-medium ${
              enabled ? 'text-emerald-700' : 'text-gray-500'
            }`}
          >
            {enabled ? 'On' : 'Off'}
          </span>
          <ToggleSwitch checked={enabled} onChange={handleToggle} />
        </div>

        <button
          type="button"
          disabled={!interacted}
          onClick={handleContinue}
          className={`
            w-full rounded-xl px-5 py-3 text-sm font-medium text-white
            transition-colors
            disabled:cursor-not-allowed disabled:opacity-45
            ${
              interacted
                ? 'bg-emerald-600 hover:bg-emerald-700'
                : 'cursor-not-allowed bg-gray-300'
            }
          `}
        >
          Continue
        </button>
      </div>
    </div>
  );
}
