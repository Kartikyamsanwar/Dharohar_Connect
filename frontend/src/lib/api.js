const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
const TOKEN_KEY = 'dh_token';

export const getToken = () => { try { return localStorage.getItem(TOKEN_KEY); } catch { return null; } };
export const setToken = (t) => { try { t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY); } catch { /* storage unavailable */ } };

async function request(path, options = {}) {
  const token = getToken();
  const headers = { ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers };
  const r = await fetch(`${API}${path}`, { ...options, headers });
  if (!r.ok) {
    let message = `Request failed (${r.status})`;
    try {
      const body = await r.json();
      const d = body.detail;
      message = typeof d === 'string' ? d : Array.isArray(d) ? d.map((e) => `${(e.loc || []).slice(-1)[0]}: ${e.msg}`).join('; ') : message;
    } catch { /* non-JSON error body */ }
    const err = new Error(message);
    err.status = r.status;
    if (r.status === 401 && token) window.dispatchEvent(new Event('dh-unauthorized'));
    throw err;
  }
  return r.json();
}

const post = (path, body) => request(path, { method: 'POST', body: JSON.stringify(body ?? {}) });
const qs = (params) => new URLSearchParams(Object.entries(params).filter(([, v]) => v !== '' && v != null)).toString();

export const getHeritage = (q = '') => request(`/heritage?q=${encodeURIComponent(q)}`);
export const chat = (message) => post('/chat', { message });
export const planTrip = (payload) => post('/plan', payload);

export const register = (data) => post('/auth/register', data);
export const login = (data) => post('/auth/login', data);
export const getMe = () => request('/auth/me');

export const getHotels = (params) => request(`/hotels?${qs(params)}`);
export const bookHotel = (data) => post('/bookings/hotel', data);
export const getTickets = (params) => request(`/tickets?${qs(params)}`);
export const bookTicket = (data) => post('/bookings/ticket', data);
export const getBookings = () => request('/bookings');
export const cancelBooking = (ref) => post(`/bookings/${ref}/cancel`);
export const saveTrip = (data) => post('/trips', data);
export const getTrips = () => request('/trips');
export const deleteTrip = (id) => request(`/trips/${id}`, { method: 'DELETE' });

export const getCommunity = (params = {}) => request(`/community?${qs(params)}`);
export const getCommunityPost = (id) => request(`/community/${id}`);
export const createCommunityPost = (data) => post('/community', data);
export const commentOnPost = (id, text) => post(`/community/${id}/comments`, { text });
export const likePost = (id) => post(`/community/${id}/like`);
export const getGroups = (params = {}) => request(`/groups?${qs(params)}`);
export const getGroup = (id) => request(`/groups/${id}`);
export const createGroup = (data) => post('/groups', data);
export const joinGroup = (id) => post(`/groups/${id}/join`);
export const leaveGroup = (id) => post(`/groups/${id}/leave`);
export const getCulture = (params = {}) => request(`/culture?${qs(params)}`);
export const getSafety = () => request('/safety');

export const siteImages = {
  Hampi: 'https://images.unsplash.com/photo-1600100397608-f0105f0b3b3c?auto=format&fit=crop&w=900&q=80',
  'Ajanta Caves': 'https://images.unsplash.com/photo-1598091383021-15ddea10925d?auto=format&fit=crop&w=900&q=80',
  'Ellora Caves': 'https://images.unsplash.com/photo-1599661046289-e31897846e41?auto=format&fit=crop&w=900&q=80',
  'Konark Sun Temple': 'https://images.unsplash.com/photo-1606298855672-3efb63017be8?auto=format&fit=crop&w=900&q=80',
};

export const NAV = ['HOME', 'EXPLORE', 'AI GUIDE', 'PLAN TRIP', 'BOOK', 'GROUPS', 'COMMUNITY', 'CULTURE', 'SAFETY'];

export const CULTURE_ICONS = {
  Architecture: '🏛️',
  'Traditional Arts': '🎨',
  Yoga: '🧘',
  Ayurveda: '🌿',
  'Indigenous Games': '🎮',
  'Performing Arts': '🎭',
  'Food Heritage': '🍛',
  'Ancient Science & Engineering': '🔬',
  'Festivals & Traditions': '🪔',
};

export const inr = (n) => `₹${Number(n).toLocaleString('en-IN')}`;
export const isoDate = (offsetDays = 0) => { const d = new Date(); d.setDate(d.getDate() + offsetDays); return d.toISOString().slice(0, 10); };
