import { useState } from 'react';
import { ChevronDown, CheckCircle, AlertCircle } from 'lucide-react';

const Dropdown = ({ label, value, options, onChange }) => {
  const [open, setOpen] = useState(false);
  const selected = options.find((o) => o.id === value);
  const selectedName = selected ? selected.name : label;

  return (
    <div className="relative w-full">
      <button
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={label}
        onClick={() => setOpen((o) => !o)}
        className="
          flex w-full items-center justify-between gap-2 rounded-xl border border-gray-200
          bg-white px-4 py-3 text-left text-sm text-gray-800 shadow-soft
          hover:border-gray-300 focus-visible:outline-none focus-visible:ring-2
          focus-visible:ring-emerald-600
        "
      >
        <span>{selectedName}</span>
        <ChevronDown className="h-4 w-4 text-gray-500 transition-transform" />
      </button>
      {open && (
        <div
          className="
            absolute z-10 mt-1 w-full overflow-hidden rounded-xl border border-gray-200
            bg-white shadow-soft-md
          "
        >
          <ul role="listbox">
            {options.map((option) => (
              <li key={option.id}>
                <button
                  type="button"
                  role="option"
                  aria-selected={option.id === value}
                  onClick={() => {
                    onChange(option.id);
                    setOpen(false);
                  }}
                  className="
                    w-full px-4 py-3 text-left text-sm text-gray-800
                    hover:bg-gray-50 focus-visible:outline-none
                    data-[selected=true]:bg-emerald-50
                  "
                  data-selected={option.id === value ? 'true' : undefined}
                >
                  {option.name}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default function Dashboard({
  customers,
  selectedId,
  onSelect,
  monitoringOn,
  onShowDetails,
}) {
  const selected = customers.find((c) => c.id === selectedId) || customers[0];
  const flag = monitoringOn ? selected.flag : null;
  const isHealthy = !flag;

  return (
    <div className="w-full max-w-sm space-y-6 px-4 py-6">
      <div className="space-y-1">
        <label className="block text-xs font-medium text-gray-500">
          Demo customer
        </label>
        <Dropdown
          label="Demo customer"
          value={selectedId}
          options={customers}
          onChange={onSelect}
        />
      </div>

      <div
        className={`
          relative flex items-start gap-3 rounded-xl p-4
          ${
            isHealthy
              ? 'bg-green-50 ring-1 ring-green-100'
              : 'bg-amber-50 ring-1 ring-amber-100'
          }
        `}
      >
        {isHealthy ? (
          <CheckCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-green-600" />
        ) : (
          <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-amber-600" />
        )}
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-gray-900">
            {isHealthy
              ? 'Your finances look steady. No action needed.'
              : flag.message}
          </p>
          {!isHealthy && (
            <button
              type="button"
              onClick={onShowDetails}
              className="
                mt-2 inline-flex items-center gap-1 text-sm font-medium text-amber-800
                hover:underline
              "
            >
              See details
            </button>
          )}
        </div>
      </div>

      {!monitoringOn && (
        <p className="text-center text-xs text-gray-500">
          Monitoring is off. Turn it on in Settings to enable alerts.
        </p>
      )}
    </div>
  );
}
