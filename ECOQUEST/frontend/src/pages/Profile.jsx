import { CalendarDays, Mail, MapPin, ShieldCheck, UserRound } from "lucide-react";
import { useEffect, useState } from "react";
import EmptyState from "../components/EmptyState.jsx";
import LoadingSkeleton from "../components/LoadingSkeleton.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { gamificationService } from "../services/gamificationService.js";
import { registrationService } from "../services/registrationService.js";

export default function Profile() {
  const { user } = useAuth();
  const [registrations, setRegistrations] = useState([]);
  const [rewards, setRewards] = useState({ available: false, reason: "Rewards API has not been configured by Person 3 yet." });
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    Promise.allSettled([registrationService.mine(), gamificationService.summary()])
      .then(([records, summary]) => {
        if (records.status === "fulfilled") setRegistrations(records.value);
        if (summary.status === "fulfilled") setRewards(summary.value);
      }).finally(() => setLoading(false));
  }, []);
  const points = rewards.available ? (rewards.data.eco_points ?? rewards.data.total_points) : "—";
  const history = registrations.slice(0, 5);
  return (
    <div className="profile-page"><section className="profile-cover"><div className="profile-cover-art"><div /><span>GROWING TOGETHER</span></div><div className="profile-heading"><span className="profile-avatar">{user?.full_name?.slice(0, 1).toUpperCase() || "S"}</span><div><span className="eyebrow">YOUR ECOQUEST PROFILE</span><h1>{user?.full_name}</h1><p><MapPin size={15} />{user?.department || "Student"} · Semester {user?.semester}</p></div></div></section>
      {loading ? <LoadingSkeleton /> : <div className="profile-stats"><div><strong>{points}</strong><span>Eco Points</span></div><div><strong>{registrations.length}</strong><span>Registered activities</span></div><div><strong>{registrations.filter((item) => item.status === "COMPLETED").length}</strong><span>Completed</span></div></div>}
      {!rewards.available && <p className="integration-note">{rewards.reason} Eco Points and badges are not estimated here.</p>}
      <div className="profile-columns"><section className="content-panel"><div className="section-heading"><div><span className="eyebrow">YOUR DETAILS</span><h2>Student information</h2></div><ShieldCheck size={20} className="profile-shield" /></div><div className="profile-details"><div><UserRound size={17} /><span><small>Full name</small><strong>{user?.full_name}</strong></span></div><div><Mail size={17} /><span><small>College email</small><strong>{user?.email}</strong></span></div><div><span className="usn-icon">ID</span><span><small>USN</small><strong>{user?.usn}</strong></span></div><div><MapPin size={17} /><span><small>Department</small><strong>{user?.department}</strong></span></div><div><CalendarDays size={17} /><span><small>Semester</small><strong>{user?.semester}</strong></span></div></div></section>
        <section className="content-panel"><div className="section-heading"><div><span className="eyebrow">YOUR JOURNEY</span><h2>Participation history</h2></div></div>{history.length ? <div className="profile-history">{history.map((item) => <div key={item.id}><span className="history-dot" /><span><strong>{item.event.title}</strong><small>{item.status} · {item.event.start_date ? new Date(item.event.start_date).toLocaleDateString() : "Date TBA"}</small></span></div>)}</div> : <EmptyState title="No activities yet" message="Your participation history will appear once you register for events." />}</section></div>
    </div>
  );
}
