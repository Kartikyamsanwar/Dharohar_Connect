import { ArrowRight, Sparkles } from 'lucide-react';

const features = [
  ['🏛️', 'Heritage Explorer', 'Discover UNESCO sites and hidden stories across India'],
  ['🤖', 'AI Heritage Guide', 'Source-grounded answers powered by Groq LLM'],
  ['🧳', 'Smart Trip Planner', 'Multi-agent planning with live weather intelligence'],
  ['🌦️', 'Live Travel Intelligence', 'Real OpenWeather data shapes your itinerary'],
  ['👥', 'Group Travel', 'Find compatible travelers for heritage journeys'],
  ['🌍', 'Community', 'Stories, research and local knowledge sharing'],
  ['🛡️', 'Safety', 'Trip safety tools and prototype safety concepts'],
  ['📚', 'Cultural Knowledge', 'Architecture, arts, festivals and traditions'],
];

export default function Home({ setPage }) {
  return (
    <main>
      <section className="hero-pattern">
        <div className="mx-auto grid max-w-7xl items-center gap-10 px-5 py-20 md:grid-cols-2 md:py-28">
          <div className="fade-in">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-[#6f2f24]/15 bg-white/60 px-4 py-2 text-xs font-bold text-[#6f2f24]">
              <Sparkles size={14} /> Connecting People with India&apos;s Heritage
            </div>
            <h1 className="serif text-5xl font-bold leading-tight text-[#39251a] md:text-6xl">
              DHAROHAR <span className="text-[#8d3528]">CONNECT</span>
            </h1>
            <p className="mt-4 text-lg font-medium text-[#6f2f24]">Connecting People with India&apos;s Heritage</p>
            <p className="mt-4 max-w-xl text-lg leading-8 text-[#705b49]">
              Discover heritage, understand its stories, plan meaningful journeys and connect with people who share your interests.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <button onClick={() => setPage('EXPLORE')} className="flex items-center gap-2 rounded-full bg-[#6f2f24] px-6 py-3 font-bold text-white transition hover:scale-[1.02]">
                Explore Heritage <ArrowRight size={18} />
              </button>
              <button onClick={() => setPage('PLAN TRIP')} className="rounded-full border border-[#6f2f24]/20 bg-white/70 px-6 py-3 font-bold text-[#6f2f24] transition hover:bg-white">
                Plan My Journey
              </button>
              <button onClick={() => setPage('COMMUNITY')} className="rounded-full border border-[#6f2f24]/20 bg-white/70 px-6 py-3 font-bold text-[#6f2f24] transition hover:bg-white">
                Explore Community
              </button>
            </div>
          </div>
          <div className="relative fade-in">
            <div className="overflow-hidden rounded-[2rem] shadow-2xl">
              <img className="h-[420px] w-full object-cover" src="https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=1200&q=85" alt="Indian heritage" />
              <div className="absolute inset-x-5 bottom-5 rounded-2xl bg-black/45 p-5 text-white backdrop-blur">
                <div className="text-xs font-bold uppercase tracking-widest text-[#f7d58a]">Complete Ecosystem</div>
                <div className="serif text-2xl font-bold">From discovery to journey.</div>
              </div>
            </div>
          </div>
        </div>
      </section>
      <section className="mx-auto max-w-7xl px-5 py-16">
        <h2 className="serif mb-8 text-center text-3xl font-bold text-[#39251a]">Your heritage journey starts here</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {features.map(([icon, title, desc]) => (
            <div className="glass card-hover rounded-3xl p-6" key={title}>
              <div className="text-3xl">{icon}</div>
              <div className="mt-4 font-bold text-[#39251a]">{title}</div>
              <div className="mt-1 text-sm leading-6 text-[#806b58]">{desc}</div>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
