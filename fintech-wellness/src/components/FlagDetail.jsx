import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceArea,
  CartesianGrid,
} from 'recharts';
import { monthLabels, currencyFormatter } from '../data/customers';

const formatY = (value) => currencyFormatter(value);

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload || !payload.length) return null;
  return (
    <div className="min-w-[120px] rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs shadow-soft">
      <p className="text-gray-500">{label}</p>
      <p className="font-medium text-gray-800">
        {currencyFormatter(payload[0].value)}
      </p>
    </div>
  );
};

export default function FlagDetail({ customer, onBack, onShowIntervention }) {
  const flag = customer.flag;
  const highlightSet = new Set(flag.highlightMonths || []);
  const data = customer.monthlyBalances.map((value, index) => ({
    month: monthLabels[index] ?? `#${index + 1}`,
    value,
    index,
  }));

  const low = Math.min(...customer.monthlyBalances) / 2;

  return (
    <div className="w-full max-w-sm space-y-6 px-4 py-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">Flagged activity</h2>
        <button
          type="button"
          onClick={onBack}
          className="rounded-full bg-gray-100 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-200"
        >
          Back
        </button>
      </div>

      <p className="text-sm text-gray-800">{flag.message}</p>

      <div className="h-56 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 10, right: 8, left: -18, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f1f1" vertical={false} />
            <XAxis
              dataKey="month"
              tickLine={false}
              axisLine={false}
              tick={{ fill: '#9ca3af', fontSize: 12 }}
            />
            <YAxis
              tickLine={false}
              axisLine={false}
              tick={{ fill: '#9ca3af', fontSize: 12 }}
              tickFormatter={formatY}
              domain={['dataMin - 1000', 'dataMax + 5000']}
            />
            <Tooltip content={<CustomTooltip />} />

            {customer.monthlyBalances
              .map((_, i) => i)
              .filter((i) => highlightSet.has(i))
              .map((i) => {
                const next = i + 1;
                if (next >= data.length) return null;
                return (
                  <ReferenceArea
                    key={`band-${i}`}
                    x1={i}
                    x2={next}
                    y1={low}
                    y2="dataMax"
                    fill="#fffbeb"
                    fillOpacity={1}
                    strokeOpacity={0}
                  />
                );
              })}

            <Line
              type="monotone"
              dataKey="value"
              stroke="#4d7c0f"
              strokeWidth={2.5}
              dot={{ r: 4, fill: '#fff', stroke: '#4d7c0f', strokeWidth: 2 }}
              activeDot={{ r: 6, fill: '#fff', stroke: '#4d7c0f', strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <p className="text-sm text-gray-500">
        Why you're seeing this:{' '}
        <span className="text-gray-700">{flag.rule}</span>
      </p>

      <button
        type="button"
        onClick={onShowIntervention}
        className="
          w-full rounded-xl bg-emerald-600 px-5 py-3 text-sm font-medium text-white
          hover:bg-emerald-700 focus-visible:outline-none
          focus-visible:ring-2 focus-visible:ring-emerald-600 focus-visible:ring-offset-2
        "
      >
        See what you can do
      </button>
    </div>
  );
}
