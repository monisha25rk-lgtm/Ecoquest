export default function LoadingSkeleton({ fullPage = false }) {
  return (
    <div className={fullPage ? "loading-page" : "loading-grid"} aria-label="Loading">
      {fullPage ? <span className="spinner" /> : Array.from({ length: 3 }, (_, i) => <div className="skeleton-card" key={i} />)}
    </div>
  );
}
