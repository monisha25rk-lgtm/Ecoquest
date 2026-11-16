import { Search, SlidersHorizontal, X } from "lucide-react";
import { useEffect, useState } from "react";
import EmptyState from "../components/EmptyState.jsx";
import EventCard from "../components/EventCard.jsx";
import LoadingSkeleton from "../components/LoadingSkeleton.jsx";
import { eventService } from "../services/eventService.js";
import { apiRequest } from "../services/api.js";

export default function ExploreEvents() {
  const [events, setEvents] = useState([]);
  const [categories, setCategories] = useState([]);
  const [search, setSearch] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [eventDate, setEventDate] = useState("");
  const [upcoming, setUpcoming] = useState(false);
  const [registrationOpen, setRegistrationOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    apiRequest("/categories").then(setCategories).catch((requestError) => setError(requestError.message));
  }, []);
  useEffect(() => {
    let active = true;
    setLoading(true);
    const timer = window.setTimeout(() => {
      eventService.list({ search, category_id: categoryId, date: eventDate, upcoming, registration_open: registrationOpen, limit: 30 })
        .then((response) => active && setEvents(response.items))
        .catch((requestError) => active && setError(requestError.message))
        .finally(() => active && setLoading(false));
    }, 250);
    return () => { active = false; window.clearTimeout(timer); };
  }, [search, categoryId, eventDate, upcoming, registrationOpen]);
  const hasFilters = search || categoryId || eventDate || upcoming || registrationOpen;
  return (
    <div className="explore-page">
      <section className="page-intro"><div><span className="eyebrow">EXPLORE & GET INVOLVED</span><h1>Discover opportunities</h1><p>Find meaningful experiences. Turn participation into impact.</p></div><div className="intro-decoration"><SlidersHorizontal size={22} /></div></section>
      <section className="filter-panel">
        <div className="search-field"><Search size={19} /><input aria-label="Search events" placeholder="Search events or organizers…" value={search} onChange={(e) => setSearch(e.target.value)} /><kbd>⌘ K</kbd></div>
        <div className="filter-row">
          <select aria-label="Filter by category" value={categoryId} onChange={(e) => setCategoryId(e.target.value)}><option value="">All categories</option>{categories.map((category) => <option value={category.id} key={category.id}>{category.name}</option>)}</select>
          <label className="date-filter">On date <input aria-label="Filter by date" type="date" value={eventDate} onChange={(e) => setEventDate(e.target.value)} /></label>
          <label className="check-filter"><input type="checkbox" checked={upcoming} onChange={(e) => setUpcoming(e.target.checked)} />Upcoming</label>
          <label className="check-filter"><input type="checkbox" checked={registrationOpen} onChange={(e) => setRegistrationOpen(e.target.checked)} />Registration open</label>
          {hasFilters && <button className="clear-filters" onClick={() => { setSearch(""); setCategoryId(""); setEventDate(""); setUpcoming(false); setRegistrationOpen(false); }}><X size={15} /> Clear</button>}
        </div>
      </section>
      {error && <div className="inline-error" role="status">{error}</div>}
      <div className="results-caption"><span>{loading ? "Finding opportunities…" : `${events.length} ${events.length === 1 ? "opportunity" : "opportunities"}`}</span><span>Only published events are shown</span></div>
      {loading ? <LoadingSkeleton /> : events.length ? <div className="event-grid">{events.map((event) => <EventCard event={event} key={event.id} />)}</div> : <EmptyState title={hasFilters ? "No matching events" : "The next opportunity is on its way"} message={hasFilters ? "Try changing your search or filters to find another event." : "There are no published events to explore right now. Check back soon."} action={hasFilters && <button className="button-secondary" onClick={() => { setSearch(""); setCategoryId(""); setEventDate(""); }}>Clear filters</button>} />}
    </div>
  );
}
