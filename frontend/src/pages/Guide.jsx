import { useEffect, useRef, useState } from 'react';
import { Send, RotateCcw, CloudSun, Wallet, BookOpenCheck, ArrowRight, Sparkles } from 'lucide-react';
import { chat, inr } from '../lib/api';
import { LabelBadge } from '../components/Detail';
import Markdown from '../components/Markdown';

const STORE = 'dh_guide_chat';
const WELCOME = {
  role: 'ai',
  text: "Namaste! I'm **DHAROHAR**, your heritage guide. Ask me about a monument's history, check the live weather before you go, or get a trip-cost estimate from your city.",
};
const STARTERS = [
  'Why is Hampi architecturally important?',
  'Will it rain at the Taj Mahal this weekend?',
  'How much is a 3-day trip to Jaipur from Delhi for 2?',
  'Which Buddhist heritage sites can I visit?',
];
const TOOL_LABELS = {
  search_heritage: { icon: BookOpenCheck, text: 'Searched verified records' },
  get_weather: { icon: CloudSun, text: 'Checked live weather' },
  estimate_trip_cost: { icon: Wallet, text: 'Estimated trip cost' },
};

const load = () => {
  try { return JSON.parse(sessionStorage.getItem(STORE)) || [WELCOME]; } catch { return [WELCOME]; }
};

function shortDate(iso) {
  return new Date(`${iso}T00:00:00`).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
}

function WeatherCard({ w }) {
  return (
    <div className="mt-3 rounded-2xl border border-[#6f4423]/10 bg-white p-4">
      <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#8d3528]"><CloudSun size={14} /> Weather · {w.place}</div>
      <div className="mt-3 grid gap-2 sm:grid-cols-3">
        {w.forecast.map((d) => (
          <div key={d.date} className="rounded-xl bg-[#f8f1e5] p-3 text-sm">
            <div className="flex items-center justify-between gap-1">
              <b>{d.day.slice(0, 3)}, {shortDate(d.date)}</b>
              {d.source !== 'forecast' && <span className="rounded bg-amber-100 px-1 text-[9px] font-bold text-amber-900">HIST AVG</span>}
            </div>
            <div className="mt-1 text-lg font-bold">{d.temp_min}–{d.temp_max}°C</div>
            <div className="text-xs capitalize text-[#806b58]">{d.condition}</div>
            <div className="mt-1 text-xs">Rain <b>{d.rain_probability}%</b></div>
            {d.windows?.morning != null && (
              <div className="mt-2 grid grid-cols-3 gap-1 text-center text-[9px] font-semibold">
                {['morning', 'afternoon', 'evening'].map((k) => (
                  <span key={k} className={`rounded px-0.5 py-0.5 ${d.windows[k] >= 60 ? 'bg-blue-200 text-blue-900' : 'bg-white text-[#705b49]'}`}>{k.slice(0, 3).toUpperCase()} {d.windows[k]}%</span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
      <div className="mt-2 text-[10px] text-[#806b58]">Live data · {w.provider}</div>
    </div>
  );
}

function CostCard({ c }) {
  const e = c.estimate;
  const labels = { transport: 'Transport', stay: 'Stay', food: 'Food', local: 'Tickets & local' };
  return (
    <div className="mt-3 rounded-2xl border border-[#6f4423]/10 bg-white p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#8d3528]"><Wallet size={14} /> Trip cost · per person</div>
        {e.within_budget !== null && (
          <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${e.within_budget ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'}`}>
            {e.within_budget ? `Within budget · ${inr(e.difference)} spare` : `Over budget by ${inr(Math.abs(e.difference))}`}
          </span>
        )}
      </div>
      <div className="mt-2 text-2xl font-bold">{inr(e.per_person_total)}</div>
      <div className="text-xs text-[#806b58]">
        {c.origin} → {c.destination} · {c.days} day(s) · {c.travelers} traveller(s)
        {c.route?.available && ` · ${c.route.distance_km} km, ~${c.route.duration_hours} hr by road`}
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
        {Object.entries(e.breakdown).map(([k, v]) => (
          <div key={k} className="rounded-xl bg-[#f8f1e5] p-2 text-center">
            <div className="text-[10px] font-bold text-[#8d3528]">{labels[k] || k}</div>
            <div className="text-sm font-bold">{inr(v)}</div>
          </div>
        ))}
      </div>
      {c.stay_options?.length > 0 && (
        <div className="mt-3 text-xs text-[#705b49]">
          <b>Stays:</b> {c.stay_options.map((s) => `${s.tier} ${inr(s.price_per_night)}/night`).join(' · ')}
        </div>
      )}
      <details className="mt-2 text-xs text-[#806b58]">
        <summary className="cursor-pointer font-semibold">How this is calculated</summary>
        <ul className="mt-1 list-disc pl-4">{e.assumptions.map((a) => <li key={a}>{a}</li>)}</ul>
        <p className="mt-1 italic">{c.note}</p>
      </details>
    </div>
  );
}

function AiMessage({ m, isLast, onSend, onAction, busy }) {
  return (
    <div className="max-w-[92%] rounded-2xl bg-[#f4e7d4] p-4">
      {m.label && <div className="mb-2 flex flex-wrap items-center gap-2"><LabelBadge label={m.label} />
        {m.tools?.map((t) => {
          const T = TOOL_LABELS[t];
          return T ? <span key={t} className="flex items-center gap-1 rounded-full bg-white/70 px-2 py-0.5 text-[10px] font-semibold text-[#6f2f24]"><T.icon size={11} />{T.text}</span> : null;
        })}
      </div>}
      <Markdown text={m.text} />
      {m.weather && <WeatherCard w={m.weather} />}
      {m.cost && <CostCard c={m.cost} />}
      {m.sources?.length > 0 && (
        <div className="mt-3 border-t border-[#6f4423]/10 pt-2 text-xs font-semibold opacity-80">Verified sources: {m.sources.join(' · ')}</div>
      )}
      {m.mode === 'local knowledge fallback' && <div className="mt-1 text-[10px] uppercase tracking-wider opacity-60">Offline mode · stored records only</div>}
      {isLast && m.actions?.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {m.actions.map((a) => (
            <button key={a.label} onClick={() => onAction(a)} className="flex items-center gap-1 rounded-full bg-[#6f2f24] px-3 py-1.5 text-xs font-bold text-white hover:bg-[#8d3528]">
              {a.label} <ArrowRight size={12} />
            </button>
          ))}
        </div>
      )}
      {isLast && m.suggestions?.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {m.suggestions.map((s) => (
            <button key={s} disabled={busy} onClick={() => onSend(s)} className="rounded-full border border-[#6f2f24]/25 bg-white px-3 py-1.5 text-xs font-semibold text-[#6f2f24] hover:bg-[#fbf6ed] disabled:opacity-50">{s}</button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Guide({ onAction }) {
  const [messages, setMessages] = useState(load);
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    try { sessionStorage.setItem(STORE, JSON.stringify(messages.slice(-30))); } catch { /* storage unavailable */ }
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, busy]);

  const send = async (raw) => {
    const q = (raw ?? text).trim();
    if (q.length < 2 || busy) return;
    setText('');
    const history = messages
      .filter((m) => m !== WELCOME && m.text && !m.error)
      .slice(-10)
      .map((m) => ({ role: m.role === 'user' ? 'user' : 'assistant', content: m.text }));
    setMessages((ms) => [...ms, { role: 'user', text: q }]);
    setBusy(true);
    try {
      const a = await chat(q, history);
      setMessages((ms) => [...ms, {
        role: 'ai', text: a.answer, sources: a.sources, mode: a.mode, label: a.label, tools: a.tools_used,
        weather: a.weather, cost: a.cost, suggestions: a.suggestions, actions: a.actions,
      }]);
    } catch (err) {
      const msg = err.status === 429 ? "You're asking quickly — give me a few seconds and try again."
        : err.status ? err.message : "I can't reach the server right now. Please check your connection and try again.";
      setMessages((ms) => [...ms, { role: 'ai', text: msg, error: true }]);
    } finally {
      setBusy(false);
    }
  };

  const reset = () => setMessages([WELCOME]);
  const started = messages.length > 1;

  return (
    <main className="mx-auto max-w-4xl px-5 py-12">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="text-xs font-bold uppercase tracking-[.25em] text-[#8d3528]">AI Heritage Guide</div>
          <h2 className="serif mt-2 text-4xl font-bold">Ask. Explore. Understand.</h2>
          <div className="mt-3 flex flex-wrap gap-2 text-[11px] font-semibold text-[#6f2f24]">
            {[[BookOpenCheck, 'Verified records'], [CloudSun, 'Live weather'], [Wallet, 'Trip cost estimates']].map(([Icon, label]) => (
              <span key={label} className="flex items-center gap-1 rounded-full bg-white px-2.5 py-1 shadow-sm"><Icon size={12} />{label}</span>
            ))}
          </div>
        </div>
        {started && <button onClick={reset} className="flex items-center gap-1 rounded-full border border-[#6f2f24]/20 bg-white px-4 py-2 text-xs font-bold text-[#6f2f24]"><RotateCcw size={13} /> New chat</button>}
      </div>

      <div className="mt-6 overflow-hidden rounded-3xl border border-[#6f4423]/10 bg-white shadow-sm">
        <div className="h-[560px] space-y-4 overflow-auto p-6">
          {messages.map((m, i) => (m.role === 'user' ? (
            <div key={i} className="ml-auto max-w-[85%] whitespace-pre-wrap rounded-2xl bg-[#6f2f24] p-4 leading-7 text-white">{m.text}</div>
          ) : (
            <AiMessage key={i} m={m} isLast={i === messages.length - 1} onSend={send} onAction={onAction} busy={busy} />
          )))}
          {!started && (
            <div className="grid gap-2 sm:grid-cols-2">
              {STARTERS.map((s) => (
                <button key={s} onClick={() => send(s)} className="flex items-start gap-2 rounded-2xl border border-[#6f4423]/10 bg-[#fbf6ed] p-3 text-left text-sm hover:border-[#8d3528]/30">
                  <Sparkles size={15} className="mt-0.5 shrink-0 text-[#8d3528]" />{s}
                </button>
              ))}
            </div>
          )}
          {busy && (
            <div className="flex w-fit items-center gap-2 rounded-2xl bg-[#f4e7d4] px-4 py-3 text-sm text-[#705b49]">
              <span className="flex gap-1">{[0, 150, 300].map((d) => <span key={d} className="h-2 w-2 animate-bounce rounded-full bg-[#8d3528]" style={{ animationDelay: `${d}ms` }} />)}</span>
              Checking records and live data…
            </div>
          )}
          <div ref={endRef} />
        </div>
        <form onSubmit={(e) => { e.preventDefault(); send(); }} className="flex gap-2 border-t p-4">
          <input value={text} onChange={(e) => setText(e.target.value)} maxLength={600} disabled={busy}
            placeholder="Ask about a monument, its weather, or a trip budget…" className="flex-1 rounded-xl bg-[#f8f1e5] px-4 py-3 outline-none disabled:opacity-60" />
          <button type="submit" disabled={busy || text.trim().length < 2} aria-label="Send" className="rounded-xl bg-[#6f2f24] p-3 text-white disabled:opacity-50"><Send size={18} /></button>
        </form>
      </div>
      <p className="mt-3 text-xs text-[#806b58]">Heritage facts come from DHAROHAR&apos;s verified records (ASI, UNESCO). Anything beyond them is labelled as general knowledge. Weather is live from Open-Meteo; cost estimates use live road distance and this app&apos;s demo hotel prices.</p>
    </main>
  );
}
