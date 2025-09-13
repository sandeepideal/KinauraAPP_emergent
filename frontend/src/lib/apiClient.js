/**
 * Centralized API client with retry logic, error handling, and 401 management
 */

let toast; // Will be injected by App.js

export const setToastInstance = (toastInstance) => {
  toast = toastInstance;
};

class APIError extends Error {
  constructor(message, status, response) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.response = response;
  }
}

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Calculate exponential backoff delay
 */
const getBackoffDelay = (attempt) => {
  const baseDelay = 1000; // 1 second
  const maxDelay = 10000; // 10 seconds
  const delay = Math.min(baseDelay * Math.pow(2, attempt), maxDelay);
  // Add jitter to prevent thundering herd
  return delay + Math.random() * 1000;
};

/**
 * Check if error is retryable
 */
const isRetryableError = (status) => {
  return status === 429 || status >= 500;
};

/**
 * Handle 401 errors by attempting token refresh
 */
const handle401Error = async () => {
  try {
    const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (response.ok) {
      const data = await response.json();
      if (data.access_token) {
        localStorage.setItem('token', data.access_token);
        return true; // Refresh successful
      }
    }
  } catch (error) {
    console.error('Token refresh failed:', error);
  }

  // Refresh failed, logout user
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  
  if (toast) {
    toast.error('Your session has expired. Please log in again.');
  }
  
  // Redirect to login
  window.location.href = '/';
  return false;
};

/**
 * Main API client function
 */
export const apiClient = async (path, options = {}) => {
  const {
    method = 'GET',
    body,
    headers = {},
    timeout = 12000,
    maxRetries = 2,
    skipAuth = false,
    skipToast = false
  } = options;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  // Prepare headers
  const requestHeaders = {
    'Content-Type': 'application/json',
    ...headers
  };

  // Add auth token if not skipped
  if (!skipAuth) {
    const token = localStorage.getItem('token');
    if (token) {
      requestHeaders['Authorization'] = `Bearer ${token}`;
    }
  }

  // Prepare request config
  const config = {
    method,
    headers: requestHeaders,
    signal: controller.signal,
    credentials: 'include' // For cookies
  };

  if (body) {
    config.body = typeof body === 'string' ? body : JSON.stringify(body);
  }

  let lastError;
  let attempt = 0;

  while (attempt <= maxRetries) {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}${path}`,
        config
      );

      clearTimeout(timeoutId);

      // Handle 401 errors
      if (response.status === 401 && !skipAuth && attempt === 0) {
        const refreshSuccess = await handle401Error();
        if (refreshSuccess) {
          // Update authorization header and retry
          const newToken = localStorage.getItem('token');
          if (newToken) {
            config.headers['Authorization'] = `Bearer ${newToken}`;
            attempt++;
            continue;
          }
        }
        // If refresh failed, don't retry
        throw new APIError('Authentication failed', 401, response);
      }

      // Handle other client errors (don't retry)
      if (response.status >= 400 && response.status < 500 && response.status !== 429) {
        const errorText = await response.text();
        let errorMessage;
        
        try {
          const errorData = JSON.parse(errorText);
          errorMessage = errorData.detail || errorData.message || `Request failed with status ${response.status}`;
        } catch {
          errorMessage = errorText || `Request failed with status ${response.status}`;
        }
        
        throw new APIError(errorMessage, response.status, response);
      }

      // Handle server errors and rate limiting (retry these)
      if (isRetryableError(response.status) && attempt < maxRetries) {
        const delay = getBackoffDelay(attempt);
        console.warn(`Request failed with status ${response.status}, retrying after ${delay}ms...`);
        await sleep(delay);
        attempt++;
        continue;
      }

      // If we've exhausted retries for server errors
      if (!response.ok) {
        const errorText = await response.text();
        let errorMessage;
        
        try {
          const errorData = JSON.parse(errorText);
          errorMessage = errorData.detail || errorData.message || `Request failed with status ${response.status}`;
        } catch {
          errorMessage = errorText || `Request failed with status ${response.status}`;
        }
        
        throw new APIError(errorMessage, response.status, response);
      }

      // Success - parse response
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }
      
      return await response.text();

    } catch (error) {
      clearTimeout(timeoutId);
      
      // Handle abort/timeout
      if (error.name === 'AbortError') {
        lastError = new APIError('Request timeout', 408);
        break;
      }

      // Handle network errors
      if (error instanceof TypeError && error.message.includes('fetch')) {
        lastError = new APIError('Network error - please check your connection', 0);
        if (attempt < maxRetries) {
          const delay = getBackoffDelay(attempt);
          console.warn(`Network error, retrying after ${delay}ms...`);
          await sleep(delay);
          attempt++;
          continue;
        }
        break;
      }

      // Re-throw APIErrors and other errors
      if (error instanceof APIError) {
        lastError = error;
        break;
      }

      lastError = error;
      break;
    }
  }

  // Show toast for errors (unless skipped)
  if (!skipToast && toast && lastError) {
    if (lastError.status === 0) {
      toast.networkError();
    } else {
      toast.apiError(lastError);
    }
  }

  throw lastError;
};

/**
 * Convenience methods for different HTTP methods
 */
export const api = {
  get: (path, options = {}) => 
    apiClient(path, { ...options, method: 'GET' }),
  
  post: (path, body, options = {}) => 
    apiClient(path, { ...options, method: 'POST', body }),
  
  put: (path, body, options = {}) => 
    apiClient(path, { ...options, method: 'PUT', body }),
  
  delete: (path, options = {}) => 
    apiClient(path, { ...options, method: 'DELETE' }),
  
  patch: (path, body, options = {}) => 
    apiClient(path, { ...options, method: 'PATCH', body })
};

export default apiClient;