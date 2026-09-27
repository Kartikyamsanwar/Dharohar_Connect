import { useState } from 'react';
import { Send } from 'lucide-react';
import { chat } from '../lib/api';
import { LabelBadge } from '../components/Detail';

export default function Guide() {
  const [messages, setMessages] = useState([
    { role: 'ai', text: 'Namaste! I am your DHAROHAR Heritage Guide. Ask me about any major Indian heritage site — Hampi, Taj Mahal, Qutub Minar, Golden Temple, Ajanta, Ellora, Konark and more.' },
  ]);
  const [text, setText] = useState('');

  const send = async () => {
    if (!text.trim()) return;
    const q = text;
    setText('');
    setMessages((m) => [...m, { role: 'user', text: q }]);
    try {
      const a = await chat(q);
      setMessages((m) => [...m, { role: 'ai', text: a.answer, sources: a.sources, mode: a.mode, label: a.label }]);
    } catch {
      setMessages((m) => [...m, { role: 'ai', text: 'Backend is not reachable. Start FastAPI on port 8000.' }]);
    }
  };

  return (
    <main className="mx-auto max-w-4xl px-5 py-12">
      <div className="text-xs font-bold uppercase tracking-[.25em] text-[#8d3528]">AI Heritage Guide</div>
      <h2 className="serif mt-2 text-4xl font-bold">Ask. Explore. Understand.</h2>
      <p className="mt-2 text-sm text-[#806b58]">Source-grounded responses via Heritage Agent → local knowledge → Groq LLM</p>
      <div className="mt-8 overflow-hidden rounded-3xl border border-[#6f4423]/10 bg-white shadow-sm">
        <div className="h-[470px] space-y-4 overflow-auto p-6">
          {messages.map((m, i) => (
            <div key={i} className={`max-w-[90%] rounded-2xl p-4 ${m.role === 'user' ? 'ml-auto bg-[#6f2f24] text-white' : 'bg-[#f4e7d4]'}`}>
              {m.label && m.role === 'ai' && <div className="mb-2"><LabelBadge label={m.label} /></div>}
              <p className="whitespace-pre-wrap leading-7">{m.text}</p>
              {m.sources && (
                <div className="mt-3 border-t border-[#6f4423]/10 pt-2 text-xs font-semibold opacity-80">
                  Sources: {m.sources.join(' · ')}
                </div>
              )}
              {m.mode && m.role === 'ai' && <div className="mt-1 text-[10px] uppercase tracking-wider opacity-60">{m.mode}</div>}
            </div>
          ))}
        </div>
        <div className="flex gap-2 border-t p-4">
          <input value={text} onChange={(e) => setText(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && send()} placeholder="Why is Hampi important?" className="flex-1 rounded-xl bg-[#f8f1e5] px-4 outline-none" />
          <button onClick={send} className="rounded-xl bg-[#6f2f24] p-3 text-white"><Send size={18} /></button>
        </div>
      </div>
    </main>
  );
}
