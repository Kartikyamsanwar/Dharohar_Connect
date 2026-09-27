import { useEffect, useState } from 'react';
import { ShieldCheck, Share2, Phone, CloudRain, CheckSquare, Users, Ban, Flag } from 'lucide-react';
import { getSafety } from '../lib/api';

export default function Safety() {
  const [data, setData] = useState(null);
  useEffect(() => { getSafety().then(setData).catch(() => {}); }, []);

  if (!data) {
    return <main className="mx-auto max-w-5xl px-5 py-12"><div className="text-center text-[#806b58]">Loading safety information...</div></main>;
  }

  return (
    <main className="mx-auto max-w-5xl px-5 py-12">
      <div className="rounded-[2rem] bg-[#211b17] p-8 text-white md:p-12">
        <ShieldCheck size={38} className="text-[#f7d58a]" />
        <div className="mt-5 text-xs font-bold uppercase tracking-[.25em] text-[#f7d58a]">Safety Center</div>
        <h2 className="serif mt-2 text-4xl font-bold">Travel with awareness</h2>
        <p className="mt-4 max-w-2xl leading-7 text-white/70">{data.disclaimer}</p>
      </div>

      <section className="mt-8 rounded-3xl bg-white p-8 shadow-sm">
        <h3 className="flex items-center gap-2 text-xl font-bold"><Share2 size={20} className="text-[#8d3528]" /> Trip Safety</h3>
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <Card icon={<Share2 size={18} />} title="Share trip details" desc={data.trip_safety.share_trip} />
          <Card icon={<Phone size={18} />} title="Trusted contact" desc={data.trip_safety.trusted_contact} />
          <Card icon={<Phone size={18} />} title="Emergency information" desc={data.trip_safety.emergency} />
          <Card icon={<CloudRain size={18} />} title="Weather precautions" desc={data.trip_safety.weather_precautions} />
        </div>
        <div className="mt-5 rounded-2xl bg-[#f4e7d4] p-5">
          <div className="flex items-center gap-2 font-bold"><CheckSquare size={18} /> Travel checklist</div>
          <ul className="mt-3 space-y-1 text-sm">{data.trip_safety.checklist.map((x) => <li key={x}>✓ {x}</li>)}</ul>
        </div>
      </section>

      <section className="mt-8 rounded-3xl bg-white p-8 shadow-sm">
        <h3 className="flex items-center gap-2 text-xl font-bold"><Users size={20} className="text-[#8d3528]" /> Group Safety</h3>
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <Card icon={<Flag size={18} />} title="Report user" desc={data.group_safety.report_user} />
          <Card icon={<Ban size={18} />} title="Block user" desc={data.group_safety.block_user} />
        </div>
        <div className="mt-5 rounded-2xl bg-[#eef1e7] p-5">
          <b>Group guidelines</b>
          <ul className="mt-2 space-y-1 text-sm">{data.group_safety.guidelines.map((x) => <li key={x}>• {x}</li>)}</ul>
          <p className="mt-3 text-xs italic text-[#705b49]">{data.group_safety.verification_status}</p>
        </div>
      </section>

      <section className="mt-8 rounded-3xl bg-[#f4e7d4] p-8">
        <h3 className="text-xl font-bold">Women Safety</h3>
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <Card title="Prefer verified groups" desc={data.women_safety.prefer_verified_groups} />
          <Card title="Trusted contact" desc={data.women_safety.trusted_contact} />
          <Card title="Share trip" desc={data.women_safety.share_trip} />
        </div>
        <div className="mt-5 rounded-2xl bg-white p-5">
          <b>Safety checklist</b>
          <ul className="mt-2 space-y-1 text-sm">{data.women_safety.checklist.map((x) => <li key={x}>✓ {x}</li>)}</ul>
        </div>
      </section>

      <p className="mt-8 rounded-2xl border border-amber-300 bg-amber-50 p-4 text-center text-sm text-amber-900">
        {data.disclaimer}
      </p>
    </main>
  );
}

function Card({ icon, title, desc }) {
  return (
    <div className="rounded-2xl border border-[#6f4423]/10 bg-[#fbf6ed] p-5">
      {icon && <div className="text-[#8d3528]">{icon}</div>}
      <div className="mt-2 font-bold">{title}</div>
      <div className="mt-1 text-sm leading-6 text-[#705b49]">{desc}</div>
    </div>
  );
}
