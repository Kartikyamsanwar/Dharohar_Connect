import { useEffect, useState } from 'react';
import { Plus, Search, MapPin, Heart, MessageCircle } from 'lucide-react';
import { getCommunity, createCommunityPost, commentOnPost, likePost } from '../lib/api';
import { useAuth } from '../components/Auth';
import { LabelBadge } from '../components/Detail';

export default function Community() {
  const { user, openAuth } = useAuth();
  const [comment, setComment] = useState('');
  const [notice, setNotice] = useState('');
  const [posts, setPosts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [filters, setFilters] = useState({ category: '', location: '', content_type: '' });
  const [selected, setSelected] = useState(null);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ title: '', description: '', category: 'Travel Experience', location: '' });

  const load = () => getCommunity(filters).then((d) => { setPosts(d.posts); setCategories(d.categories); }).catch(() => {});
  useEffect(() => { load(); }, []);

  const search = (e) => { e.preventDefault(); load(); };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!user) return openAuth('Log in to share a post.');
    try {
      await createCommunityPost(form);
      setShowCreate(false);
      setForm({ title: '', description: '', category: 'Travel Experience', location: '' });
      load();
    } catch (err) {
      setNotice(err.message);
    }
  };

  const requireAuth = (note) => { if (!user) { openAuth(note); return false; } return true; };
  const refreshSelected = (p) => { setSelected(p); load(); };
  const handleLike = async () => {
    if (!requireAuth('Log in to like posts.')) return;
    try { refreshSelected(await likePost(selected.id)); setNotice(''); } catch (err) { setNotice(err.message); }
  };
  const handleComment = async (e) => {
    e.preventDefault();
    if (!requireAuth('Log in to comment.') || !comment.trim()) return;
    try { refreshSelected(await commentOnPost(selected.id, comment)); setComment(''); setNotice(''); } catch (err) { setNotice(err.message); }
  };

  return (
    <main className="mx-auto max-w-7xl px-5 py-12">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="text-xs font-bold uppercase tracking-[.25em] text-[#8d3528]">Community Portal</div>
          <h2 className="serif mt-2 text-4xl font-bold">Share heritage knowledge</h2>
          <p className="mt-2 text-sm text-[#806b58]">Travelers · Students · Historians · Local communities · Heritage enthusiasts</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="flex items-center gap-2 rounded-full bg-[#6f2f24] px-5 py-2.5 text-sm font-bold text-white">
          <Plus size={16} /> Create Post
        </button>
      </div>

      <form onSubmit={search} className="mt-8 grid gap-3 rounded-3xl bg-white p-5 shadow-sm md:grid-cols-4">
        <select value={filters.category} onChange={(e) => setFilters({ ...filters, category: e.target.value })} className="rounded-xl bg-[#f8f1e5] px-4 py-2.5 outline-none">
          <option value="">All categories</option>
          {categories.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <input placeholder="Location" value={filters.location} onChange={(e) => setFilters({ ...filters, location: e.target.value })} className="rounded-xl bg-[#f8f1e5] px-4 py-2.5 outline-none" />
        <select value={filters.content_type} onChange={(e) => setFilters({ ...filters, content_type: e.target.value })} className="rounded-xl bg-[#f8f1e5] px-4 py-2.5 outline-none">
          <option value="">All types</option>
          <option value="verified">Verified source</option>
          <option value="community">Community contribution</option>
        </select>
        <button className="flex items-center justify-center gap-2 rounded-xl bg-[#6f2f24] py-2.5 font-bold text-white"><Search size={16} /> Filter</button>
      </form>

      <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {posts.map((p) => (
          <button key={p.id} onClick={() => setSelected(p)} className="card-hover rounded-3xl border border-[#6f4423]/10 bg-white p-5 text-left shadow-sm">
            <LabelBadge label={p.label} />
            <h3 className="mt-3 text-lg font-bold">{p.title}</h3>
            <p className="mt-2 line-clamp-3 text-sm leading-6 text-[#806b58]">{p.description}</p>
            <div className="mt-4 flex flex-wrap items-center gap-3 text-xs text-[#705b49]">
              <span>{p.author}</span>
              <span className="flex items-center gap-1"><MapPin size={12} />{p.location}</span>
              <span>{p.date}</span>
            </div>
            <div className="mt-3 flex gap-4 text-sm text-[#8d3528]">
              <span className="flex items-center gap-1"><Heart size={14} /> {p.likes}</span>
              <span className="flex items-center gap-1"><MessageCircle size={14} /> {p.comments?.length || 0}</span>
              <span className="rounded-full bg-[#f4e7d4] px-2 py-0.5 text-[10px] font-bold">{p.category}</span>
            </div>
          </button>
        ))}
      </div>

      {selected && (
        <div className="fixed inset-0 z-40 grid place-items-center bg-black/50 p-5" onClick={() => setSelected(null)}>
          <div className="max-h-[90vh] max-w-2xl overflow-auto rounded-3xl bg-[#fffaf2] p-7" onClick={(e) => e.stopPropagation()}>
            <LabelBadge label={selected.label} />
            <h3 className="serif mt-3 text-3xl font-bold">{selected.title}</h3>
            <div className="mt-2 text-sm text-[#705b49]">{selected.author} · {selected.location} · {selected.date}</div>
            <p className="mt-5 leading-7 text-[#705b49]">{selected.description}</p>
            {selected.related_heritage && (
              <div className="mt-5 rounded-2xl bg-[#f4e7d4] p-4 text-sm"><b>Related heritage:</b> {selected.related_heritage}</div>
            )}
            <div className="mt-4 flex items-center gap-3">
              <button onClick={handleLike} className="flex items-center gap-1 rounded-full border border-[#8d3528]/30 px-4 py-1.5 text-sm font-bold text-[#8d3528]"><Heart size={14} /> {selected.likes}</button>
              {notice && <span className="text-xs font-semibold text-red-700">{notice}</span>}
            </div>
            <div className="mt-5">
              <b className="text-sm">Comments</b>
              {selected.comments?.length ? selected.comments.map((c, i) => (
                <div key={i} className="mt-2 rounded-xl bg-white p-3 text-sm">
                  <b>{c.author}</b> <span className="text-xs text-[#806b58]">{c.date}</span>
                  <p className="mt-1">{c.text}</p>
                </div>
              )) : <p className="mt-2 text-sm text-[#806b58]">No comments yet.</p>}
              <form onSubmit={handleComment} className="mt-3 flex gap-2">
                <input value={comment} onChange={(e) => setComment(e.target.value)} maxLength={1000} placeholder={user ? 'Add a comment' : 'Log in to comment'} className="flex-1 rounded-xl bg-white px-3 py-2 text-sm outline-none" />
                <button className="rounded-xl bg-[#6f2f24] px-4 py-2 text-sm font-bold text-white">Post</button>
              </form>
            </div>
          </div>
        </div>
      )}

      {showCreate && (
        <div className="fixed inset-0 z-40 grid place-items-center bg-black/50 p-5" onClick={() => setShowCreate(false)}>
          <form onSubmit={handleCreate} className="w-full max-w-md rounded-3xl bg-white p-7" onClick={(e) => e.stopPropagation()}>
            <h3 className="serif text-2xl font-bold">Create Post</h3>
            <p className="mt-1 text-xs text-amber-700">👤 Posts are published under your name and marked COMMUNITY CONTRIBUTION</p>
            {[['title', 'Title'], ['description', 'Description'], ['location', 'Heritage location']].map(([k, l]) => (
              <label key={k} className="mt-3 block text-sm font-semibold">{l}
                <input value={form[k]} onChange={(e) => setForm({ ...form, [k]: e.target.value })} className="mt-1 w-full rounded-xl bg-[#f8f1e5] px-3 py-2 font-normal outline-none" required />
              </label>
            ))}
            <label className="mt-3 block text-sm font-semibold">Category
              <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} className="mt-1 w-full rounded-xl bg-[#f8f1e5] px-3 py-2 outline-none">
                {categories.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </label>
            {notice && <p className="mt-3 rounded-xl bg-red-50 p-3 text-sm text-red-800">{notice}</p>}
            <button type="submit" className="mt-5 w-full rounded-xl bg-[#6f2f24] py-3 font-bold text-white">Publish</button>
          </form>
        </div>
      )}
    </main>
  );
}
