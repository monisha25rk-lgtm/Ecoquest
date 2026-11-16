const labels = {
  REGISTERED: "Registered",
  COMPLETED: "Completed",
  CANCELLED: "Cancelled",
  PENDING: "Pending review",
  CHANGES_REQUESTED: "Changes requested",
  APPROVED: "Approved",
  REJECTED: "Not approved",
  DRAFT: "Draft",
};

export default function StatusBadge({ status }) {
  return <span className={`status-badge status-${String(status || "").toLowerCase()}`}>{labels[status] || status}</span>;
}
