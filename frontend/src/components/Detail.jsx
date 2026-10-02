export default function Detail({ site, close, goBook }) {
  return (
    <div className="fixed inset-0 z-40 grid place-items-center bg-black/50 p-5 fade-in" onClick={close}>
      <div className="max-h-[90vh] max-w-2xl overflow-auto rounded-3xl bg-[#fffaf2] p-7" onClick={(e) => e.stopPropagation()}>
        {site.image && (
          <figure className="-mx-7 -mt-7 mb-5">
            <img src={site.image} alt={site.name} className="h-64 w-full rounded-t-3xl object-cover" />
            {site.image_credit && (
              <figcaption className="px-7 pt-2 text-[11px] text-[#806b58]">
                Photo: {site.image_credit.author} · {site.image_credit.license} ·{' '}
                <a href={site.image_credit.source} target="_blank" rel="noopener noreferrer" className="underline">Wikimedia Commons</a>
              </figcaption>
            )}
          </figure>
        )}
        <div className="flex justify-between gap-5">
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-[#8d3528]">{site.category}</div>
            <h3 className="serif text-3xl font-bold">{site.name}</h3>
            <p className="mt-1 text-sm text-[#806b58]">{site.state} · {site.period}</p>
          </div>
          <button onClick={close} className="text-xl text-[#705b49]">✕</button>
        </div>
        <p className="mt-5 leading-7 text-[#705b49]">{site.description}</p>
        <div className="mt-5 rounded-2xl bg-[#f4e7d4] p-5">
          <b>Significance</b>
          <p className="mt-2 text-sm leading-6">{site.significance}</p>
        </div>
        {site.best_time && <p className="mt-4 text-sm text-[#705b49]"><b>Best time to visit:</b> {site.best_time}</p>}
        <div className="mt-5 flex flex-wrap gap-2">
          {site.sources?.map((x) => (
            <span key={x} className="rounded-full border border-[#6f2f24]/10 bg-white px-3 py-2 text-xs font-semibold">
              ✓ VERIFIED SOURCE · {x}
            </span>
          ))}
        </div>
        {goBook && (
          <div className="mt-6 flex flex-wrap gap-2">
            <button onClick={() => goBook({ destination: site.name, tab: 'tickets' })} className="rounded-xl bg-[#6f2f24] px-5 py-2.5 text-sm font-bold text-white">Book tickets</button>
            <button onClick={() => goBook({ destination: site.name, tab: 'stays' })} className="rounded-xl border border-[#6f2f24]/25 px-5 py-2.5 text-sm font-bold text-[#6f2f24]">Find stays nearby</button>
          </div>
        )}
      </div>
    </div>
  );
}

export function LabelBadge({ label }) {
  if (label === 'verified') {
    return <span className="rounded-full bg-emerald-100 px-2 py-1 text-[10px] font-bold text-emerald-800">✓ VERIFIED SOURCE</span>;
  }
  return <span className="rounded-full bg-amber-100 px-2 py-1 text-[10px] font-bold text-amber-900">👤 COMMUNITY CONTRIBUTION</span>;
}
