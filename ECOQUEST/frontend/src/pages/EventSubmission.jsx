import { useEffect, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { apiRequest } from "../services/api.js";
import { person2Service } from "../services/person2Service.js";

export default function EventSubmission() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [categories, setCategories] = useState([]);
  const [form, setForm] = useState({ event_mode: "IN_PERSON", entry_fee: 0 });
  const [poster, setPoster] = useState(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    apiRequest("/categories").then(setCategories).catch((error) => setMessage(error.message));
  }, []);

  if (user?.role !== "ORGANIZER") return <Navigate to="/" replace />;

  const update = (event) => setForm((current) => ({ ...current, [event.target.name]: event.target.value }));

  const submit = async (event) => {
    event.preventDefault();
    try {
      const created = await person2Service.createEvent({
        ...form,
        category_id: Number(form.category_id),
        capacity: Number(form.capacity),
        entry_fee: Number(form.entry_fee || 0),
        proposed_eco_points: Number(form.proposed_eco_points),
      });
      if (poster) await person2Service.uploadPoster(created.id, poster);
      setMessage("Event proposal submitted for admin review.");
      setTimeout(() => navigate("/"), 700);
    } catch (error) {
      setMessage(error.message);
    }
  };

  return (
    <section className="content-panel form-panel">
      <span className="eyebrow">EVENT PROPOSAL</span>
      <h1>Submit an event</h1>
      <p className="muted-copy">Share the complete activity details students need before registering.</p>
      {message && <div className="integration-note">{message}</div>}
      <form onSubmit={submit} className="staff-form">
        <label className="staff-form-wide">Event title<input name="title" required onChange={update} /></label>
        <label>Venue / location<input name="venue" required placeholder="Where is it happening?" onChange={update} /></label>
        <label>Event mode<select name="event_mode" value={form.event_mode} onChange={update}><option value="IN_PERSON">In person</option><option value="ONLINE">Online</option><option value="HYBRID">Hybrid</option></select></label>
        <label>Entry fee (₹)<input name="entry_fee" type="number" min="0" value={form.entry_fee} onChange={update} /></label>
        <label>Start date and time<input name="start_date" type="datetime-local" required onChange={update} /></label>
        <label>End date and time<input name="end_date" type="datetime-local" required onChange={update} /></label>
        <label>Registration deadline<input name="registration_deadline" type="datetime-local" required onChange={update} /></label>
        <label>Participant capacity<input name="capacity" type="number" min="1" required onChange={update} /></label>
        <label>Eco Points students get<input name="proposed_eco_points" type="number" min="0" required onChange={update} /></label>
        <label>VTU activity point category<select name="category_id" required onChange={update}><option value="">Select a category</option>{categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</select></label>
        <label className="staff-form-wide">Facilities provided<textarea name="facilities" rows="2" placeholder="Water, meals, transport, certificates, materials..." onChange={update} /></label>
        {[["description", "Description"], ["eligibility_requirements", "Eligibility requirements"], ["participation_requirements", "Participation requirements"], ["evidence_requirements", "Evidence requirements"]].map(([name, label]) => <label key={name} className="staff-form-wide">{label}<textarea name={name} required rows="3" onChange={update} /></label>)}
        <label className="staff-form-wide">Event poster (image or PDF)<input type="file" accept="image/*,application/pdf" onChange={(event) => setPoster(event.target.files?.[0] || null)} /></label>
        <button className="button-primary" type="submit">Submit event for approval</button>
      </form>
    </section>
  );
}
