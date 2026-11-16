import { ArrowLeft, ArrowRight, Leaf } from "lucide-react";
import { useState } from "react";
import { Link, Navigate, useNavigate, useParams } from "react-router-dom";
import { apiRequest } from "../services/api.js";

const types = ["College Club", "Department", "NGO", "Student Association", "External Organization", "Other"];

export default function RoleRegistration() {
  const { role } = useParams();
  const navigate = useNavigate();
  const isOrganizer = role === "ORGANIZER";
  const isTeacher = role === "TEACHER";
  const isAdmin = role === "COLLEGE_ADMIN";
  const [form, setForm] = useState({ role, full_name: "", email: "", password: "", organization_type: "", organization_name: "", organization_description: "", organization_official_email: "", affiliation: "", employee_id: "", department: "", designation: "", contact_number: "", college_name: "", college_code: "", college_official_email: "", college_address: "", college_city: "", college_state: "" });
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  if (!isOrganizer && !isTeacher && !isAdmin) return <Navigate to="/welcome" replace />;
  const update = (event) => setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
  const submit = async (event) => {
    event.preventDefault();
    setError("");
    setMessage("");
    const normalized = Object.fromEntries(Object.entries(form).map(([key, value]) => [key, typeof value === "string" ? value.trim() : value]));
    const payload = { role: normalized.role, full_name: normalized.full_name, email: normalized.email, password: normalized.password };
    if (isOrganizer) Object.assign(payload, {
      organization_name: normalized.organization_name,
      organization_type: normalized.organization_type,
      organization_description: normalized.organization_description,
      organization_official_email: normalized.organization_official_email,
      contact_number: normalized.contact_number,
      affiliation: normalized.affiliation,
    });
    if (isTeacher) Object.assign(payload, {
      employee_id: normalized.employee_id,
      department: normalized.department,
      designation: normalized.designation,
      contact_number: normalized.contact_number,
    });
    if (isAdmin) Object.assign(payload, {
      college_name: normalized.college_name,
      college_code: normalized.college_code,
      college_official_email: normalized.college_official_email,
      contact_number: normalized.contact_number,
      college_address: normalized.college_address,
      college_city: normalized.college_city,
      college_state: normalized.college_state,
    });
    const emails = [payload.email, payload.organization_official_email, payload.college_official_email].filter(Boolean);
    if (emails.some((email) => !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email))) {
      setError("Enter a valid email address, including @ and a domain such as nie.ac or college.edu.");
      return;
    }
    try {
      await apiRequest("/auth/register-role", { method: "POST", body: JSON.stringify(payload) });
      setMessage("Registration completed. You can now sign in.");
      setTimeout(() => navigate("/login?role=" + (isAdmin ? "ADMIN" : role)), 800);
    } catch (requestError) {
      setError(requestError.message);
    }
  };
  const title = isOrganizer ? "Register your organization" : isTeacher ? "Register your faculty profile" : "Register your college";
  const label = isOrganizer ? "Organizer" : isTeacher ? "Teacher" : "College admin";
  return (
    <main className="auth-page source-auth-page organizer-registration-page">
      <div className="auth-frame">
        <section className="auth-story source-auth-story">
          <div className="auth-brand-row"><Link to="/welcome" className="source-brand"><span className="source-brand-icon"><Leaf size={19} /></span><span>EcoQuest</span></Link><span className="auth-tag"><i />{label} access</span></div>
          <div className="source-story-copy"><span className="eyebrow light-eyebrow">{isOrganizer ? "BUILD COMMUNITY IMPACT" : isTeacher ? "GUIDE STUDENT IMPACT" : "ENABLE CAMPUS IMPACT"}</span><h1>{isOrganizer ? <>Bring your community<br /><span>together.</span></> : isTeacher ? <>Support student<br /><span>progress.</span></> : <>Lead your college<br /><span>forward.</span></>}</h1><p>{isOrganizer ? "Register your organization and submit meaningful activities for college approval." : isTeacher ? "Register your faculty profile so assigned student evidence can reach you." : "Register your college administration workspace for event and faculty management."}</p></div>
        </section>
        <section className="auth-form-side source-auth-form-side">
          <div className="source-auth-panel">
            <div className="auth-form-heading"><div><span className="eyebrow">{label.toUpperCase()} REGISTRATION</span><h2>{title}</h2><p>Use one EcoQuest account for access and role-specific details.</p></div></div>
            {error && <div className="inline-error">{error}</div>}
            {message && <div className="integration-note">{message}</div>}
            <form onSubmit={submit} className="staff-form organizer-form">
              <label className="staff-form-wide">Full name<input name="full_name" required onChange={update} /></label>
              <label>Email<input name="email" type="email" required onChange={update} /></label>
              <label>Password<input name="password" type="password" minLength="8" required onChange={update} /></label>
              {isOrganizer && <><label>Organization name<input name="organization_name" required onChange={update} /></label><label>Organization type<select name="organization_type" required value={form.organization_type} onChange={update}><option value="">Select type</option>{types.map((type) => <option key={type}>{type}</option>)}</select></label><label>Official email<input name="organization_official_email" type="email" required onChange={update} /></label><label>Contact number<input name="contact_number" required onChange={update} /></label><label>Affiliation (optional)<input name="affiliation" onChange={update} /></label><label className="staff-form-wide">Description<textarea name="organization_description" minLength="10" required rows="4" onChange={update} /></label></>}
              {isTeacher && <><label>Employee ID<input name="employee_id" required onChange={update} /></label><label>Department<input name="department" required onChange={update} /></label><label>Designation<input name="designation" required placeholder="Professor / Assistant Professor" onChange={update} /></label><label>Contact number (optional)<input name="contact_number" onChange={update} /></label></>}
              {isAdmin && <><label>College name<input name="college_name" required onChange={update} /></label><label>College code<input name="college_code" required onChange={update} /></label><label>Official email<input name="college_official_email" type="email" required onChange={update} /></label><label>Contact number<input name="contact_number" required onChange={update} /></label><label className="staff-form-wide">Address<textarea name="college_address" rows="2" onChange={update} /></label><label>City<input name="college_city" required onChange={update} /></label><label>State<input name="college_state" required onChange={update} /></label></>}
              <button className="button-primary staff-form-wide" type="submit">Create {isOrganizer ? "organizer" : isTeacher ? "teacher" : "college admin"} account <ArrowRight size={16} /></button>
            </form>
            <Link to="/welcome" className="organizer-back-link"><ArrowLeft size={14} /> Back to role selection</Link>
          </div>
        </section>
      </div>
    </main>
  );
}
