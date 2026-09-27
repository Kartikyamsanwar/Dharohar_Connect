import { Compass } from 'lucide-react';
import { NAV } from '../lib/api';
import { useAuth } from './Auth';

export default function Header({ page, setPage }) {
  const { user, openAuth, logout } = useAuth();
  return (
    <header className="sticky top-0 z-20 border-b border-[#6f4423]/10 bg-[#fbf4e8]/90 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-5 py-4">
        <button onClick={() => setPage('HOME')} className="flex shrink-0 items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-2xl bg-[#6f2f24] text-[#f7d58a]">
            <Compass size={22} />
          </div>
          <div className="text-left">
            <div className="serif text-xl font-bold tracking-wide">DHAROHAR</div>
            <div className="text-[10px] font-semibold tracking-[.25em] text-[#876b52]">CONNECT</div>
          </div>
        </button>
        <nav className="hidden flex-wrap justify-center gap-4 lg:flex xl:gap-5">
          {NAV.map((n) => (
            <button
              key={n}
              onClick={() => setPage(n)}
              className={`text-[10px] font-bold tracking-wider xl:text-xs ${page === n ? 'text-[#8d3528]' : 'text-[#705b49] hover:text-[#8d3528]'}`}
            >
              {n}
            </button>
          ))}
        </nav>
        <select
          className="rounded-xl border border-[#6f4423]/15 bg-white px-2 py-2 text-xs font-bold text-[#6f2f24] lg:hidden"
          value={page}
          onChange={(e) => setPage(e.target.value)}
        >
          {[...NAV, ...(user ? ['MY TRIPS'] : [])].map((n) => (
            <option key={n} value={n}>{n}</option>
          ))}
        </select>
        <div className="flex shrink-0 items-center gap-2">
          {user ? (
            <>
              <button onClick={() => setPage('MY TRIPS')} className={`hidden text-xs font-bold sm:block ${page === 'MY TRIPS' ? 'text-[#8d3528]' : 'text-[#705b49]'}`}>MY TRIPS · {user.name.split(' ')[0]}</button>
              <button onClick={logout} className="rounded-full border border-[#6f2f24]/25 px-4 py-2 text-xs font-bold text-[#6f2f24]">Log out</button>
            </>
          ) : (
            <button onClick={() => openAuth()} className="rounded-full bg-[#6f2f24] px-4 py-2 text-xs font-bold text-white shadow-sm">Log in</button>
          )}
        </div>
      </div>
    </header>
  );
}
