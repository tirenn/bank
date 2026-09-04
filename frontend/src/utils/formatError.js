/**
 * Human-readable error message parser for Tirenn Core Banking & AI Copilot.
 * Converts technical backend, database, and network errors into clean, friendly user messages.
 */
export function formatHumanReadableError(err, fallback = 'Something went wrong. Please try again.') {
  if (!err) return fallback;

  // Extract raw message string from various Axios / standard error shapes
  let rawMsg = '';
  if (typeof err === 'string') {
    rawMsg = err;
  } else if (err.response?.data?.error) {
    rawMsg = err.response.data.error;
  } else if (err.response?.data?.detail) {
    rawMsg = err.response.data.detail;
  } else if (err.response?.data?.message) {
    rawMsg = err.response.data.message;
  } else if (err.message) {
    rawMsg = err.message;
  } else {
    rawMsg = String(err);
  }

  const lower = rawMsg.toLowerCase().trim();

  // 1. Account & Status Errors
  if (lower.includes('source account is not active') || lower.includes('selected source account is not active')) {
    return 'The selected account is currently frozen or inactive. Please choose an active account from the dropdown.';
  }
  if (lower.includes('destination account is not active')) {
    return "The recipient's account is currently inactive or frozen and cannot receive funds.";
  }
  if (lower.includes('destination account not found') || lower.includes('recipient account not found') || lower.includes('account number not found')) {
    return 'Recipient account not found. Please verify the account number and try again.';
  }
  if (lower.includes('source account not found') || lower.includes('sender account not found')) {
    return 'Your source account could not be found. Please refresh your page and select your account again.';
  }

  // 2. Transfer & Balance Errors
  if (lower.includes('insufficient') || lower.includes('insufficient account balance') || lower.includes('insufficient funds')) {
    return 'Insufficient balance. You do not have enough funds in this account for this transfer.';
  }
  if (lower.includes('cannot transfer funds to your own account') || lower.includes('same account')) {
    return 'You cannot transfer funds to the same account. Please choose a different recipient account.';
  }
  if (lower.includes('amount must be greater than zero') || lower.includes('strictly greater than zero')) {
    return 'Please enter a valid transfer amount greater than $0.00.';
  }
  if (lower.includes('daily transfer limit') || lower.includes('limit exceeded')) {
    return 'Daily transfer limit exceeded. Please adjust the transfer amount or update your daily limit in security settings.';
  }

  // 3. Confirmation OTP Gate Errors
  if (lower.includes('otp') || lower.includes('confirmation code')) {
    return 'Invalid or missing confirmation OTP. Please enter the valid 6-digit code (Demo: 888888).';
  }

  // 4. Card & Security Errors
  if (lower.includes('card is frozen') || lower.includes('frozen card')) {
    return 'This card is currently frozen. Please unfreeze it in your settings before making transactions.';
  }

  // 5. Auth & Identity Errors
  if (lower.includes('invalid credentials') || lower.includes('crypto/bcrypt') || lower.includes('unauthorized') || lower.includes('incorrect password')) {
    return 'Incorrect email or password. Please check your credentials and try again.';
  }
  if (lower.includes('already registered') || lower.includes('already exists') || lower.includes('duplicate key')) {
    return 'An account with this email address already exists. Please sign in instead.';
  }
  if (lower.includes('token expired') || lower.includes('jwt expired')) {
    return 'Your security session has expired. Please sign in again to continue.';
  }

  // 6. Network & Rate Limit Errors
  if (lower.includes('rate limit') || lower.includes('too many requests') || lower.includes('429')) {
    return 'Too many requests in a short period. Please wait a few moments before trying again.';
  }
  if (lower.includes('network error') || lower.includes('err_connection_refused') || lower.includes('failed to fetch')) {
    return 'Unable to reach the banking server. Please verify your internet connection.';
  }
  if (lower.includes('500') || lower.includes('internal server error')) {
    return 'The banking service encountered a temporary server error. Please try again shortly.';
  }

  // If already clean and user-friendly, return directly
  if (rawMsg.length > 0 && rawMsg.length < 120 && !rawMsg.includes('{') && !rawMsg.includes('Exception') && !rawMsg.includes('sql')) {
    return rawMsg;
  }

  return fallback;
}
