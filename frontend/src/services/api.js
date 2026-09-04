import axios from 'axios';

const CORE_API_BASE = import.meta.env.VITE_CORE_API_URL || '/api/v1';
const AI_API_BASE = import.meta.env.VITE_AI_API_URL || '/api/v1/ai';
export const DEFAULT_TRANSFER_OTP = import.meta.env.VITE_DEFAULT_TRANSFER_OTP || '888888';


const coreClient = axios.create({
  baseURL: CORE_API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

const aiClient = axios.create({
  baseURL: AI_API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to attach JWT token
const attachAuthInterceptor = (client) => {
  client.interceptors.request.use((config) => {
    const token = localStorage.getItem('bank_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });
};

attachAuthInterceptor(coreClient);
attachAuthInterceptor(aiClient);

export const authApi = {
  login: async (email, password) => {
    const res = await coreClient.post('/auth/login', { email, password });
    return res.data;
  },
  register: async (email, password, fullName) => {
    const res = await coreClient.post('/auth/register', { email, password, full_name: fullName });
    return res.data;
  },
  getMe: async () => {
    const res = await coreClient.get('/auth/me');
    return res.data;
  },
  updateAddress: async (street, city, state, postalCode, country) => {
    const res = await coreClient.put('/users/address', {
      street,
      city,
      state,
      postal_code: postalCode,
      country,
    });
    return res.data;
  },
  updateKYC: async (docType, docNumber) => {
    const res = await coreClient.put('/users/kyc', {
      doc_type: docType,
      doc_number: docNumber,
    });
    return res.data;
  },
};

export const bankingApi = {
  getMyAccount: async () => {
    const res = await coreClient.get('/accounts/my');
    return res.data;
  },
  getAccounts: async () => {
    const res = await coreClient.get('/accounts');
    return res.data;
  },
  createAccount: async (accountName, accountType = 'SAVINGS', currency = 'USD', cardBrand = 'VISA', initialDepositDollars = 500) => {
    const res = await coreClient.post('/accounts', {
      account_name: accountName,
      account_type: accountType,
      currency: currency,
      card_brand: cardBrand,
      initial_deposit_dollars: Number(initialDepositDollars),
    });
    return res.data;
  },
  lookupAccount: async (accountNumber) => {
    const res = await coreClient.get(`/accounts/lookup/${accountNumber}`);
    return res.data;
  },

  transfer: async (toAccountNumber, amountDollars, description, category = 'Transfer', otp = '', fromAccountId = null) => {
    const amountCents = Math.round(amountDollars * 100);
    const payload = {
      to_account_number: toAccountNumber,
      amount_cents: amountCents,
      description: description || 'Transfer',
      category: category,
      otp: String(otp || '').trim(),
    };
    if (fromAccountId) {
      payload.from_account_id = Number(fromAccountId);
    }
    const res = await coreClient.post('/transfers', payload);
    return res.data;
  },
  deposit: async (amountDollars, description, category = 'Deposit') => {
    const amountCents = Math.round(amountDollars * 100);
    const res = await coreClient.post('/transfers/deposit', {
      amount_cents: amountCents,
      description: description || 'Account Deposit',
      category: category,
    });
    return res.data;
  },
  getTransactions: async (limit = 50, offset = 0, category = '') => {
    const params = { limit, offset };
    if (category) params.category = category;
    const res = await coreClient.get('/transactions', { params });
    return res.data;
  },
  getTransactionDetail: async (identifier) => {
    const res = await coreClient.get(`/transactions/${identifier}`);
    return res.data;
  },
  getSpendingSummary: async () => {
    const res = await coreClient.get('/transactions/summary');
    return res.data;
  },
  getStatement: async (startDate, endDate) => {
    const payload = {};
    if (startDate) payload.start_date = startDate;
    if (endDate) payload.end_date = endDate;
    const res = await coreClient.post('/accounts/statements', payload);
    return res.data;
  },
  updateStatus: async (frozen, reason = '') => {
    const res = await coreClient.put('/accounts/status', { frozen, reason });
    return res.data;
  },
  updateLimits: async (dailyLimitDollars) => {
    const daily_transfer_limit_cents = Math.round(dailyLimitDollars * 100);
    const res = await coreClient.put('/accounts/limits', { daily_transfer_limit_cents });
    return res.data;
  },
  getBeneficiaries: async () => {
    const res = await coreClient.get('/beneficiaries');
    return res.data;
  },
  addBeneficiary: async (nickname, accountNumber, bankName = 'Tirenn Core Bank') => {
    const res = await coreClient.post('/beneficiaries', {
      nickname,
      account_number: accountNumber,
      bank_name: bankName,
    });
    return res.data;
  },
  deleteBeneficiary: async (id) => {
    const res = await coreClient.delete(`/beneficiaries/${id}`);
    return res.data;
  },
  convertForex: async (fromCurrency, toCurrency, amount) => {
    const res = await coreClient.post('/forex/convert', {
      from: fromCurrency,
      to: toCurrency,
      amount: Number(amount),
    });
    return res.data;
  },
  calculateLoan: async (principal, annualRatePct, termMonths, loanType = 'PERSONAL') => {
    const res = await coreClient.post('/loans/calculate', {
      principal: Number(principal),
      annual_rate_pct: Number(annualRatePct),
      term_months: Number(termMonths),
      loan_type: loanType,
    });
    return res.data;
  },
};



export const aiAssistantApi = {
  getAvailableModels: async () => {
    const res = await aiClient.get('/models');
    return res.data;
  },
  sendChat: async (messages, apiKey = '', model = '') => {
    const isPaid = Boolean(apiKey && model);
    const payload = {
      messages,
      ...(isPaid ? { openrouter_api_key: apiKey, model } : {}),
    };
    const res = await aiClient.post('/chat', payload);
    return res.data;
  },
  resetSession: async () => {
    const res = await aiClient.delete('/session');
    return res.data;
  },
  getSessionHistory: async () => {
    const res = await aiClient.get('/session/history');
    return res.data;
  },
  getCostAnalytics: async () => {
    const res = await aiClient.get('/analytics/cost');
    return res.data;
  },
  resetCostAnalytics: async () => {
    const res = await aiClient.post('/analytics/cost/reset');
    return res.data;
  },
};




export const ragAdminApi = {
  listDocuments: async () => {
    const res = await aiClient.get('/faq');
    return res.data;
  },
  uploadText: async (topic, content, chunkSize = 500, overlap = 100) => {
    const res = await aiClient.post('/faq/upload', {
      topic,
      content,
      chunk_size: chunkSize,
      overlap: overlap,
    });
    return res.data;
  },
  uploadFile: async (file, topic, chunkSize = 500, overlap = 100) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('topic', topic);
    formData.append('chunk_size', chunkSize);
    formData.append('overlap', overlap);

    const res = await aiClient.post('/faq/upload-file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },
  deleteDocument: async (docId) => {
    const res = await aiClient.delete(`/faq/${docId}`);
    return res.data;
  },
  deleteBatch: async (batchId) => {
    const res = await aiClient.delete(`/faq/batch/${batchId}`);
    return res.data;
  },
};

export const adminModelApi = {
  listModels: async () => {
    const res = await coreClient.get('/admin/ai/models');
    return res.data;
  },
};




