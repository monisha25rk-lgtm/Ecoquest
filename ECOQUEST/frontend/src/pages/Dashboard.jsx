import { ArrowRight, Award, CalendarCheck, CalendarDays, Leaf, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import EmptyState from "../components/EmptyState.jsx";
import EventCard from "../components/EventCard.jsx";
import LoadingSkeleton from "../components/LoadingSkeleton.jsx";
import StatCard from "../components/StatCard.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { eventService } from "../services/eventService.js";
import { gamificationService } from "../services/gamificationService.js";
import { pointsService } from "../services/pointsService.js";
import { registrationService } from "../services/registrationService.js";

function greeting() {
  const hour = new Date().getHours();
  return hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
}

export default function Dashboard() {
  const { user } = useAuth();
  const [registrations, setRegistrations] = useState([]);
  const [events, setEvents] = useState([]);
  const [pointsSummary, setPointsSummary] = useState(null);
  const [pointsError, setPointsError] = useState("");
  const [gamification, setGamification] = useState({ available: false, reason: "Loading Eco Points…" });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    const refreshPoints = () => pointsService.summary()
      .then((summary) => {
        if (active) {
          setPointsSummary(summary);
          setPointsError("");
        }
      })
      .catch(() => {
        if (active) setPointsError("Eco Points are temporarily unavailable.");
      });
    Promise.allSettled([
      registrationService.mine(),
      eventService.list({ upcoming: true, limit: 3 }),
      gamificationService.summary(),
      refreshPoints(),
    ])
      .then(([registered, discovered, summary]) => {
        if (!active) return;
        if (registered.status === "fulfilled") setRegistrations(registered.value);
        if (discovered.status === "fulfilled") setEvents(discovered.value.items);
        else setError(discovered.reason.message);
        if (summary.status === "fulfilled") setGamification(summary.value);
        else setGamification({ available: false, reason: "Badges and leaderboard are temporarily unavailable." });
      }).finally(() => active && setLoading(false));
    window.addEventListener("focus", refreshPoints);
    return () => {
      active = false;
      window.removeEventListener("focus", refreshPoints);
    };
  }, []);
  const completed = registrations.filter((item) => item.status === "COMPLETED").length;
  const registeredUpcoming = registrations.filter((item) => item.status === "REGISTERED" && new Date(item.event.end_date) >= new Date()).slice(0, 3);
  const points = pointsSummary?.total_points ?? null;
  const badges = gamification.available && Array.isArray(gamification.data.badges) ? gamification.data.badges.length : null;

  return (
    <div className="dashboard-page">
      <section className="welcome-panel"><div><span className="eyebrow light-eyebrow">YOUR IMPACT, IN MOTION</span><h1>{greeting()}, {user?.full_name?.split(" ")[0] || "there"}.</h1><p>Small actions. Meaningful impact. Ready for what’s next?</p><Link className="welcome-cta" to="/events">Find your next opportunity <ArrowRight size={16} /></Link></div><div className="welcome-art" aria-hidden="true"><div className="art-sun" /><div className="art-hill art-hill-back" /><div className="art-hill art-hill-front" /><span className="art-leaf leaf-a">✦</span><span className="art-leaf leaf-b">✳</span><span className="art-dot" /></div></section>
      {loading ? <LoadingSkeleton /> : <div className="stats-grid">
        <StatCard icon={Sparkles} label="Eco Points" value={points == null ? "—" : points} note={pointsError ? "Points are temporarily unavailable" : "Your recorded platform rewards"} tone="gold" />
        <StatCard icon={CalendarCheck} label="Registered events" value={registrations.filter((item) => item.status === "REGISTERED").length} note="Your active commitments" tone="green" />
        <StatCard icon={Leaf} label="Completed activities" value={completed} note="Every effort matters" tone="sage" />
        <StatCard icon={Award} label="Badges earned" value={badges == null ? "—" : badges} note={gamification.available ? "Keep showing up" : "Waiting for badges integration"} tone="gold" />
      </div>}
      {pointsError && <p className="integration-note">{pointsError}</p>}
      {!gamification.available && <p className="integration-note">{gamification.reason || "Badges and leaderboard features are not configured yet."} Eco Points are calculated from your recorded transactions.</p>}
      {error && <div className="inline-error" role="status">{error}</div>}
      <div className="dashboard-columns">
        <section className="content-panel"><div className="section-heading"><div><span className="eyebrow">YOUR CALENDAR</span><h2>Coming up</h2></div><Link to="/activities" className="text-link">All activities <ArrowRight size={15} /></Link></div>
          {registeredUpcoming.length ? <div className="upcoming-list">{registeredUpcoming.map((item) => <Link className="upcoming-row" to={`/events/${item.event_id}`} key={item.id}><span className="calendar-tile"><CalendarDays size={18} /><small>{item.event.start_date ? new Date(item.event.start_date).toLocaleDateString(undefined, { month: "short", day: "numeric" }) : "TBA"}</small></span><span className="upcoming-copy"><strong>{item.event.title}</strong><small>{item.event.venue || "Venue to be announced"}</small></span><ArrowRight size={16} /></Link>)}</div> : <EmptyState title="Your calendar is open" message="Register for an event and it’ll show up here." action={<Link className="text-link" to="/events">Explore events <ArrowRight size={15} /></Link>} />}
        </section>
        <aside className="impact-card"><span className="impact-icon"><Leaf size={20} /></span><span className="eyebrow">A NOTE ON POINTS</span><h3>Good work deserves recognition.</h3><p>Eco Points are EcoQuest rewards for participation. They are separate from official VTU/AICTE academic activity points.</p><Link to="/leaderboard" className="text-link">See the leaderboard <ArrowRight size={15} /></Link></aside>
      </div>
      <section className="content-panel points-history"><div className="section-heading"><div><span className="eyebrow">YOUR REWARDS</span><h2>Eco Points history</h2></div><strong>{points == null ? "—" : `${points} total`}</strong></div>
        {pointsSummary?.transactions?.length ? <div className="points-history-list">{pointsSummary.transactions.map((transaction) => <article className="points-history-row" key={transaction.transaction_id}><div><strong>{transaction.transaction_type === "REVERSAL" ? "Points reversed" : "Points awarded"}</strong><span>{transaction.event_title}</span><small>{new Date(transaction.created_at).toLocaleString()}</small></div><b className={transaction.points < 0 ? "points-negative" : "points-positive"}>{transaction.points > 0 ? "+" : ""}{transaction.points}</b></article>)}</div> : <p className="muted-copy">{pointsError ? "Transaction history is unavailable." : "Your approved Eco Points transactions will appear here."}</p>}
      </section>
      <section className="home-events"><div className="section-heading"><div><span className="eyebrow">ACTIVITY POINT OPPORTUNITIES</span><h2>Events to earn Eco Points</h2></div><Link to="/events" className="text-link">See all activities <ArrowRight size={15} /></Link></div>
        {loading ? <LoadingSkeleton /> : events.length ? <div className="event-grid">{events.map((event) => <EventCard key={event.id} event={event} />)}</div> : <EmptyState title="New opportunities are on their way" message="Published events will appear here as soon as they’re available." action={<Link className="button-secondary" to="/events">Browse events</Link>} />}
      </section>
    </div>
  );
}
