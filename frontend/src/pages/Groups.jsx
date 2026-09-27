import { useEffect, useState } from 'react';
import { Users, Plus, Search, MapPin, Calendar, Wallet } from 'lucide-react';
import { getGroups, createGroup, joinGroup, leaveGroup } from '../lib/api';
import { useAuth } from '../components/Auth';

export default function Groups() {
  const { user, openAuth } = useAuth();
  const [groups, setGroups] = useState([]);
  const [filters, setFilters] = useState({ destination: '', interests: '', budget: '' });
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: '', destination: '', dates: '', budget_min: 5000, budget_max: 8000, interests: '', capacity: 6, description: '' });
  const [selected, setSelected] = useState(null);
  const [message, setMessage] = useState('');

  const load = () => getGroups(filters).then((d) => setGroups(d.groups)).catch(() => setGroups([]));
  useEffect(() => { load(); }, [user]); // eslint-disable-line react-hooks/exhaustive-deps

  const search = (e) => { e.preventDefault(); load(); };

  const handleJoin = async (id, joined) => {
    if (!user) return openAuth('Log in to join a group.');
    try {
      const r = await (joined ? leaveGroup(id) : joinGroup(id));
      setMessage(r.message);
      load();
      if (selected?.id === id) setSelected(r.group);
    } catch (err) {
      setMessage(err.message);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!user) return openAuth('Log in to create a group.');
    try {
      await createGroup(form);
      setShowCreate(false);
      setForm({ name: '', destination: '', dates: '', budget_min: 5000, budget_max: 8000, interests: '', capacity: 6, description: '' });
      load();
      setMessage('Group created. You are its first member.');
    } catch (err) {
      setMessage(err.message);
    }
  };

  return (
    <main className="mx-auto max-w-7xl px-5 py-12">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="text-xs font-bold uppercase tracking-[.25em] text-[#8d3528]">Group Travel</div>
          <h2 className="serif mt-2 text-4xl font-bold">Find a Group</h2>
          <p className="mt-2 text-sm text-[#806b58]">Discover compatible travelers for heritage destinations · <span className="font-bold text-amber-700">Prototype · no identity verification</span></p>
        </div>
        <button onClick={() => setShowCreate(true)} className="flex items-center gap-2 rounded-full bg-[#6f2f24] px-5 py-2.5 text-sm font-bold text-white">
          <Plus size={16} /> Create Group
        </button>
      </div>

      <form onSubmit={search} className="mt-8 grid gap-3 rounded-3xl bg-white p-5 shadow-sm md:grid-cols-4">
        <input placeholder="Destination" value={filters.destination} onChange={(e) => setFilters({ ...filters, destination: e.target.value })} className="rounded-xl bg-[#f8f1e5] px-4 py-2.5 outline-none" />
        <input placeholder="Interests" value={filters.interests} onChange={(e) => setFilters({ ...filters, interests: e.target.value })} className="rounded-xl bg-[#f8f1e5] px-4 py-2.5 outline-none" />
        <input placeholder="Budget (₹)" value={filters.budget} onChange={(e) => setFilters({ ...filters, budget: e.target.value })} className="rounded-xl bg-[#f8f1e5] px-4 py-2.5 outline-none" />
        <button className="flex items-center justify-center gap-2 rounded-xl bg-[#6f2f24] py-2.5 font-bold text-white"><Search size={16} /> Match</button>
      </form>

      {message && <div className="mt-4 rounded-xl bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div>}

      <div className="mt-8 grid gap-5 sm:grid-cols-2">
        {groups.map((g) => (
          <div key={g.id} className="card-hover rounded-3xl border border-[#6f4423]/10 bg-white p-6 shadow-sm">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <Users size={18} className="text-[#8d3528]" />
                  <h3 className="text-xl font-bold">{g.name}</h3>
                </div>
                {g.verified && <span className="mt-1 inline-block rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-800">✓ Verified organizer</span>}
              </div>
              <div className="flex flex-col items-end gap-1">
                <span className="rounded-full bg-[#f4e7d4] px-3 py-1 text-sm font-bold">{g.members}/{g.capacity}</span>
                {g.match_score !== null && g.match_score !== undefined && <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-800">{g.match_score}% match</span>}
              </div>
            </div>
            <div className="mt-4 space-y-2 text-sm text-[#705b49]">
              <div className="flex items-center gap-2"><MapPin size={14} /> {g.destination}</div>
              <div className="flex items-center gap-2"><Calendar size={14} /> {g.dates}</div>
              <div className="flex items-center gap-2"><Wallet size={14} /> {g.budget_label}</div>
              <div>{g.interests}</div>
            </div>
            <div className="mt-5 flex gap-2">
              <button onClick={() => setSelected(g)} className="rounded-xl border border-[#6f4423]/15 px-4 py-2 text-sm font-bold">View</button>
              <button onClick={() => handleJoin(g.id, g.joined)} className={`rounded-xl px-4 py-2 text-sm font-bold ${g.joined ? 'border border-[#6f2f24]/30 text-[#6f2f24]' : 'bg-[#6f2f24] text-white'}`}>{g.joined ? 'Leave Group' : 'Join Group'}</button>
            </div>
          </div>
        ))}
      </div>

      {selected && (
        <div className="fixed inset-0 z-40 grid place-items-center bg-black/50 p-5" onClick={() => setSelected(null)}>
          <div className="max-w-lg rounded-3xl bg-[#fffaf2] p-7" onClick={(e) => e.stopPropagation()}>
            <h3 className="serif text-2xl font-bold">{selected.name}</h3>
            <p className="mt-3 text-sm leading-6 text-[#705b49]">{selected.description}</p>
            <div className="mt-4 space-y-1 text-sm"><b>Organizer:</b> {selected.organizer}</div>
            <div className="mt-4 rounded-xl bg-amber-50 p-3 text-xs text-amber-900">Groups are matched by destination, budget and interests. There is no identity verification yet — meet in public places and use the Safety Center guidance.</div>
            <button onClick={() => handleJoin(selected.id, selected.joined)} className="mt-4 w-full rounded-xl bg-[#6f2f24] py-3 font-bold text-white">{selected.joined ? 'Leave Group' : 'Join Group'}</button>
          </div>
        </div>
      )}

      {showCreate && (
        <div className="fixed inset-0 z-40 grid place-items-center bg-black/50 p-5" onClick={() => setShowCreate(false)}>
          <form onSubmit={handleCreate} className="max-h-[90vh] w-full max-w-md overflow-auto rounded-3xl bg-white p-7" onClick={(e) => e.stopPropagation()}>
            <h3 className="serif text-2xl font-bold">Create Group</h3>
            {[['name', 'Group name'], ['destination', 'Destination'], ['dates', 'Travel dates'], ['interests', 'Interests'], ['description', 'Description']].map(([k, l]) => (
              <label key={k} className="mt-3 block text-sm font-semibold">{l}
                <input value={form[k]} onChange={(e) => setForm({ ...form, [k]: e.target.value })} className="mt-1 w-full rounded-xl bg-[#f8f1e5] px-3 py-2 font-normal outline-none" />
              </label>
            ))}
            <div className="mt-3 grid grid-cols-2 gap-3">
              <label className="text-sm font-semibold">Budget min<input type="number" value={form.budget_min} onChange={(e) => setForm({ ...form, budget_min: Number(e.target.value) })} className="mt-1 w-full rounded-xl bg-[#f8f1e5] px-3 py-2 outline-none" /></label>
              <label className="text-sm font-semibold">Budget max<input type="number" value={form.budget_max} onChange={(e) => setForm({ ...form, budget_max: Number(e.target.value) })} className="mt-1 w-full rounded-xl bg-[#f8f1e5] px-3 py-2 outline-none" /></label>
            </div>
            <button type="submit" className="mt-5 w-full rounded-xl bg-[#6f2f24] py-3 font-bold text-white">Create group</button>
          </form>
        </div>
      )}
    </main>
  );
}
