import { ArrowLeft, CalendarDays, Clock3, Leaf, MapPin, Users } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import EmptyState from "../components/EmptyState.jsx";
import LoadingSkeleton from "../components/LoadingSkeleton.jsx";
import RegistrationModal from "../components/RegistrationModal.jsx";
import { eventService } from "../services/eventService.js";
import { registrationService } from "../services/registrationService.js";

const formatDate = (value) => value ? new Intl.DateTimeFormat(undefined, { dateStyle: "long", timeStyle: "short" }).format(new Date(value)) : "To be announced";

export default function EventDetails() {
  const { eventId } = useParams();
  const [event, setEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [registering, setRegistering] = useState(false);
  const [registered, setRegistered] = useState(false);
  const [registrationError, setRegistrationError] = useState("");

  useEffect(() => {
    let active = true;
    Promise.all([eventService.get(eventId), registrationService.mine()])
      .then(([details, registrations]) => {
        if (!active) return;
        setEvent(details);
        setRegistered(registrations.some((item) => item.event_id === Number(eventId) && item.status !== "CANCELLED"));
      }).catch((requestError) => active && setError(requestError.message))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [eventId]);

  const confirmRegistration = async () => {
    setRegistering(true);
    setRegistrationError("");
    try {
      await registrationService.register(event.id);
      setRegistered(true);
    } catch (requestError) {
      setRegistrationError(requestError.message);
    } finally {
      setRegistering(false);
    }
  };
  if (loading) return <LoadingSkeleton />;
  if (!event) return <div className="page-error"><EmptyState title="We couldn’t open this event" message={error || "This event may no longer be available."} action={<Link className="button-secondary" to="/events"><ArrowLeft size={16} /> Back to events</Link>} /></div>;
  const deadlinePassed = event.registration_deadline && new Date(event.registration_deadline) < new Date();
  const full = event.available_seats === 0;

  return (
    <div className="event-detail-page">
      <Link to="/events" className="back-link"><ArrowLeft size={17} /> All opportunities</Link>
      <section className="event-hero">{event.poster_path ? <img src={event.poster_path} alt="" /> : <div className="event-hero-art"><div className="hero-art-sun" /><div className="hero-art-hill" /><Leaf className="hero-art-leaf" size={76} /></div>}<div className="event-hero-shade" /><div className="event-hero-copy"><span className="category-pill">{event.category_name || `Category ${event.category_id}`}</span><h1>{event.title}</h1><p>{event.organization_name || "EcoQuest community"}</p></div></section>
      <div className="event-detail-layout"><article className="event-detail-main">
        <section className="detail-section"><span className="eyebrow">ABOUT THIS EVENT</span><h2>Be part of something meaningful.</h2><p className="event-description">{event.description || "Event details will be shared by the organizer."}</p></section>
        <section className="detail-section"><span className="eyebrow">THE DETAILS</span><div className="detail-facts"><div><CalendarDays size={18} /><span><small>Starts</small><strong>{formatDate(event.start_date)}</strong></span></div><div><CalendarDays size={18} /><span><small>Ends</small><strong>{formatDate(event.end_date)}</strong></span></div><div><MapPin size={18} /><span><small>Location</small><strong>{event.venue || "To be announced"}</strong></span></div><div><Clock3 size={18} /><span><small>Register by</small><strong>{formatDate(event.registration_deadline)}</strong></span></div><div><Leaf size={18} /><span><small>Entry fee</small><strong>{event.entry_fee ? `₹${event.entry_fee}` : "Free"}</strong></span></div></div>{event.facilities && <div className="requirement-block"><h3>Facilities</h3><p>{event.facilities}</p></div>}</section>
        {(event.eligibility_requirements || event.participation_requirements || event.evidence_requirements) && <section className="detail-section"><span className="eyebrow">WHAT TO KNOW</span>{event.eligibility_requirements && <div className="requirement-block"><h3>Who can join</h3><p>{event.eligibility_requirements}</p></div>}{event.participation_requirements && <div className="requirement-block"><h3>Participation</h3><p>{event.participation_requirements}</p></div>}{event.evidence_requirements && <div className="requirement-block"><h3>Evidence requirements</h3><p>{event.evidence_requirements}</p></div>}</section>}
      </article><aside className="registration-card"><span className="eyebrow">YOUR NEXT STEP</span><div className="detail-points"><span className="points-icon"><Leaf size={18} /></span><div><strong>{event.approved_eco_points ?? "—"}</strong><small>Eco Points</small></div><span className="points-disclaimer">Platform rewards only</span></div><div className="capacity-fact"><Users size={17} /><span>{event.available_seats == null ? "Capacity not listed" : full ? "Event is full" : `${event.available_seats} seats available`}</span></div>
        <button className="button-primary full-button" disabled={registered || deadlinePassed || full} onClick={() => setModalOpen(true)}>{registered ? "You’re registered" : deadlinePassed ? "Registration closed" : full ? "Event is full" : "Register now"}</button>
        {registered && <p className="registered-note">You’re all set. Find this event in <Link to="/activities">My Activities</Link>.</p>}
        <p className="registration-hint">Your registration is confirmed by EcoQuest’s backend. Availability is checked when you register.</p>
      </aside></div>
      <RegistrationModal open={modalOpen} event={event} loading={registering} error={registrationError} success={registered} onClose={() => setModalOpen(false)} onConfirm={confirmRegistration} />
    </div>
  );
}
