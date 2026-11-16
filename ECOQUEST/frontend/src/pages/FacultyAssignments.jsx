import { ArrowRight, UsersRound } from "lucide-react";
import { useEffect, useState } from "react";
import { person2Service } from "../services/person2Service.js";

const statusClass = (status) => "status-badge status-" + String(status).toLowerCase();

export default function FacultyAssignments() {
  const [teachers, setTeachers] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [form, setForm] = useState({ teacher_id: "", start_usn: "", end_usn: "" });
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const refresh = () => {
    setLoading(true);
    return Promise.all([person2Service.teachers(), person2Service.facultyAssignments()])
      .then(([teacherList, assignmentList]) => {
        setTeachers(teacherList);
        setAssignments(assignmentList);
      })
      .catch((requestError) => setError(requestError.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { refresh(); }, []);

  const assignRange = async (event) => {
    event.preventDefault();
    setError("");
    setMessage("");
    setSaving(true);
    try {
      const result = await person2Service.assignFacultyRange({
        teacher_id: Number(form.teacher_id),
        start_usn: form.start_usn.trim().toUpperCase(),
        end_usn: form.end_usn.trim().toUpperCase(),
      });
      const missing = result.missing_usns?.length ? ` Missing: ${result.missing_usns.join(", ")}.` : "";
      setMessage(`${result.assigned_count} student assignment${result.assigned_count === 1 ? "" : "s"} saved.${missing}`);
      setForm({ teacher_id: "", start_usn: "", end_usn: "" });
      await refresh();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="admin-module-page">
      <section className="page-intro">
        <div>
          <span className="eyebrow">FACULTY MANAGEMENT</span>
          <h1>Assign faculty reviewers</h1>
          <p>Assign one teacher to a continuous range of student USNs.</p>
        </div>
        <div className="intro-decoration"><UsersRound size={22} /></div>
      </section>

      <section className="content-panel assignment-panel">
        <div className="section-heading">
          <div>
            <span className="eyebrow">USN RANGE ASSIGNMENT</span>
            <h2>Assign students from one USN to another</h2>
          </div>
        </div>
        <p className="muted-copy">Example: assign every existing student from <strong>4NI24CS128</strong> through <strong>4NI24CS132</strong>. The backend matches actual student records only.</p>
        {error && <div className="inline-error" role="alert">{error}</div>}
        {message && <div className="integration-note" role="status">{message}</div>}
        <form className="range-assignment-form" onSubmit={assignRange}>
          <label>Assigned teacher<select value={form.teacher_id} required onChange={(event) => setForm({ ...form, teacher_id: event.target.value })}><option value="">Select teacher</option>{teachers.map((teacher) => <option value={teacher.id} key={teacher.id}>{teacher.full_name} · {teacher.department}</option>)}</select></label>
          <label>Starting USN<input value={form.start_usn} required placeholder="4NI24CS128" onChange={(event) => setForm({ ...form, start_usn: event.target.value })} /></label>
          <label>Ending USN<input value={form.end_usn} required placeholder="4NI24CS132" onChange={(event) => setForm({ ...form, end_usn: event.target.value })} /></label>
          <button className="button-primary" type="submit" disabled={saving}>{saving ? "Assigning…" : <>Assign USN range <ArrowRight size={16} /></>}</button>
        </form>
      </section>

      <section className="content-panel assignment-panel">
        <div className="section-heading"><div><span className="eyebrow">CURRENT MAPPINGS</span><h2>Active faculty assignments</h2></div><span className="status-badge status-approved">{assignments.filter((item) => item.status === "ACTIVE").length} active</span></div>
        {loading ? <p className="muted-copy">Loading assignments…</p> : assignments.length === 0 ? <p className="muted-copy">No faculty assignments yet.</p> : <div className="assignment-table" role="table"><div className="assignment-table-row assignment-table-head" role="row"><span>Student</span><span>USN</span><span>Department</span><span>Assigned teacher</span><span>Status</span></div>{assignments.map((assignment) => <div className="assignment-table-row" role="row" key={assignment.id}><strong>{assignment.student_name}</strong><span>{assignment.student_usn}</span><span>{assignment.student_department || "—"}</span><span>{assignment.teacher_name}</span><span className={statusClass(assignment.status)}>{assignment.status}</span></div>)}</div>}
      </section>
    </div>
  );
}
