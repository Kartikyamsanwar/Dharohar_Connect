import { useCallback, useEffect, useState } from 'react';
import { cancelBooking, deleteTrip, getBookings, getTrips, inr } from '../lib/api';
import { useAuth } from '../components/Auth';

export default function MyTrips({ setPage }) {
  const { user, ready, openAuth } = useAuth();
  const [bookings, setBookings] = useState([]);
  const [trips, setTrips] = useState([]);
  const [error, setError] = useState('');
  const [openTrip, setOpenTrip] = useState(null);

  const load = useCallback(async () => {
    try {
      const [b, t] = await Promise.all([getBookings(), getTrips()]);
      setBookings(b.bookings);
      setTrips(t.trips);
    } catch (err) { setError(err.message); }
  }, []);
  useEffect(() => { if (user) load(); }, [user, load]);

  if (!ready) return <main className="mx-auto max-w-5xl px-5 py-12 text-[#806b58]">Loading...</main>;
  if (!user) {
    return (
      <main className="mx-auto max-w-xl px-5 py-20 text-center">
        <h2 className="serif text-3xl font-bold">Your trips and bookings</h2>
        <p className="mt-3 text-[#806b58]">Log in to see your bookings and saved itineraries.</p>
        <button onClick={() => openAuth()} className="mt-6 rounded-full bg-[#6f2f24] px-6 py-3 font-bold text-white">Log in / Sign up</button>
      </main>
    );
  }

  const cancel = async (ref) => {
    if (!window.confirm('Cancel this booking?')) return;
    try { await cancelBooking(ref); load(); } catch (err) { setError(err.message); }
  };
  const remove = async (id) => { try { await deleteTrip(id); load(); } catch (err) { setError(err.message); } };

  return (
    <main className="mx-auto max-w-5xl px-5 py-12">
      <div className="text-xs font-bold uppercase tracking-[.25em] text-[#8d3528]">Hello, {user.name}</div>
      <h2 className="serif mt-2 text-4xl font-bold">My trips and bookings</h2>
      {error && <div className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-800">{error}</div>}

      <h3 className="mt-10 text-xl font-bold">Bookings</h3>
      <div className="mt-4 space-y-3">
        {bookings.length === 0 && <p className="text-sm text-[#806b58]">No bookings yet. <button onClick={() => setPage('BOOK')} className="font-bold text-[#8d3528]">Find a stay or tickets</button></p>}
        {bookings.map((b) => (
          <div key={b.ref} className={`flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-white p-5 shadow-sm ${b.status === 'cancelled' ? 'opacity-60' : ''}`}>
            <div>
              <div className="flex items-center gap-2"><span className="text-xs font-bold uppercase tracking-wider text-[#8d3528]">{b.kind}</span><span className="text-xs text-[#806b58]">{b.ref}</span>
                <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${b.status === 'confirmed' ? 'bg-emerald-100 text-emerald-800' : 'bg-gray-200 text-gray-700'}`}>{b.status}</span></div>
              <div className="mt-1 font-bold">{b.item_name}</div>
              <div className="text-sm text-[#705b49]">{b.kind === 'hotel' ? `${b.start_date} → ${b.end_date} · ${b.quantity} room(s)` : `${b.start_date} · ${b.quantity} ticket(s)`} · {inr(b.total)}</div>
              <div className="text-xs text-[#806b58]">{b.payment_status === 'refunded_simulated' ? 'Refund simulated (test mode)' : b.payment_note}</div>
            </div>
            {b.status === 'confirmed' && <button onClick={() => cancel(b.ref)} className="rounded-xl border border-red-300 px-4 py-2 text-sm font-bold text-red-700">Cancel</button>}
          </div>
        ))}
      </div>

      <h3 className="mt-10 text-xl font-bold">Saved itineraries</h3>
      <div className="mt-4 space-y-3">
        {trips.length === 0 && <p className="text-sm text-[#806b58]">Plan a trip and press “Save this trip”.</p>}
        {trips.map((t) => (
          <div key={t.id} className="rounded-2xl bg-white p-5 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div><div className="font-bold">{t.title}</div><div className="text-sm text-[#705b49]">{t.start_date} · {t.days} day(s)</div></div>
              <div className="flex gap-2">
                <button onClick={() => setOpenTrip(openTrip === t.id ? null : t.id)} className="rounded-xl bg-[#6f2f24] px-4 py-2 text-sm font-bold text-white">{openTrip === t.id ? 'Hide' : 'View'}</button>
                <button onClick={() => remove(t.id)} className="rounded-xl border border-[#6f4423]/20 px-4 py-2 text-sm font-bold">Delete</button>
              </div>
            </div>
            {openTrip === t.id && (
              <div className="mt-4 space-y-3">
                {t.payload.itinerary?.map((d) => (
                  <div key={d.day} className="rounded-xl bg-[#f8f1e5] p-4 text-sm">
                    <b>Day {d.day} · {d.theme}</b> <span className="text-xs text-[#806b58]">{d.date}</span>
                    <ul className="mt-2 space-y-1">{d.activities.map((a) => <li key={a}>• {a}</li>)}</ul>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </main>
  );
}
