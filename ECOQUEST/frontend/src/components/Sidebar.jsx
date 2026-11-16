import { Activity, Bell, Compass, LayoutDashboard, Leaf, Trophy, UserRound } from "lucide-react";
import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/events", label: "Explore events", icon: Compass },
  { to: "/activities", label: "My activities", icon: Activity },
  { to: "/notifications", label: "Notifications", icon: Bell, notification: true },
  { to: "/leaderboard", label: "Leaderboard", icon: Trophy },
  { to: "/profile", label: "My profile", icon: UserRound },
];

export default function Sidebar({ unreadCount }) {
  return (
    <aside className="sidebar">
      <NavLink to="/" className="brand"><span className="brand-mark"><Leaf size={21} /></span><span>ecoquest<small>STUDENT IMPACT</small></span></NavLink>
      <span className="nav-caption">YOUR SPACE</span>
      <nav className="side-nav">
        {links.map(({ to, label, icon: Icon, end, notification }) => <NavLink key={to} to={to} end={end} className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}><Icon size={18} /><span>{label}</span>{notification && unreadCount > 0 && <i className="nav-count">{unreadCount > 9 ? "9+" : unreadCount}</i>}</NavLink>)}
      </nav>
      <div className="sidebar-footer"><div className="sidebar-leaf"><Leaf size={17} /></div><p>Small actions.<br /><strong>Meaningful impact.</strong></p><span>Every step counts.</span></div>
    </aside>
  );
}
