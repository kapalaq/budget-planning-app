const BASE = '/api';

function getToken() {
  return localStorage.getItem('token');
}

function setToken(token) {
  localStorage.setItem('token', token);
}

function clearToken() {
  localStorage.removeItem('token');
}

async function request(method, path, body = null, { auth = true, params = {} } = {}) {
  const url = new URL(BASE + path, window.location.origin);
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null) url.searchParams.set(k, v);
  });

  const headers = { 'Content-Type': 'application/json' };
  if (auth) {
    const token = getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(url.toString(), {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401) {
    clearToken();
    window.location.href = '/login';
    throw new Error('Unauthorized');
  }

  const json = await res.json();
  if (!res.ok) throw new Error(json.detail || json.message || 'Request failed');
  return json;
}

const api = {
  // Auth
  login: (login, password) => request('POST', '/auth/login', { login, password }, { auth: false }),
  register: (login, password) => request('POST', '/auth/register', { login, password }, { auth: false }),

  // Dashboard
  getDashboard: () => request('GET', '/dashboard'),
  getPortfolio: () => request('GET', '/portfolio'),

  // Transactions
  getTransaction: (index) => request('GET', `/transactions/${index}`),
  addTransaction: (data) => request('POST', '/transactions', data),
  editTransaction: (index, data) => request('PUT', `/transactions/${index}`, data),
  deleteTransaction: (index) => request('DELETE', `/transactions/${index}`),

  // Categories
  getCategories: (type = 'expense') => request('GET', '/categories', null, { params: { transaction_type: type } }),
  suggestAmount: (category, type = 'expense') => request('GET', '/suggest-amount', null, { params: { category, transaction_type: type } }),

  // Wallets
  getWallets: () => request('GET', '/wallets'),
  getWalletDetail: (name) => request('GET', `/wallets/${encodeURIComponent(name)}`),
  addWallet: (data) => request('POST', '/wallets', data),
  editWallet: (name, data) => request('PUT', `/wallets/${encodeURIComponent(name)}`, data),
  deleteWallet: (name) => request('DELETE', `/wallets/${encodeURIComponent(name)}`),
  switchWallet: (name) => request('POST', '/wallets/switch', { name }),

  // Transfer
  getTransferContext: () => request('GET', '/transfer'),
  transfer: (data) => request('POST', '/transfer', data),

  // Sorting
  getSortingOptions: () => request('GET', '/sorting'),
  setSorting: (data) => request('POST', '/sorting', data),

  // Filters
  getActiveFilters: () => request('GET', '/filters'),
  addFilter: (data) => request('POST', '/filters', data),
  removeFilter: (index) => request('DELETE', `/filters/${index}`),
  clearFilters: () => request('DELETE', '/filters'),

  // Percentages
  getPercentages: () => request('GET', '/percentages'),

  // Recurring
  getRecurringList: () => request('GET', '/recurring'),
  getRecurringDetail: (index) => request('GET', `/recurring/${index}`),
  addRecurring: (data) => request('POST', '/recurring', data),
  editRecurring: (index, data) => request('PUT', `/recurring/${index}`, data),
  deleteRecurring: (index, option = 1) => request('DELETE', `/recurring/${index}`, null, { params: { delete_option: option } }),
  processRecurring: () => request('POST', '/recurring/process'),

  // Goals
  getGoals: (filter = 'active') => request('GET', '/goals', null, { params: { filter } }),
  getAllGoals: () => request('GET', '/goals/all'),
  getGoalDetail: (name) => request('GET', `/goals/${encodeURIComponent(name)}`),
  addGoal: (data) => request('POST', '/goals', data),
  saveToGoal: (data) => request('POST', '/goals/save', data),
  completeGoal: (name) => request('POST', `/goals/${encodeURIComponent(name)}/complete`),
  hideGoal: (name) => request('POST', `/goals/${encodeURIComponent(name)}/hide`),
  reactivateGoal: (name) => request('POST', `/goals/${encodeURIComponent(name)}/reactivate`),
  deleteGoal: (name) => request('DELETE', `/goals/${encodeURIComponent(name)}`),

  // Bills
  getBills: (filter = 'active') => request('GET', '/bills', null, { params: { filter } }),
  getAllBills: () => request('GET', '/bills/all'),
  getBillDetail: (name) => request('GET', `/bills/${encodeURIComponent(name)}`),
  addBill: (data) => request('POST', '/bills', data),
  saveToBill: (data) => request('POST', '/bills/save', data),
  completeBill: (name) => request('POST', `/bills/${encodeURIComponent(name)}/complete`),
  hideBill: (name) => request('POST', `/bills/${encodeURIComponent(name)}/hide`),
  reactivateBill: (name) => request('POST', `/bills/${encodeURIComponent(name)}/reactivate`),
  deleteBill: (name) => request('DELETE', `/bills/${encodeURIComponent(name)}`),

  // Settings
  getLanguage: () => request('GET', '/settings/language'),
  setLanguage: (language) => request('POST', '/settings/language', { language }),
  getTimezone: () => request('GET', '/settings/timezone'),
  setTimezone: (timezone) => request('POST', '/settings/timezone', { timezone }),

  // Currency
  convert: (amount, from, to) => request('GET', '/currency/convert', null, { params: { amount, from_currency: from, to_currency: to } }),
};

export { getToken, setToken, clearToken };
export default api;
