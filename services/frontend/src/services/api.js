import axios from 'axios';

const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL !== undefined && import.meta.env.VITE_API_URL !== null ? import.meta.env.VITE_API_URL : 'http://localhost:8000',
});

// Request Interceptor: Attach Google Access Token to headers if it exists
API.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('google_access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Capture refreshed tokens and handle auto refresh on 401
API.interceptors.response.use(
  (response) => {
    // Check if the response contains refreshed tokens from multi-account sync
    if (response.data && response.data.refreshed_tokens) {
      const refreshed = response.data.refreshed_tokens;
      try {
        let accounts = JSON.parse(localStorage.getItem('aeroinbox_accounts')) || [];
        let updated = false;
        for (const [email, newToken] of Object.entries(refreshed)) {
          const idx = accounts.findIndex(a => a.email === email);
          if (idx > -1) {
            accounts[idx].access_token = newToken;
            updated = true;
          }
          if (email === localStorage.getItem('user_email')) {
            localStorage.setItem('google_access_token', newToken);
          }
        }
        if (updated) {
          localStorage.setItem('aeroinbox_accounts', JSON.stringify(accounts));
        }
      } catch (e) {
        console.error("Error updating refreshed tokens in localStorage", e);
      }
    }
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    
    // If the response is 401 Unauthorized and we haven't retried yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      const refreshToken = localStorage.getItem('google_refresh_token');
      
      if (refreshToken) {
        originalRequest._retry = true;
        try {
          // Request a new access token from the backend
          const response = await axios.post(`${API.defaults.baseURL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          
          const { access_token } = response.data;
          
          // Store the fresh access token
          localStorage.setItem('google_access_token', access_token);
          
          // Update original request headers and retry the request
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return API(originalRequest);
        } catch (refreshError) {
          // If token refresh fails, clear auth data and redirect to login
          console.error('OAuth token refresh failed. Redirecting to login.', refreshError);
          localStorage.removeItem('google_access_token');
          localStorage.removeItem('google_refresh_token');
          localStorage.removeItem('user_email');
          window.location.href = '/';
          return Promise.reject(refreshError);
        }
      } else {
        // No refresh token available, redirect to login
        localStorage.removeItem('google_access_token');
        localStorage.removeItem('user_email');
        window.location.href = '/';
      }
    }
    
    return Promise.reject(error);
  }
);

export default API;
