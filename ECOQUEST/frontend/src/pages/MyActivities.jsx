import { CalendarDays, FileUp, MapPin } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import EmptyState from "../components/EmptyState.jsx";
import LoadingSkeleton from "../components/LoadingSkeleton.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import { person2Service } from "../services/person2Service.js";
import { registrationService } from "../services/registrationService.js";

const tabs = ["All", "Upcoming", "Ongoing", "Completed"];

function eventBucket(registration) {
  const now = new Date();
  const start = registration.event.start_date ? new Date(registration.event.start_date) : null;
  const end = registration.event.end_date ? new Date(registration.event.end_date) : null;
  if (registration.status === "COMPLETED" || (end && end < now)) return "Completed";
  if (start && start <= now && (!end || end >= now)) return "Ongoing";
  return "Upcoming";
}

function submissionState(status) {
  const states = {
    PENDING: { label: "Submitted · Waiting for review", tone: "pending" },
    APPROVED: { label: "Approved", tone: "approved" },
    REJECTED: { label: "Rejected", tone: "rejected" },
    CHANGES_REQUESTED: { label: "Changes requested", tone: "changes" },
    DRAFT: { label: "Draft · Not submitted", tone: "draft" },
  };
  return states[status] || { label: "Not submitted", tone: "draft" };
}

function EvidenceState({ submission, review }) {
  if (!submission) return null;
  const state = submissionState(submission.status);
  return <div className={`evidence-state evidence-state-${state.tone}`} role="status">
    <strong>{state.label}</strong>
    {review?.grade != null && <span>Grade: {review.grade}/100</span>}
    {review?.note && <p>{review.note}</p>}
  </div>;
}

export default function MyActivities() {
  const [registrations, setRegistrations] = useState([]);
  const [activeTab, setActiveTab] = useState("All");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [evidenceFor, setEvidenceFor] = useState(null);
  const [submission, setSubmission] = useState({});
  const [evidenceError, setEvidenceError] = useState("");
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    registrationService.mine()
      .then(setRegistrations)
      .catch((requestError) => setError(requestError.message))
      .finally(() => setLoading(false));
  }, []);

  const visible = useMemo(
    () => activeTab === "All" ? registrations : registrations.filter((registration) => eventBucket(registration) === activeTab),
    [registrations, activeTab],
  );

  const openEvidence = async (registrationId) => {
    setEvidenceFor(registrationId);
    setEvidenceError("");
    try {
      const result = await person2Service.submission(registrationId);
      setSubmission((current) => ({ ...current, [registrationId]: result }));
    } catch (requestError) {
      if (requestError.status !== 404) setEvidenceError(requestError.message);
    }
  };

  const submitEvidence = async (event, registrationId) => {
    event.preventDefault();
    setUploading(true);
    setEvidenceError("");
    try {
      const result = await person2Service.submitEvidence(registrationId, new FormData(event.currentTarget));
      setSubmission((current) => ({ ...current, [registrationId]: result }));
    } catch (requestError) {
      setEvidenceError(requestError.message);
    } finally {
      setUploading(false);
    }
  };

  return <div className="activities-page">
    <section className="page-intro"><div><span className="eyebrow">YOUR JOURNEY</span><h1>My activities</h1><p>See every event you registered for and submit your participation evidence.</p></div></section>
    <div className="tabs-row" role="tablist">{tabs.map((tab) => <button key={tab} role="tab" aria-selected={activeTab === tab} className={activeTab === tab ? "tab-button active" : "tab-button"} onClick={() => setActiveTab(tab)}>{tab}<span>{tab === "All" ? registrations.length : registrations.filter((item) => eventBucket(item) === tab).length}</span></button>)}</div>
    {error && <div className="inline-error" role="status">{error}</div>}
    {loading ? <LoadingSkeleton /> : visible.length ? <div className="activity-list">{visible.map((registration) => {
      const current = submission[registration.id];
      const latestReview = current?.reviews?.at(-1);
      const canEdit = !current || current.status === "DRAFT" || current.status === "CHANGES_REQUESTED";
      return <article className="activity-entry" key={registration.id}>
        <div className="activity-row"><div className="activity-date"><CalendarDays size={18} /><span>{registration.event.start_date ? new Date(registration.event.start_date).toLocaleDateString(undefined, { month: "short", day: "numeric" }) : "TBA"}</span></div><div className="activity-copy"><Link to={`/events/${registration.event_id}`}><h3>{registration.event.title}</h3></Link><p>{registration.event.organization_name || "EcoQuest community"} · {registration.event.category_name || "Community event"}</p><small><MapPin size={14} />{registration.event.venue || "Venue to be announced"}</small></div><div className="activity-status"><StatusBadge status={registration.status} /><span>{eventBucket(registration)}</span></div><button className="button-small" onClick={() => openEvidence(registration.id)}><FileUp size={14} /> Evidence</button></div>
        {evidenceFor === registration.id && <div className="evidence-panel">
          <EvidenceState submission={current} review={latestReview} />
          {canEdit && <form onSubmit={(event) => submitEvidence(event, registration.id)} className="evidence-form"><label>Participation dates<input name="participation_dates" placeholder="e.g. 12–14 March 2026" required /></label><label>Note for faculty<textarea name="student_note" rows="2" placeholder="Describe your contribution" /></label><label>Photos, report or certificate<input name="files" type="file" multiple accept="image/*,.pdf,.doc,.docx" /></label><button className="button-primary" disabled={uploading}>{uploading ? "Submitting…" : current?.status === "CHANGES_REQUESTED" ? "Resubmit evidence" : "Submit evidence"}</button></form>}
          {evidenceError && <div className="inline-error">{evidenceError}</div>}
        </div>}
      </article>;
    })}</div> : <EmptyState title={activeTab === "All" ? "Your story starts with a first step" : `No ${activeTab.toLowerCase()} activities`} message={activeTab === "All" ? "Explore opportunities and register for an event that matters to you." : "When you have an activity in this stage, it’ll appear here."} action={<Link to="/events" className="button-primary">Explore events</Link>} />}
  </div>;
}
