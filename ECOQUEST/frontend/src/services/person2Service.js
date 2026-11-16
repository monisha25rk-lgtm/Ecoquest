import { apiRequest, apiUrl, getToken } from "./api.js";

export const person2Service = {
  organization: () => apiRequest("/organizations/me"),
  registerOrganization: (payload, supportingDocument) => {
    const body = new FormData();
    Object.entries(payload).forEach(([key, value]) => { if (value !== undefined && value !== null) body.append(key, value); });
    if (supportingDocument) body.append("supporting_document", supportingDocument);
    return apiRequest("/organizations/register", { method: "POST", body });
  },
  createEvent: (payload) => apiRequest("/organizer/events", { method: "POST", body: JSON.stringify(payload) }),
  uploadPoster: (eventId, file) => { const body = new FormData(); body.append("poster", file); return apiRequest(`/organizer/events/${eventId}/poster`, { method: "POST", body }); },
  myEvents: () => apiRequest("/organizer/events"),
  organizations: () => apiRequest("/organizations"),
  decideOrganization: (id, payload) => apiRequest(`/organizations/${id}/decision`, { method: "PATCH", body: JSON.stringify(payload) }),
  adminEvents: () => apiRequest("/admin/events"),
  decideEvent: (id, payload) => apiRequest(`/admin/events/${id}/decision`, { method: "PATCH", body: JSON.stringify(payload) }),
  pendingSubmissions: () => apiRequest("/admin/submissions"),
  reviewSubmission: (id, payload) => apiRequest(`/admin/submissions/${id}/review`, { method: "PATCH", body: JSON.stringify(payload) }),
  submitEvidence: (registrationId, formData) => apiRequest(`/registrations/${registrationId}/submission`, { method: "POST", body: formData }),
  addProgress: (registrationId, payload) => apiRequest(`/registrations/${registrationId}/progress`, { method: "POST", body: JSON.stringify(payload) }),
  submission: (registrationId) => apiRequest(`/registrations/${registrationId}/submission`),
  teachers: () => apiRequest("/admin/teachers"),
  students: () => apiRequest("/admin/students"),
  facultyAssignments: () => apiRequest("/admin/faculty-assignments"),
  assignFaculty: (payload) => apiRequest("/admin/faculty-assignments", { method: "POST", body: JSON.stringify(payload) }),
  assignFacultyRange: (payload) => apiRequest("/admin/faculty-assignments/range", { method: "POST", body: JSON.stringify(payload) }),
  teacherDashboard: () => apiRequest("/teacher/dashboard"),
  reviewTeacherSubmission: (id, payload) => apiRequest("/teacher/submissions/" + id + "/review", { method: "PATCH", body: JSON.stringify(payload) }),
  downloadEvidence: async (fileId) => {
    const response = await fetch(`${apiUrl}/submissions/files/${fileId}`, { headers: { Authorization: `Bearer ${getToken()}` } });
    if (!response.ok) throw new Error("This evidence file could not be opened.");
    return response.blob();
  },
};
