const customers = {
  healthy: {
    id: 'healthy',
    name: 'Healthy',
    flag: null,
    monthlyBalances: [42000, 45000, 43000, 47000, 46000, 48000],
  },
  minimum_due_streak: {
    id: 'minimum_due_streak',
    name: 'Minimum-Due Streak',
    flag: {
      message:
        'Your card payments have been minimum-due only for the last 3 months.',
      rule: 'Rule: 3+ consecutive minimum-due-only payments detected',
      highlightMonths: [3, 4, 5],
    },
    monthlyBalances: [40000, 38000, 30000, 22000, 15000, 9000],
  },
  balance_drop: {
    id: 'balance_drop',
    name: 'Balance Drop',
    flag: {
      message:
        'Your account balance has dropped sharply over the past 2 months.',
      rule: 'Rule: Balance velocity drop exceeds threshold over 2 months',
      highlightMonths: [4, 5],
    },
    monthlyBalances: [50000, 49000, 48000, 45000, 25000, 10000],
  },
  overleveraged: {
    id: 'overleveraged',
    name: 'Overleveraged',
    flag: {
      message:
        'A new loan was taken out shortly after your existing EMI began.',
      rule: 'Rule: New loan within 30 days of existing EMI start',
      highlightMonths: [2, 3],
    },
    monthlyBalances: [30000, 28000, 26000, 20000, 18000, 16000],
  },
};

export const customerList = Object.values(customers);
export const customerMap = customers;

export const monthLabels = ['Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr'];
export const currencyFormatter = (value) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);
