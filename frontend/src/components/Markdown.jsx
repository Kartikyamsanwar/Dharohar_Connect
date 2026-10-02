// Minimal Markdown for chat replies: headings, bullets, numbered lists, rules, **bold**, _italic_, links.
// Builds React elements only (no innerHTML), so model output cannot inject markup or scripts.

const INLINE = /\*\*(.+?)\*\*|\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)|(?<![\w*])[_*](?![\s*_])(.+?)(?<![\s*_])[_*](?![\w*])/g;

function inline(text, keyBase) {
  const out = [];
  let last = 0;
  let i = 0;
  for (const m of text.matchAll(INLINE)) {
    if (m.index > last) out.push(text.slice(last, m.index));
    const key = `${keyBase}-${i++}`;
    if (m[1] !== undefined) out.push(<strong key={key}>{m[1]}</strong>);
    else if (m[2] !== undefined) out.push(<a key={key} href={m[3]} target="_blank" rel="noopener noreferrer" className="underline">{m[2]}</a>);
    else out.push(<em key={key}>{m[4]}</em>);
    last = m.index + m[0].length;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}

export default function Markdown({ text }) {
  const lines = (text || '').replace(/\r/g, '').split('\n');
  const blocks = [];
  let para = [];
  let list = null;

  const flushPara = () => {
    if (para.length) blocks.push({ type: 'p', lines: para });
    para = [];
  };
  const flushList = () => {
    if (list) blocks.push(list);
    list = null;
  };

  for (const raw of lines) {
    const line = raw.replace(/\s+$/, '');
    const bullet = line.match(/^(\s*)([-*•]|\d+[.)])\s+(.*)$/);
    const heading = line.match(/^\s*(#{1,4})\s+(.*)$/);
    if (!line.trim()) { flushPara(); flushList(); continue; }
    if (/^\s*(-{3,}|\*{3,}|_{3,})\s*$/.test(line)) { flushPara(); flushList(); blocks.push({ type: 'hr' }); continue; }
    if (heading) { flushPara(); flushList(); blocks.push({ type: 'h', level: heading[1].length, text: heading[2] }); continue; }
    if (bullet) {
      flushPara();
      const ordered = /\d/.test(bullet[2]);
      if (!list || list.ordered !== ordered) { flushList(); list = { type: 'list', ordered, items: [] }; }
      list.items.push({ text: bullet[3], indent: bullet[1].length >= 2 });
      continue;
    }
    flushList();
    para.push(line.trim());
  }
  flushPara();
  flushList();

  return (
    <div className="space-y-2.5 leading-7">
      {blocks.map((b, bi) => {
        if (b.type === 'hr') return <hr key={bi} className="border-[#6f4423]/15" />;
        if (b.type === 'h') {
          return <div key={bi} className={`font-bold text-[#6f2f24] ${b.level <= 2 ? 'text-lg' : 'text-base'} pt-1`}>{inline(b.text, bi)}</div>;
        }
        if (b.type === 'list') {
          const Tag = b.ordered ? 'ol' : 'ul';
          return (
            <Tag key={bi} className={`${b.ordered ? 'list-decimal' : 'list-disc'} space-y-1 pl-5 marker:text-[#8d3528]`}>
              {b.items.map((it, ii) => <li key={ii} className={it.indent ? 'ml-4' : ''}>{inline(it.text, `${bi}-${ii}`)}</li>)}
            </Tag>
          );
        }
        return (
          <p key={bi}>
            {b.lines.map((l, li) => (
              <span key={li}>{li > 0 && <br />}{inline(l, `${bi}-${li}`)}</span>
            ))}
          </p>
        );
      })}
    </div>
  );
}
