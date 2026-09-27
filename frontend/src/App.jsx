import { useEffect, useState } from 'react';
import Header from './components/Header';
import Detail from './components/Detail';
import { AuthProvider } from './components/Auth';
import Home from './pages/Home';
import Explore from './pages/Explore';
import Guide from './pages/Guide';
import Planner from './pages/Planner';
import Book from './pages/Book';
import MyTrips from './pages/MyTrips';
import Groups from './pages/Groups';
import Community from './pages/Community';
import Culture from './pages/Culture';
import Safety from './pages/Safety';
import { getHeritage } from './lib/api';

export default function App() {
  const [page, setPage] = useState('HOME');
  const [sites, setSites] = useState([]);
  const [selected, setSelected] = useState(null);
  const [prefill, setPrefill] = useState(null);

  useEffect(() => {
    getHeritage().then(setSites).catch(() => {});
  }, []);

  const goBook = (data) => { setPrefill({ ...data, at: Date.now() }); setPage('BOOK'); };

  return (
    <AuthProvider>
      <div className="min-h-screen">
        <Header page={page} setPage={setPage} />
        {page === 'HOME' && <Home setPage={setPage} />}
        {page === 'EXPLORE' && <Explore sites={sites} setSelected={setSelected} />}
        {page === 'AI GUIDE' && <Guide />}
        {page === 'PLAN TRIP' && <Planner goBook={goBook} setPage={setPage} />}
        {page === 'BOOK' && <Book key={prefill?.at || 'book'} prefill={prefill} setPage={setPage} />}
        {page === 'MY TRIPS' && <MyTrips setPage={setPage} />}
        {page === 'GROUPS' && <Groups />}
        {page === 'COMMUNITY' && <Community />}
        {page === 'CULTURE' && <Culture setPage={setPage} />}
        {page === 'SAFETY' && <Safety />}
        {selected && <Detail site={selected} close={() => setSelected(null)} goBook={(d) => { setSelected(null); goBook(d); }} />}
        <footer className="mt-16 border-t border-[#6f4423]/10 p-8 text-center text-sm text-[#705b49]">
          DHAROHAR CONNECT · Connecting People with India&apos;s Heritage
        </footer>
      </div>
    </AuthProvider>
  );
}
