import { Check, ClipboardList, X } from "lucide-react";
import { useEffect, useState } from "react";
import { person2Service } from "../services/person2Service.js";

const statusClass = (status) => "status-badge status-" + String(status).toLowerCase();

export default function PendingApprovals() {
  const [organizations, setOrganizations] = useState([]);
  const [events, setEvents] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const refresh = () => {
    setLoading(true);
    return Promise.all([person2Service.organizations(), person2Service.adminEvents()])
      .then(([organizationList, eventList]) => { setOrganizations(organizationList); setEvents(eventList); })
      .catch((requestError) => setError(requestError.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { refresh(); }, []);

  const decideOrganization = async (id, status) => {
    try { await person2Service.decideOrganization(id, { status }); await refresh(); } catch (requestError) { setError(requestError.message); }
  };
  const decideEvent = async (id, status) => {
    try { await person2Service.decideEvent(id, { status, review_note: status === "REJECTED" ? "Rejected by college administration." : null }); await refresh(); } catch (requestError) { setError(requestError.message); }
  };

  const pendingOrganizations = organizations.filter((item) => item.status === "PENDING");
  const pendingEvents = events.filter((item) => item.status === "PENDING");

  return <div className="admin-module-page"><section className="page-intro"><div><span className="eyebrow">COLLEGE ADMINISTRATION</span><h1>Pending approvals</h1><p>Review organization requests and event proposals before they reach students.</p></div><div className="intro-decoration"><ClipboardList size={22} /></div></section>{error && <div className="inline-error" role="alert">{error}</div>}{loading ? <div className="content-panel"><p className="muted-copy">Loading approvals…</p></div> : <><ApprovalPanel title="Organization requests" count={pendingOrganizations.length}>{pendingOrganizations.length === 0 ? <p className="muted-copy">No organization requests are waiting for approval.</p> : pendingOrganizations.map((organization) => <ApprovalRow key={organization.id} title={organization.name} meta={`${organization.organization_type} · ${organization.contact_email || "No email"}`} actionLabel="Approve" onApprove={() => decideOrganization(organization.id, "APPROVED")} onReject={() => decideOrganization(organization.id, "REJECTED")} />)}</ApprovalPanel><ApprovalPanel title="Event proposals" count={pendingEvents.length}>{pendingEvents.length === 0 ? <p className="muted-copy">No event proposals are waiting for approval.</p> : pendingEvents.map((event) => <ApprovalRow key={event.id} title={event.title} meta={`${event.organization_name || "Organization"} · ${event.category_name || "Category"} · ${event.start_date ? new Date(event.start_date).toLocaleString() : "Date TBA"} · ${event.proposed_eco_points ?? 0} proposed Eco Points`} actionLabel="Publish" onApprove={() => decideEvent(event.id, "PUBLISHED")} onReject={() => decideEvent(event.id, "REJECTED")} />)}</ApprovalPanel></>}</div>;
}

function ApprovalPanel({ title, count, children }) { return <section className="content-panel approvals-panel"><div className="section-heading"><div><span className="eyebrow">REVIEW QUEUE</span><h2>{title}</h2></div><span className="approval-count">{count} pending</span></div><div className="approval-list">{children}</div></section>; }
function ApprovalRow({ title, meta, actionLabel, onApprove, onReject }) { return <div className="approval-row"><div className="approval-copy"><h3>{title}</h3><p>{meta}</p></div><span className="status-badge status-pending">PENDING</span><div className="approval-actions"><button className="button-small" onClick={onApprove}><Check size={14} />{actionLabel}</button><button className="button-small danger" onClick={onReject}><X size={14} />Reject</button></div></div>; }
