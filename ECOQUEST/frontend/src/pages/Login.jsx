import { ArrowRight, BadgeCheck, Eye, EyeOff, KeyRound, Leaf, Mail, Moon, ShieldCheck, Sun, Tag, UserRound } from "lucide-react";
import { useMemo, useState } from "react";
import { Link, Navigate, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { useTheme } from "../context/ThemeContext.jsx";

function PasswordInput({ id, label, value, onChange, autoComplete }) {
  const [visible, setVisible] = useState(false);
  return (
    <>
      {label && <label htmlFor={id}>{label}</label>}
      <div className="auth-input-wrap">
        <KeyRound size={17} aria-hidden="true" />
        <input id={id} type={visible ? "text" : "password"} value={value} onChange={onChange} autoComplete={autoComplete} placeholder="Enter your password" minLength={8} maxLength={128} required />
        <button className="password-visibility" type="button" onClick={() => setVisible((current) => !current)} aria-label={visible ? "Hide password" : "Show password"}>
          {visible ? <EyeOff size={17} /> : <Eye size={17} />}
        </button>
      </div>
    </>
  );
}

export default function Login({ mode = "signin" }) {
  const isRegister = mode === "register";
  const { login, logout, register } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const selectedRole = ["ORGANIZER", "ADMIN", "TEACHER"].includes(searchParams.get("role")) ? searchParams.get("role") : null;
  const roleTitle = selectedRole === "ORGANIZER" ? "Organizer" : selectedRole === "ADMIN" ? "College admin" : selectedRole === "TEACHER" ? "Teacher" : "Student";
  const roleRegisterPath = selectedRole === "ORGANIZER" ? "/register-role/ORGANIZER" : selectedRole === "ADMIN" ? "/register-role/COLLEGE_ADMIN" : selectedRole === "TEACHER" ? "/register-role/TEACHER" : "/register";
  const [form, setForm] = useState({ full_name: "", email: "", usn: "", department: "", semester: "", password: "", confirmPassword: "" });
  const [remember, setRemember] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (isRegister && selectedRole) return <Navigate to={"/login?role=" + selectedRole} replace />;

  const setField = (field) => (event) => setForm((current) => ({ ...current, [field]: event.target.value }));
  const passwordStrength = useMemo(() => {
    const value = form.password;
    return [value.length >= 8, /[A-Z]/.test(value) && /[a-z]/.test(value), /\d/.test(value), /[^A-Za-z0-9]/.test(value)].filter(Boolean).length;
  }, [form.password]);

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    if (isRegister && form.password !== form.confirmPassword) {
      setError("Your passwords do not match.");
      return;
    }
    setLoading(true);
    try {
      if (isRegister) {
        await register({
          full_name: form.full_name,
          email: form.email,
          usn: form.usn,
          department: form.department,
          semester: Number(form.semester),
          password: form.password,
        });
        navigate("/login", { replace: true, state: { registered: true } });
      } else {
        const loggedInUser = await login(form.email, form.password, remember);
        if (selectedRole && loggedInUser.role !== selectedRole) {
          logout();
          throw new Error("This account is not authorized for the " + roleTitle + " portal.");
        }
        navigate("/", { replace: true });
      }
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-page source-auth-page">
      <div className="auth-frame">
        <section className="auth-story source-auth-story">
          <div className="auth-brand-row">
            <Link to="/login" className="source-brand"><span className="source-brand-icon"><Leaf size={19} /></span><span>EcoQuest</span></Link>
            <span className="auth-tag"><i />{roleTitle} access</span>
          </div>
          <div className="source-story-copy">
            <span className="eyebrow light-eyebrow">MEANINGFUL ACTION STARTS HERE</span>
            <h1>Empowering student<br /><span>climate action.</span></h1>
            <p>Discover community-led opportunities, show up for your campus and neighborhood, and keep track of the difference you make.</p>
            <div className="auth-metrics">
              <article><span><Tag size={15} />Activity categories</span><strong>15</strong><small>Explore meaningful ways to contribute</small></article>
              <article><span><BadgeCheck size={15} />Eco Points</span><strong>Platform rewards</strong><small>Separate from academic activity points</small></article>
            </div>
            <div className="auth-security-note"><ShieldCheck size={18} /><span><strong>Secure student access</strong><small>JWT sign-in · Your profile stays yours</small></span></div>
          </div>
          <div className="auth-story-footer"><span><span className="live-dot" /> Your next step can start today.</span><button className="auth-theme-toggle" type="button" onClick={toggleTheme} aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}>{theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}{theme === "dark" ? "Light theme" : "Dark theme"}</button></div>
          <span className="source-glow source-glow-one" /><span className="source-glow source-glow-two" />
        </section>

        <section className="auth-form-side source-auth-form-side">
          <div className="auth-form-wrap source-auth-panel">
            <div className={selectedRole ? "auth-form-heading role-aware-heading role-" + selectedRole.toLowerCase() : "auth-form-heading"}>
              <div><span className="eyebrow">SECURE STUDENT ACCESS</span><h2>{isRegister ? "Create student account" : "Student portal sign in"}</h2><p>{isRegister ? "Use your college details to get started." : "Welcome back. Let’s keep your impact going."}</p></div>
              <button className="small-theme-toggle" type="button" onClick={toggleTheme} aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}>{theme === "dark" ? <Sun size={17} /> : <Moon size={17} />}</button>
            </div>
            <div className="auth-tabs" role="tablist" aria-label="Account access">
              <Link to={selectedRole ? "/login?role=" + selectedRole : "/login"} role="tab" aria-selected={!isRegister} className={!isRegister ? "active" : ""}>Sign in</Link>
              <Link to={roleRegisterPath} role="tab" aria-selected={isRegister} className={isRegister ? "active" : ""}>Register</Link>
            </div>
            {!isRegister && location.state?.registered && <div className="auth-success" role="status">Your student account is ready. Sign in with your college email and password.</div>}
            <form onSubmit={submit} className="source-auth-form">
              {isRegister && <>
                <label htmlFor="full_name">Student full name</label>
                <div className="auth-input-wrap"><UserRound size={17} /><input id="full_name" value={form.full_name} onChange={setField("full_name")} autoComplete="name" placeholder="Your full name" minLength={2} maxLength={160} required /></div>
                <label htmlFor="usn">University seat number (USN)</label>
                <div className="auth-input-wrap"><Tag size={17} /><input id="usn" value={form.usn} onChange={setField("usn")} placeholder="e.g. 1XX23CS001" pattern="[-A-Za-z0-9/_]+" maxLength={32} required /></div>
              </>}
              <label htmlFor="auth-email">Institutional college email</label>
              <div className="auth-input-wrap"><Mail size={17} /><input id="auth-email" type="email" value={form.email} onChange={setField("email")} autoComplete="email" placeholder="you@college.edu" required /></div>
              {isRegister && <>
                <div className="auth-field-grid">
                  <div><label htmlFor="department">Department</label><input id="department" className="auth-plain-input" value={form.department} onChange={setField("department")} placeholder="e.g. Computer Science" minLength={2} maxLength={120} required /></div>
                  <div><label htmlFor="semester">Semester</label><select id="semester" className="auth-plain-input" value={form.semester} onChange={setField("semester")} required><option value="">Select</option>{Array.from({ length: 12 }, (_, index) => <option value={index + 1} key={index + 1}>{index + 1}</option>)}</select></div>
                </div>
              </>}
              <div className="auth-password-label"><label htmlFor="auth-password">Account password</label>{!isRegister && <button className="auth-forgot" type="button" onClick={() => setError("Password recovery is not available yet. Please contact your EcoQuest administrator.")}>Forgot password?</button>}</div>
              <PasswordInput id="auth-password" label="" value={form.password} onChange={setField("password")} autoComplete={isRegister ? "new-password" : "current-password"} />
              {isRegister && <>
                <div className="password-meter" aria-label={`Password strength ${passwordStrength} of 4`}>{[1, 2, 3, 4].map((level) => <i className={passwordStrength >= level ? "filled" : ""} key={level} />)}<span>{["Use 8+ characters", "Getting there", "Good", "Strong"][Math.max(0, passwordStrength - 1)]}</span></div>
                <PasswordInput id="confirm-password" label="Confirm password" value={form.confirmPassword} onChange={setField("confirmPassword")} autoComplete="new-password" />
                <p className="auth-terms">Eco Points are EcoQuest platform rewards, not official VTU/AICTE academic activity points.</p>
              </>}
              {!isRegister && <label className="remember-option"><input type="checkbox" checked={remember} onChange={(event) => setRemember(event.target.checked)} /><span>Remember this device</span></label>}
              {error && <div className="form-error" role="alert">{error}</div>}
              <button className="button-primary auth-submit source-auth-submit" type="submit" disabled={loading}>{loading ? (isRegister ? "Creating account…" : "Signing in…") : <>{isRegister ? "Create student account" : "Sign in to EcoQuest"} <ArrowRight size={17} /></>}</button>
            </form>
            <div className="auth-protocol"><span />Authentication uses a signed JWT session<span /></div>
            <Link to="/welcome" className="auth-back-welcome">← Back to welcome</Link>
            <div className="auth-bottom-note"><ShieldCheck size={16} /><span>Account access is protected. We never expose your password.</span></div>
          </div>
        </section>
      </div>
    </main>
  );
}
