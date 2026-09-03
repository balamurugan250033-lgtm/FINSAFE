import { useState } from 'react';
import { Clock, Phone } from 'lucide-react';
import Snackbar from './Snackbar';

const offers = [
  {
    id: 'restructure',
    title: 'Restructure this card\'s EMI',
    description: 'Lower your monthly payment by extending the term.',
    icon: Clock,
    color: 'amber',
  },
  {
    id: 'advisor',
    title: 'Talk to a financial advisor',
    description: 'Free 15-minute call, no obligation.',
    icon: Phone,
    color: 'amber',
  },
];

const colorMap = {
  amber: {
    icon: 'text-amber-600',
    bg: 'bg-amber-50',
    ring: 'ring-amber-100',
    hover: 'hover:bg-amber-100',
  },
};

export default function Intervention({ onBack }) {
  const [snack, setSnack] = useState({ visible: false, message: '' });

  const handleRequest = () => {
    setSnack({ visible: true, message: 'Request received. Someone will follow up.' });
  };

  const handleClose = () =>
    setSnack({ visible: false, message: '' });

  return (
    <div className="w-full max-w-sm space-y-6 px-4 py-6">
      <header className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">
          Here's what might help
        </h2>
        <button
          type="button"
          onClick={onBack}
          className="rounded-full bg-gray-100 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-200"
        >
          Back
        </button>
      </header>

      <div className="space-y-4">
        {offers.map((offer) => {
          const Icon = offer.icon;
          const palette = colorMap[offer.color];
          return (
            <div
              key={offer.id}
              className={`
                flex items-start gap-3 rounded-xl p-4 ring-1 ${palette.bg} ${palette.ring}
              `}
            >
              <div
                className={`
                  mt-0.5 flex h-8 w-8 flex-shrink-0 items-center justify-center
                  rounded-lg bg-amber-100/60
                `}
              >
                <Icon className={`h-4 w-4 ${palette.icon}`} />
              </div>
              <div className="min-w-0 flex-1">
                <h3 className="text-sm font-medium text-gray-900">{offer.title}</h3>
                <p className="mt-0.5 text-sm text-gray-600">{offer.description}</p>
                <button
                  type="button"
                  onClick={handleRequest}
                  className="
                    mt-2 rounded-lg bg-amber-600 px-3.5 py-1.5 text-xs font-medium
                    text-white transition-colors hover:bg-amber-700
                  "
                >
                  Request
                </button>
              </div>
            </div>
          );
        })}
      </div>

      <button
        type="button"
        onClick={() => onBack()}
        className="block w-full text-center text-sm font-medium text-gray-600 hover:text-gray-900"
      >
        Not now
      </button>

      <Snackbar
        message={snack.message}
        visible={snack.visible}
        onClose={handleClose}
      />
    </div>
  );
}
