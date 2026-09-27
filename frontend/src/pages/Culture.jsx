import { useEffect, useState } from 'react';
import { Search, BookOpen } from 'lucide-react';
import { getCulture, CULTURE_ICONS } from '../lib/api';

export default function Culture({ setPage }) {
  const [items, setItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [filters, setFilters] = useState({ category: '', region: '' });

  const load = () => getCulture(filters).then((d) => { setItems(d.items); setCategories(d.categories); }).catch(() => {});
  useEffect(() => { load(); }, []);

  const search = (e) => { e.preventDefault(); load(); };

  return (
    <main className="mx-auto max-w-7xl px-5 py-12">
      <div>
        <div className="text-xs font-bold uppercase tracking-[.25em] text-[#8d3528]">Cultural Knowledge Hub</div>
        <h2 className="serif mt-2 text-4xl font-bold">India&apos;s living heritage</h2>
        <p className="mt-2 text-sm text-[#806b58]">Curated knowledge connecting to the Heritage Explorer</p>
      </div>

      <form onSubmit={search} className="mt-8 flex flex-wrap gap-3 rounded-3xl bg-white p-5 shadow-sm">
        <select value={filters.category} onChange={(e) => setFilters({ ...filters, category: e.target.value })} className="rounded-xl bg-[#f8f1e5] px-4 py-2.5 outline-none">
          <option value="">All categories</option>
          {categories.map((c) => <option key={c} value={c}>{CULTURE_ICONS[c] || '📚'} {c}</option>)}
        </select>
        <input placeholder="Region" value={filters.region} onChange={(e) => setFilters({ ...filters, region: e.target.value })} className="rounded-xl bg-[#f8f1e5] px-4 py-2.5 outline-none" />
        <button className="flex items-center gap-2 rounded-xl bg-[#6f2f24] px-5 py-2.5 font-bold text-white"><Search size={16} /> Filter</button>
      </form>

      <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((item) => (
          <div key={item.id} className="card-hover rounded-3xl border border-[#6f4423]/10 bg-white p-6 shadow-sm">
            <div className="text-2xl">{CULTURE_ICONS[item.category] || '📚'}</div>
            <div className="mt-2 text-xs font-bold uppercase tracking-wider text-[#8d3528]">{item.category}</div>
            <h3 className="mt-1 text-xl font-bold">{item.title}</h3>
            <p className="mt-3 text-sm leading-6 text-[#806b58]">{item.summary}</p>
            <div className="mt-4 text-xs text-[#705b49]">Region: {item.region}</div>
            <div className="mt-2 rounded-full border border-[#6f2f24]/10 bg-[#f4e7d4] px-3 py-1 text-xs font-semibold inline-block">✓ {item.source}</div>
            {item.heritage_link && (
              <button onClick={() => setPage('EXPLORE')} className="mt-4 flex items-center gap-1 text-sm font-bold text-[#8d3528]">
                <BookOpen size={14} /> Explore {item.heritage_link}
              </button>
            )}
          </div>
        ))}
      </div>
    </main>
  );
}
