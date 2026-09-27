import { useState } from 'react';
import { ArrowRight, Sparkles, RefreshCw, Clock, CloudSun } from 'lucide-react';
import { planTrip, saveTrip, isoDate } from '../lib/api';
import { useAuth } from '../components/Auth';

function AgentLoading() {
  const agents = ['Orchestrator', 'Heritage Agent', 'Weather Agent', 'Travel Agent', 'Recommendation Agent', 'Itinerary Agent', 'Safety Agent'];
  return (
    <div className="rounded-3xl bg-[#211b17] p-7 text-[#fff7e9]">
      <div className="flex items-center gap-2 text-sm font-bold"><Sparkles size={17} className="text-[#f7d58a]" /> Agent activity</div>
      <div className="mt-6 grid gap-3">
        {agents.map((x, i) => (
          <div key={x} className="flex items-center justify-between rounded-2xl bg-white/5 p-4">
            <span>{i === 0 ? '🧠' : '✓'} {x}</span>
            <span className="animate-pulse text-xs text-[#f7d58a]">running</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function BudgetCard({ budget }) {
  const labels = { transport: 'Transport', stay: 'Stay', food: 'Food', local: 'Tickets & local' };
  return (
    <div className="rounded-3xl bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-2 font-bold">
        <span>💰 Estimated cost (per person)</span>
        {budget.within_budget !== null && (
          <span className={`rounded-full px-3 py-1 text-xs ${budget.within_budget ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'}`}>
            {budget.within_budget ? `Within budget · ₹${budget.difference.toLocaleString()} spare` : `Over budget by ₹${Math.abs(budget.difference).toLocaleString()}`}
          </span>
        )}
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-4">
        {Object.entries(budget.breakdown).map(([k, v]) => (
          <div key={k} className="rounded-2xl bg-[#f8f1e5] p-4">
            <div className="text-xs font-bold text-[#8d3528]">{labels[k] || k}</div>
            <div className="mt-1 text-xl font-bold">₹{v.toLocaleString()}</div>
          </div>
        ))}
      </div>
      <div className="mt-3 text-sm">Total <b>₹{budget.per_person_total.toLocaleString()}</b> of ₹{budget.budget_per_person.toLocaleString()} budget</div>
      <ul className="mt-3 space-y-1 text-xs text-[#806b58]">{budget.assumptions.map((a) => <li key={a}>• {a}</li>)}</ul>
    </div>
  );
}

function TripActions({ result, form, goBook }) {
  const { user, openAuth } = useAuth();
  const [status, setStatus] = useState('');
  const end = new Date(form.date);
  end.setDate(end.getDate() + Math.max(form.days, 1));
  const range = { destination: form.destination, check_in: form.date, check_out: end.toISOString().slice(0, 10), guests: form.travelers };

  const save = async () => {
    if (!user) return openAuth('Log in to save this trip.');
    try {
      await saveTrip({ title: `${form.from_location} → ${form.destination}`, destination: form.destination, start_date: form.date, days: form.days, payload: result });
      setStatus('Saved to My Trips.');
    } catch (err) { setStatus(err.message); }
  };

  return (
    <div className="flex flex-wrap items-center gap-2 rounded-3xl bg-white p-5 shadow-sm">
      <button onClick={() => goBook({ ...range, tab: 'stays' })} className="rounded-xl bg-[#6f2f24] px-5 py-2.5 text-sm font-bold text-white">Book stays for these dates</button>
      <button onClick={() => goBook({ ...range, tab: 'tickets' })} className="rounded-xl bg-[#6f2f24] px-5 py-2.5 text-sm font-bold text-white">Book monument tickets</button>
      <button onClick={save} className="rounded-xl border border-[#6f2f24]/25 px-5 py-2.5 text-sm font-bold text-[#6f2f24]">Save this trip</button>
      {status && <span className="text-sm font-semibold text-emerald-800">{status}</span>}
    </div>
  );
}

function TripResult({ result, form, goBook }) {
  return (
    <div className="space-y-5">
      <TripActions result={result} form={form} goBook={goBook} />
      <div className="rounded-3xl bg-[#211b17] p-6 text-white">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-[#f7d58a]">
          <Sparkles size={14} /> Multi-agent plan complete
        </div>
        <div className="serif mt-2 text-3xl font-bold">Your heritage journey</div>
        <div className="mt-4 flex flex-wrap gap-2">
          {result.travel?.origin && <span className="rounded-full bg-white/10 px-3 py-2 text-sm">📍 {result.travel.origin} → {result.travel.destination}</span>}
          {result.travel?.available && <span className="rounded-full bg-white/10 px-3 py-2 text-sm">🛣️ {result.travel.distance_km} km · {result.travel.duration_hours} hr</span>}
          <span className="rounded-full bg-white/10 px-3 py-2 text-sm">🌦️ {result.weather?.available ? 'Live forecast connected' : 'Live weather unavailable'}</span>
        </div>
      </div>

      <div className="rounded-3xl bg-white p-6 shadow-sm">
        <div className="flex items-center gap-2 font-bold text-[#8d3528]">🗺️ LIVE ROUTE</div>
        {result.travel?.available ? (
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <div className="rounded-2xl bg-[#f8f1e5] p-4">
              <div className="text-xs font-bold text-[#8d3528]">Distance</div>
              <div className="mt-2 text-2xl font-bold">{result.travel.distance_km} km</div>
            </div>
            <div className="rounded-2xl bg-[#f8f1e5] p-4">
              <div className="text-xs font-bold text-[#8d3528]">Drive time</div>
              <div className="mt-2 text-2xl font-bold">{result.travel.duration_hours} hr</div>
            </div>
          </div>
        ) : (
          <div className="mt-4 rounded-2xl border border-amber-300 bg-amber-50 p-4 text-sm">
            <b>Route unavailable</b>
            <div className="mt-1">{result.travel?.note}</div>
          </div>
        )}
      </div>

      <div className="rounded-3xl bg-white p-6 shadow-sm">
        <div className="flex items-center gap-2 font-bold text-[#8d3528]"><CloudSun size={18} /> LIVE TRAVEL CONDITIONS</div>
        {result.weather?.available ? (
          <>
            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              {result.weather.forecast.map((x) => (
                <div key={x.date} className="rounded-2xl bg-[#f8f1e5] p-4">
                  <div className="flex items-center justify-between gap-2">
                    <div className="text-xs font-bold text-[#8d3528]">{x.date}</div>
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${x.source === 'forecast' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-900'}`}>{x.source === 'forecast' ? 'LIVE FORECAST' : 'HISTORICAL AVG'}</span>
                  </div>
                  <div className="mt-2 text-2xl font-bold">{x.temp_min}–{x.temp_max}°C</div>
                  <div className="text-sm capitalize text-[#806b58]">{x.condition}</div>
                  <div className="mt-2 text-xs">Rain chance: <b>{x.rain_probability}%</b>{x.precipitation_mm ? ` · ${x.precipitation_mm} mm` : ''}</div>
                  {x.windows?.morning != null && (
                    <div className="mt-2 grid grid-cols-3 gap-1 text-center text-[10px] font-semibold">
                      {['morning', 'afternoon', 'evening'].map((w) => (
                        <div key={w} className={`rounded-lg px-1 py-1 ${x.windows[w] >= 60 ? 'bg-blue-200 text-blue-900' : 'bg-white text-[#705b49]'}`}>{w.slice(0, 3).toUpperCase()} {x.windows[w]}%</div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
            <div className="mt-2 text-[11px] text-[#806b58]">Source: {result.weather.provider} · {result.weather.live_days} live day(s){result.weather.historical_days ? ` · ${result.weather.historical_days} historical` : ''}</div>
            {result.weather.planning_impact?.length > 0 && (
              <div className="mt-4 rounded-2xl border border-[#6f4423]/10 bg-[#f4e7d4] p-4">
                <div className="text-xs font-bold uppercase tracking-wider text-[#8d3528]">Planning impact</div>
                <ul className="mt-2 space-y-1 text-sm leading-6">
                  {result.weather.planning_impact.map((p) => <li key={p}>→ {p}</li>)}
                </ul>
              </div>
            )}
          </>
        ) : (
          <div className="mt-4 rounded-2xl border border-amber-300 bg-amber-50 p-4 text-sm">
            <b>Live weather unavailable</b>
            <div className="mt-1">{result.weather?.error || 'The planner will not fabricate weather.'}</div>
          </div>
        )}
      </div>

      {result.recommendations && (
        <div className="rounded-3xl bg-[#eef1e7] p-6">
          <div className="font-bold">✓ Recommendation Agent</div>
          <p className="mt-2 whitespace-pre-wrap text-sm leading-6">{result.recommendations.summary}</p>
        </div>
      )}

      {result.recommendations?.budget && <BudgetCard budget={result.recommendations.budget} />}

      <div className="rounded-3xl bg-white p-6 shadow-sm">
        <div className="flex items-center gap-2 font-bold"><Clock size={17} /> Adaptive itinerary</div>
        <div className="mt-5 space-y-4">
          {result.itinerary?.map((d) => (
            <div key={d.day} className="rounded-2xl bg-[#f8f1e5] p-5">
              <div className="flex justify-between">
                <b>DAY {d.day}{d.theme ? ` · ${d.theme}` : ''}</b>
                {d.weather && <span className="text-xs font-semibold">{d.date} · {d.weather.temp_max}°C · {d.weather.rain_probability}% rain</span>}
              </div>
              <ul className="mt-3 space-y-2 text-sm leading-6">{d.activities.map((a) => <li key={a}>• {a}</li>)}</ul>
              <div className="mt-3 text-xs font-semibold text-[#8d3528]">{d.note}</div>
              {d.agent_note && <div className="mt-3 whitespace-pre-wrap rounded-xl bg-white p-3 text-xs leading-5">💡 {d.agent_note}</div>}
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-3xl bg-[#eef1e7] p-6">
        <div className="font-bold">🛡️ Safety Agent</div>
        <ul className="mt-3 space-y-2 text-sm">{result.safety?.map((x) => <li key={x}>✓ {x}</li>)}</ul>
        {result.safety_disclaimer && <p className="mt-4 text-xs italic text-[#705b49]">{result.safety_disclaimer}</p>}
      </div>

      <div className="rounded-3xl bg-[#211b17] p-6 text-white">
        <div className="text-xs font-bold uppercase tracking-widest text-[#f7d58a]">Agent Activity</div>
        <div className="mt-4 grid gap-2 sm:grid-cols-2">
          {result.agent_activity?.map((x) => (
            <div key={x.name} className="rounded-xl bg-white/5 p-3 text-sm">
              {x.icon || '✓'} {x.name}
              <span className={`float-right text-xs ${x.status === 'unavailable' ? 'text-amber-300' : 'text-[#f7d58a]'}`}>{x.status}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function Planner({ goBook }) {
  const [form, setForm] = useState({
    from_location: 'Pune', destination: 'Hampi', date: isoDate(7), days: 3, budget: 8000, interests: 'Architecture, History', travelers: 2,
  });
  const [planned, setPlanned] = useState(form);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      setResult(await planTrip(form));
      setPlanned(form);
    } catch (err) {
      setError(err.status ? err.message : 'Could not reach the backend. Make sure the API server is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="mx-auto max-w-7xl px-5 py-12">
      <div className="grid gap-8 lg:grid-cols-[380px_1fr]">
        <section>
          <div className="text-xs font-bold uppercase tracking-[.25em] text-[#8d3528]">AI Trip Planner</div>
          <h2 className="serif mt-2 text-4xl font-bold">Plan with live intelligence.</h2>
          <p className="mt-3 leading-7 text-[#806b58]">Orchestrator → Heritage · Weather · Travel → Recommendation → Itinerary → Safety</p>
          <form onSubmit={submit} className="mt-7 space-y-3 rounded-3xl bg-white p-5 shadow-sm">
            {[['from_location', 'From'], ['destination', 'Destination'], ['date', 'Start date'], ['days', 'Days'], ['travelers', 'Travelers'], ['budget', 'Budget per person (₹)'], ['interests', 'Interests']].map(([k, l]) => {
              const numeric = ['days', 'budget', 'travelers'].includes(k);
              return (
                <label key={k} className="block text-sm font-semibold">
                  {l}
                  <input type={k === 'date' ? 'date' : numeric ? 'number' : 'text'} min={k === 'date' ? isoDate(0) : numeric ? 1 : undefined} max={k === 'days' ? 14 : undefined} required value={form[k]} onChange={(e) => setForm({ ...form, [k]: numeric ? Number(e.target.value) : e.target.value })} className="mt-1 w-full rounded-xl border border-[#6f4423]/10 bg-[#fbf6ed] px-3 py-2.5 font-normal outline-none" />
                </label>
              );
            })}
            {error && <div className="rounded-xl bg-red-50 p-3 text-sm text-red-800">{error}</div>}
            <button disabled={loading} className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#6f2f24] py-3 font-bold text-white">
              {loading ? <><RefreshCw className="animate-spin" size={17} /> Agents planning...</> : <>Plan with DHAROHAR <ArrowRight size={17} /></>}
            </button>
          </form>
        </section>
        <section>
          {loading ? <AgentLoading /> : result ? <TripResult result={result} form={planned} goBook={goBook} /> : (
            <div className="grid min-h-[500px] place-items-center rounded-3xl border border-dashed border-[#6f4423]/20 bg-white/50">
              <div className="max-w-sm text-center">
                <Sparkles className="mx-auto text-[#8d3528]" />
                <h3 className="serif mt-4 text-2xl font-bold">Your journey will appear here</h3>
                <p className="mt-2 text-sm leading-6 text-[#806b58]">Start the planner to see the multi-agent workflow, live weather status and adaptive itinerary.</p>
              </div>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
