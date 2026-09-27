import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { getMe, getToken, login as apiLogin, register as apiRegister, setToken } from '../lib/api';

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(!getToken());
  const [modal, setModal] = useState(null);

  useEffect(() => {
    if (!getToken()) return;
    getMe().then(setUser).catch(() => setToken(null)).finally(() => setReady(true));
  }, []);

  useEffect(() => {
    const onExpired = () => { setToken(null); setUser(null); setModal({ note: 'Your session expired. Please log in again.' }); };
    window.addEventListener('dh-unauthorized', onExpired);
    return () => window.removeEventListener('dh-unauthorized', onExpired);
  }, []);

  const finish = useCallback((res) => { setToken(res.token); setUser(res.user); setModal(null); }, []);
  const logout = useCallback(() => { setToken(null); setUser(null); }, []);
  const openAuth = useCallback((note = '') => setModal({ note }), []);

  const value = useMemo(() => ({ user, ready, openAuth, logout, finish }), [user, ready, openAuth, logout, finish]);
  return (
    <AuthContext.Provider value={value}>
      {children}
      {modal && <AuthModal note={modal.note} onClose={() => setModal(null)} finish={finish} />}
    </AuthContext.Provider>
  );
}

function AuthModal({ note, onClose, finish }) {
  const [mode, setMode] = useState('login');
  const [form, setForm] = useState({ name: '', email: '', password: '', phone: '' });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    setBusy(true);
    try {
      finish(mode === 'login' ? await apiLogin({ email: form.email, password: form.password }) : await apiRegister(form));
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const field = (k, label, type = 'text', extra = {}) => (
    <label className="mt-3 block text-sm font-semibold">{label}
      <input type={type} value={form[k]} onChange={(e) => setForm({ ...form, [k]: e.target.value })} className="mt-1 w-full rounded-xl bg-[#f8f1e5] px-3 py-2.5 font-normal outline-none" {...extra} />
    </label>
  );

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/50 p-5" onClick={onClose}>
      <form onSubmit={submit} className="w-full max-w-md rounded-3xl bg-white p-7" onClick={(e) => e.stopPropagation()}>
        <h3 className="serif text-2xl font-bold">{mode === 'login' ? 'Welcome back' : 'Create your account'}</h3>
        {note && <p className="mt-2 rounded-xl bg-amber-50 p-3 text-sm text-amber-900">{note}</p>}
        {mode === 'register' && field('name', 'Full name', 'text', { required: true, minLength: 2 })}
        {field('email', 'Email', 'email', { required: true, autoComplete: 'email' })}
        {mode === 'register' && field('phone', 'Phone (optional)', 'tel')}
        {field('password', 'Password', 'password', { required: true, minLength: mode === 'register' ? 8 : 1, autoComplete: mode === 'login' ? 'current-password' : 'new-password' })}
        {mode === 'register' && <p className="mt-1 text-xs text-[#806b58]">At least 8 characters.</p>}
        {error && <p className="mt-3 rounded-xl bg-red-50 p-3 text-sm text-red-800">{error}</p>}
        <button disabled={busy} className="mt-5 w-full rounded-xl bg-[#6f2f24] py-3 font-bold text-white disabled:opacity-60">{busy ? 'Please wait...' : mode === 'login' ? 'Log in' : 'Sign up'}</button>
        <button type="button" onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(''); }} className="mt-3 w-full text-sm font-semibold text-[#8d3528]">
          {mode === 'login' ? 'New here? Create an account' : 'Already registered? Log in'}
        </button>
      </form>
    </div>
  );
}
