import { useState } from 'react';
import { Search, MapPin } from 'lucide-react';

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
            <div className="relative h-48 w-full overflow-hidden bg-[#efe3d1]">
              <img src={s.image} alt={s.name} loading="lazy" className="h-full w-full object-cover transition group-hover:scale-105" />
              {s.image_credit && (
                <span className="absolute bottom-1 right-2 rounded bg-black/45 px-1.5 py-0.5 text-[9px] text-white/90">
                  © {s.image_credit.author} · {s.image_credit.license}
                </span>
              )}
            </div>
            <div className="p-5">
              <div className="text-xs font-bold uppercase tracking-wider text-[#8d3528]">{s.category}</div>
              <div className="mt-1 text-xl font-bold">{s.name}</div>
              <div className="mt-1 flex items-center gap-1 text-sm text-[#806b58]"><MapPin size={14} />{s.state}</div>
              <p className="mt-3 line-clamp-2 text-sm leading-6 text-[#806b58]">{s.description}</p>
            </div>
          </button>
        ))}
      </div>
      <p className="mt-10 text-xs text-[#806b58]">Photos from Wikimedia Commons, used under the licences shown on each image. Open a site for the photographer credit and source link.</p>
    </main>
  );
}
