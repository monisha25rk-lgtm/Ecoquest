import { ArrowRight, Building2, GraduationCap, Leaf, ShieldCheck, UsersRound } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useTheme } from "../context/ThemeContext.jsx";

const roles = [
  { key: "STUDENT", title: "Student", description: "Explore activities, register, upload evidence and track Eco Points.", icon: GraduationCap, login: "/login", register: "/register" },
  { key: "ORGANIZER", title: "Organizer", description: "Submit your organization and propose community events for approval.", icon: Building2, login: "/login?role=ORGANIZER", register: "/register-role/ORGANIZER" },
  { key: "ADMIN", title: "College admin", description: "Review organizations, approve events and assign faculty.", icon: ShieldCheck, login: "/login?role=ADMIN", register: "/register-role/COLLEGE_ADMIN" },
  { key: "TEACHER", title: "Teacher", description: "Evaluate assigned student participation and evidence submissions.", icon: UsersRound, login: "/login?role=TEACHER", register: "/register-role/TEACHER" },
];

export default function RoleSelect() {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  return (
    <main className="role-select-page">
      <section className="role-select-shell">
        <div className="role-select-topbar"><Link to="/welcome" className="source-brand"><span className="source-brand-icon"><Leaf size={19} /></span><span>EcoQuest</span></Link><button className="small-theme-toggle" type="button" onClick={toggleTheme} aria-label="Switch theme">{theme === "dark" ? "☼" : "☾"}</button></div>
        <div className="role-select-heading"><span className="eyebrow">WELCOME TO ECOQUEST</span><h1>Choose your portal</h1><p>Sign in or register through the workspace that matches your role in the EcoQuest community.</p></div>
        <div className="role-grid">
          {roles.map(({ key, title, description, icon: Icon, login, register }) => <article className="role-entry" key={key}><button className="role-card" type="button" onClick={() => navigate(login)}><span className="role-card-icon"><Icon size={21} /></span><span className="role-card-copy"><strong>{title}</strong><small>{description}</small></span><ArrowRight className="role-card-arrow" size={18} /></button><div className="role-entry-actions"><Link to={login}>Sign in</Link><Link to={register}>Register</Link></div></article>)}
        </div>
        <p className="role-select-note">Student registration uses the existing student authentication. Organizer, college admin and teacher registration use their role-specific forms and the same EcoQuest access system.</p>
      </section>
    </main>
  );
}
