export default function StatCard({ icon: Icon, label, value, note, tone = "green" }) {
  return (
    <article className="stat-card">
      <span className={`stat-icon tone-${tone}`}><Icon size={19} /></span>
      <div><p>{label}</p><strong>{value ?? "—"}</strong>{note && <small>{note}</small>}</div>
    </article>
  );
}
