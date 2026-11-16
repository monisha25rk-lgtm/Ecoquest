import { ChevronDown, LogOut, UserRound } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import NotificationBell from "./NotificationBell.jsx";
import ThemeToggle from "./ThemeToggle.jsx";

export default function Topbar({ title, unreadCount }) {
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  return (
    <header className="topbar"><div className="mobile-brand"><span className="brand-mark"><span>e</span></span>ecoquest</div><div className="topbar-title">{title}</div><div className="topbar-actions"><ThemeToggle /><NotificationBell count={unreadCount} /><button className="profile-menu-trigger" onClick={() => setMenuOpen((open) => !open)} aria-expanded={menuOpen}><span className="avatar">{user?.full_name?.slice(0, 1).toUpperCase() || "S"}</span><span className="topbar-user-name">{user?.full_name?.split(" ")[0] || "Student"}</span><ChevronDown size={15} /></button>{menuOpen && <div className="profile-menu"><Link to="/profile" onClick={() => setMenuOpen(false)}><UserRound size={16} /> My profile</Link><button onClick={logout}><LogOut size={16} /> Sign out</button></div>}</div></header>
  );
}
