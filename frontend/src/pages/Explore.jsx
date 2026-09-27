import { useState } from 'react';
import { Search, MapPin } from 'lucide-react';
import { siteImages } from '../lib/api';

function gradientFor(name) {
  let h = 0;
  for (const c of name) h = (h * 31 + c.charCodeAt(0)) % 360;
  return `linear-gradient(135deg, hsl(${h % 40 + 5}, 55%, 38%), hsl(${(h % 40) + 30}, 60%, 55%))`;
}

export default function Explore({ sites, setSelected }) {
  const [q, setQ] = useState('');
  const filtered = sites.filter((s) => (s.name + s.state + s.category).toLowerCase().includes(q.toLowerCase()));

  return (
    <main className="mx-auto max-w-7xl px-5 py-12">
      <div className="flex flex-wrap items-end justify-between gap-5">
        <div>
          <div className="text-xs font-bold uppercase tracking-[.25em] text-[#8d3528]">Heritage Explorer</div>
          <h2 className="serif mt-2 text-4xl font-bold">{sites.length ? `${sites.length} gateways` : 'Gateways'} into India&apos;s past.</h2>
        </div>
        <div className="flex w-full max-w-md items-center gap-2 rounded-2xl border border-[#6f4423]/15 bg-white px-4 py-3">
          <Search size={18} />
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search Hampi, architecture, Odisha..." className="w-full bg-transparent outline-none" />
        </div>
      </div>
      <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {filtered.map((s) => (
          <button key={s.id} onClick={() => setSelected(s)} className="group card-hover overflow-hidden rounded-3xl border border-[#6f4423]/10 bg-white text-left shadow-sm">
            {siteImages[s.name] ? (
              <img src={siteImages[s.name]} alt={s.name} className="h-48 w-full object-cover transition group-hover:scale-105" />
            ) : (
              <div className="grid h-48 w-full place-items-center text-6xl text-white/90" style={{ background: gradientFor(s.name) }}>{s.name[0]}</div>
            )}
            <div className="p-5">
              <div className="text-xs font-bold uppercase tracking-wider text-[#8d3528]">{s.category}</div>
              <div className="mt-1 text-xl font-bold">{s.name}</div>
              <div className="mt-1 flex items-center gap-1 text-sm text-[#806b58]"><MapPin size={14} />{s.state}</div>
              <p className="mt-3 line-clamp-2 text-sm leading-6 text-[#806b58]">{s.description}</p>
            </div>
          </button>
        ))}
      </div>
    </main>
  );
}
