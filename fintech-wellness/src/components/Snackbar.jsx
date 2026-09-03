import { useEffect } from 'react';
import { CheckCircle } from 'lucide-react';

export default function Snackbar({ message, visible, onClose }) {
  useEffect(() => {
    if (!visible) return undefined;
    const timer = setTimeout(onClose, 3200);
    return () => clearTimeout(timer);
  }, [visible, onClose]);

  return (
    <div
      className={`
        fixed bottom-0 left-1/2 -translate-x-1/2 rounded-t-2xl border border-gray-200
        bg-white px-5 py-3 text-sm shadow-soft-md transition-transform
        sm:max-w-sm sm:rounded-2xl sm:static sm:translate-x-0
        ${visible ? 'translate-y-0' : 'translate-y-full sm:translate-y-0'}
      `}
    >
      <div className="flex items-center gap-2 text-gray-800">
        <CheckCircle className="h-4 w-4 text-emerald-600" />
        <span>{message}</span>
      </div>
    </div>
  );
}
