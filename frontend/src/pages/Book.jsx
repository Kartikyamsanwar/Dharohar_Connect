import { useEffect, useState } from 'react';
import { BedDouble, Ticket, Star, CheckCircle2 } from 'lucide-react';
import { bookHotel, bookTicket, getHotels, getTickets, inr, isoDate } from '../lib/api';
import { useAuth } from '../components/Auth';

function Confirmation({ booking, onDone, setPage }) {
  return (
    <div className="fixed inset-0 z-40 grid place-items-center bg-black/50 p-5" onClick={onDone}>
      <div className="w-full max-w-md rounded-3xl bg-white p-7 text-center" onClick={(e) => e.stopPropagation()}>
        <CheckCircle2 className="mx-auto text-emerald-600" size={44} />
        <h3 className="serif mt-3 text-2xl font-bold">Booking confirmed</h3>
        <div className="mt-4 rounded-2xl bg-[#f8f1e5] p-4 text-left text-sm leading-6">
          <div><b>Reference:</b> {booking.ref}</div>
          <div><b>{booking.item_name}</b></div>
          <div>{booking.kind === 'hotel' ? `${booking.start_date} to ${booking.end_date} · ${booking.quantity} room(s) · ${booking.guests} guest(s)` : `${booking.start_date} · ${booking.quantity} ticket(s)`}</div>
          <div><b>Total:</b> {inr(booking.total)}</div>
        </div>
        <p className="mt-3 text-xs text-amber-800">{booking.payment_note}</p>
        <div className="mt-5 flex gap-2">
          <button onClick={onDone} className="flex-1 rounded-xl border border-[#6f4423]/15 py-2.5 font-bold">Keep browsing</button>
          <button onClick={() => { onDone(); setPage('MY TRIPS'); }} className="flex-1 rounded-xl bg-[#6f2f24] py-2.5 font-bold text-white">My bookings</button>
        </div>
      </div>
    </div>
  );
}

function Stays({ prefill, onBooked }) {
  const { user, openAuth } = useAuth();
  const [form, setForm] = useState({ destination: prefill?.destination || 'Hampi', check_in: prefill?.check_in || isoDate(7), check_out: prefill?.check_out || isoDate(9), rooms: 1, guests: prefill?.guests || 2 });
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState('');

  const search = async (e) => {
    e?.preventDefault();
    setError('');
    setBusy('search');
    try { setData(await getHotels(form)); } catch (err) { setError(err.message); setData(null); } finally { setBusy(''); }
  };
  useEffect(() => { search(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const book = async (h) => {
    if (!user) return openAuth('Log in to book a stay.');
    setBusy(h.id);
    setError('');
    try { onBooked(await bookHotel({ hotel_id: h.id, check_in: form.check_in, check_out: form.check_out, rooms: Number(form.rooms), guests: Number(form.guests) })); await search(); }
    catch (err) { setError(err.message); } finally { setBusy(''); }
  };

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const input = 'mt-1 w-full rounded-xl bg-[#f8f1e5] px-3 py-2.5 font-normal outline-none';
  return (
    <>
      <form onSubmit={search} className="mt-6 grid gap-3 rounded-3xl bg-white p-5 shadow-sm sm:grid-cols-2 lg:grid-cols-6">
        <label className="text-sm font-semibold lg:col-span-2">Destination<input value={form.destination} onChange={set('destination')} placeholder="Site, city or state" className={input} /></label>
        <label className="text-sm font-semibold">Check-in<input type="date" min={isoDate(0)} value={form.check_in} onChange={set('check_in')} className={input} /></label>
        <label className="text-sm font-semibold">Check-out<input type="date" min={form.check_in} value={form.check_out} onChange={set('check_out')} className={input} /></label>
        <label className="text-sm font-semibold">Rooms<input type="number" min="1" max="5" value={form.rooms} onChange={set('rooms')} className={input} /></label>
        <label className="text-sm font-semibold">Guests<input type="number" min="1" max="15" value={form.guests} onChange={set('guests')} className={input} /></label>
        <button disabled={busy === 'search'} className="rounded-xl bg-[#6f2f24] py-2.5 font-bold text-white sm:col-span-2 lg:col-span-6">{busy === 'search' ? 'Searching...' : 'Search stays'}</button>
      </form>
      {error && <div className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-800">{error}</div>}
      {data && <p className="mt-4 text-xs text-[#806b58]">{data.inventory_note}</p>}
      <div className="mt-4 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
        {data?.hotels.map((h) => (
          <div key={h.id} className="card-hover rounded-3xl border border-[#6f4423]/10 bg-white p-5 shadow-sm">
            <div className="flex items-start justify-between gap-2">
              <div><div className="text-xs font-bold uppercase tracking-wider text-[#8d3528]">{h.tier} · {h.city}</div><h3 className="mt-1 text-lg font-bold">{h.name}</h3></div>
              <span className="flex items-center gap-1 rounded-full bg-[#f4e7d4] px-2 py-1 text-xs font-bold"><Star size={12} /> {h.rating}</span>
            </div>
            <p className="mt-2 text-sm text-[#806b58]">{h.description}</p>
            <div className="mt-2 text-xs text-[#705b49]">Near: {h.near.join(', ')}</div>
            <div className="mt-3 flex flex-wrap gap-1">{h.amenities.map((a) => <span key={a} className="rounded-full bg-[#eef1e7] px-2 py-0.5 text-[10px] font-semibold">{a}</span>)}</div>
            <div className="mt-4 flex items-end justify-between">
              <div>
                <div className="text-xl font-bold">{inr(h.price_per_night)}<span className="text-xs font-normal text-[#806b58]"> / night</span></div>
                {h.total_price != null && <div className="text-xs text-[#705b49]">{inr(h.total_price)} for {h.nights} night(s) · {h.available_rooms} room(s) left</div>}
              </div>
              <button disabled={busy === h.id || h.bookable === false} onClick={() => book(h)} className="rounded-xl bg-[#6f2f24] px-4 py-2 text-sm font-bold text-white disabled:bg-gray-300">
                {h.bookable === false ? 'Sold out' : busy === h.id ? 'Booking...' : 'Book now'}
              </button>
            </div>
          </div>
        ))}
        {data && data.hotels.length === 0 && <p className="text-sm text-[#806b58]">No stays match that destination yet.</p>}
      </div>
    </>
  );
}

function Tickets({ prefill, onBooked }) {
  const { user, openAuth } = useAuth();
  const [destination, setDestination] = useState(prefill?.destination || 'Hampi');
  const [visit, setVisit] = useState(prefill?.check_in || isoDate(7));
  const [data, setData] = useState(null);
  const [qty, setQty] = useState({});
  const [error, setError] = useState('');
  const [busy, setBusy] = useState('');

  const search = async (e) => {
    e?.preventDefault();
    setError('');
    try { setData(await getTickets({ destination, visit_date: visit })); } catch (err) { setError(err.message); setData(null); }
  };
  useEffect(() => { search(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const book = async (t) => {
    if (!user) return openAuth('Log in to book tickets.');
    setBusy(t.id);
    setError('');
    try { onBooked(await bookTicket({ ticket_id: t.id, visit_date: visit, quantity: Number(qty[t.id] || 1) })); await search(); }
    catch (err) { setError(err.message); } finally { setBusy(''); }
  };

  const input = 'mt-1 w-full rounded-xl bg-[#f8f1e5] px-3 py-2.5 font-normal outline-none';
  return (
    <>
      <form onSubmit={search} className="mt-6 grid gap-3 rounded-3xl bg-white p-5 shadow-sm sm:grid-cols-3">
        <label className="text-sm font-semibold">Monument or state<input value={destination} onChange={(e) => setDestination(e.target.value)} className={input} /></label>
        <label className="text-sm font-semibold">Visit date<input type="date" min={isoDate(0)} value={visit} onChange={(e) => setVisit(e.target.value)} className={input} /></label>
        <button className="self-end rounded-xl bg-[#6f2f24] py-2.5 font-bold text-white">Check tickets</button>
      </form>
      {error && <div className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-800">{error}</div>}
      {data && <p className="mt-4 text-xs text-[#806b58]">{data.inventory_note}</p>}
      <div className="mt-4 grid gap-5 md:grid-cols-2">
        {data?.sites.map((s) => (
          <div key={s.heritage_id} className="rounded-3xl border border-[#6f4423]/10 bg-white p-5 shadow-sm">
            <div className="text-xs font-bold uppercase tracking-wider text-[#8d3528]">{s.state}</div>
            <h3 className="text-lg font-bold">{s.site}</h3>
            <div className="mt-3 space-y-2">
              {s.tickets.map((t) => (
                <div key={t.id} className="flex flex-wrap items-center justify-between gap-2 rounded-2xl bg-[#f8f1e5] p-3">
                  <div><div className="text-sm font-bold">{t.name}</div><div className="text-xs text-[#806b58]">{t.price === 0 ? 'Free entry' : inr(t.price)} each{t.available != null && ` · ${t.available} left`}</div></div>
                  <div className="flex items-center gap-2">
                    <input aria-label="quantity" type="number" min="1" max="10" value={qty[t.id] || 1} onChange={(e) => setQty({ ...qty, [t.id]: e.target.value })} className="w-16 rounded-lg bg-white px-2 py-1.5 text-sm outline-none" />
                    <button disabled={busy === t.id || t.available === 0} onClick={() => book(t)} className="rounded-lg bg-[#6f2f24] px-3 py-1.5 text-sm font-bold text-white disabled:bg-gray-300">{t.available === 0 ? 'Sold out' : busy === t.id ? '...' : 'Book'}</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
        {data && data.sites.length === 0 && <p className="text-sm text-[#806b58]">No monuments match that search.</p>}
      </div>
    </>
  );
}

export default function Book({ prefill, setPage }) {
  const [tab, setTab] = useState(prefill?.tab || 'stays');
  const [done, setDone] = useState(null);
  const tabBtn = (id, Icon, label) => (
    <button onClick={() => setTab(id)} className={`flex items-center gap-2 rounded-full px-5 py-2.5 text-sm font-bold ${tab === id ? 'bg-[#6f2f24] text-white' : 'bg-white text-[#6f2f24]'}`}><Icon size={16} /> {label}</button>
  );
  return (
    <main className="mx-auto max-w-7xl px-5 py-12">
      <div className="text-xs font-bold uppercase tracking-[.25em] text-[#8d3528]">Book your journey</div>
      <h2 className="serif mt-2 text-4xl font-bold">Stays and monument tickets</h2>
      <p className="mt-2 text-sm text-[#806b58]">Live availability by date. <span className="font-bold text-amber-700">Demo inventory · payments run in test mode.</span></p>
      <div className="mt-6 flex gap-2">{tabBtn('stays', BedDouble, 'Stays')}{tabBtn('tickets', Ticket, 'Tickets')}</div>
      {tab === 'stays' ? <Stays prefill={prefill} onBooked={setDone} /> : <Tickets prefill={prefill} onBooked={setDone} />}
      {done && <Confirmation booking={done} onDone={() => setDone(null)} setPage={setPage} />}
    </main>
  );
}
