import { Award, Leaf, Trophy } from "lucide-react";
import { useEffect, useState } from "react";
import EmptyState from "../components/EmptyState.jsx";
import LoadingSkeleton from "../components/LoadingSkeleton.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { gamificationService } from "../services/gamificationService.js";

export default function Leaderboard() {
  const { user } = useAuth();
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => { gamificationService.leaderboard().then(setResult).catch((requestError) => setError(requestError.message)).finally(() => setLoading(false)); }, []);
  const data = result?.available ? result.data : null;
  const entries = Array.isArray(data) ? data : data?.items || data?.leaderboard || [];
  const podium = entries.slice(0, 3);
  return (
    <div className="leaderboard-page"><section className="page-intro"><div><span className="eyebrow">CELEBRATING EVERY STEP</span><h1>Community leaderboard</h1><p>Recognizing EcoQuest participation and platform rewards.</p></div><span className="leaderboard-trophy"><Trophy size={22} /></span></section>
      <div className="points-disclaimer-banner"><Leaf size={18} /><span><strong>Eco Points are platform rewards.</strong> They are not official VTU/AICTE academic activity points.</span></div>
      {error && <div className="inline-error" role="status">{error}</div>}
      {loading ? <LoadingSkeleton /> : !data ? <EmptyState title="The leaderboard is getting ready" message={result?.reason || "Leaderboard rankings will appear when Person 3's service is connected. Rankings are never calculated in this module."} /> : entries.length ? <><section className="podium">{podium.map((entry, index) => <article className={`podium-card podium-${index + 1} ${entry.id === user?.id ? "current-student" : ""}`} key={entry.id || entry.user_id || entry.rank}><span className="podium-medal"><Award size={20} /></span><span className="podium-rank">#{entry.rank || index + 1}</span><span className="podium-avatar">{entry.full_name?.slice(0, 1) || "S"}</span><strong>{entry.full_name || entry.name || "Student"}{entry.id === user?.id && <small>YOU</small>}</strong><span>{entry.department || "EcoQuest student"}</span><b>{entry.eco_points ?? entry.points ?? "—"} <small>pts</small></b></article>)}</section><section className="leaderboard-table"><div className="leaderboard-table-head"><span>RANK</span><span>STUDENT</span><span>DEPARTMENT</span><span>ECO POINTS</span></div>{entries.map((entry, index) => <div className={`leaderboard-row ${entry.id === user?.id ? "current-student" : ""}`} key={entry.id || entry.user_id || index}><b>#{entry.rank || index + 1}</b><span><i className="mini-avatar">{entry.full_name?.slice(0, 1) || "S"}</i>{entry.full_name || entry.name || "Student"}</span><span>{entry.department || "—"}</span><strong>{entry.eco_points ?? entry.points ?? "—"}</strong></div>)}</section></> : <EmptyState title="No rankings yet" message="The community standings will show here when they’re available." />}
    </div>
  );
}
