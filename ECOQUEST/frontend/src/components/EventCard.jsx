import { ArrowUpRight, CalendarDays, MapPin, Users } from "lucide-react";
import { Link } from "react-router-dom";

const formatDate = (value) => value ? new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" }).format(new Date(value)) : "Date to be announced";

export default function EventCard({ event }) {
  return (
    <article className="event-card">
      {event.poster_path ? (
        <img className="event-cover" src={event.poster_path} alt="" />
      ) : (
        <div className="event-cover event-cover-placeholder"><span>MAKE AN IMPACT</span></div>
      )}
      <div className="event-card-content">
        <div className="event-meta-top"><span className="category-pill">{event.category_name || `Category ${event.category_id}`}</span><span className="event-points">{event.approved_eco_points ?? "—"} pts</span></div>
        <h3>{event.title}</h3>
        <p className="organizer-name">{event.organization_name || "EcoQuest community"}</p>
        <div className="event-card-facts">
          <span><CalendarDays size={15} />{formatDate(event.start_date)}</span>
          <span><MapPin size={15} />{event.venue || "Venue to be announced"}</span>
          <span><Users size={15} />{event.available_seats == null ? "Capacity not listed" : `${event.available_seats} seats left`}</span>
        </div>
        <Link className="text-link" to={`/events/${event.id}`}>View details <ArrowUpRight size={16} /></Link>
      </div>
    </article>
  );
}
