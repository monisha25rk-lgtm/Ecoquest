import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./context/AuthContext.jsx";
import StudentLayout from "./layouts/StudentLayout.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import EventDetails from "./pages/EventDetails.jsx";
import ExploreEvents from "./pages/ExploreEvents.jsx";
import Leaderboard from "./pages/Leaderboard.jsx";
import Login from "./pages/Login.jsx";
import MyActivities from "./pages/MyActivities.jsx";
import Notifications from "./pages/Notifications.jsx";
import Profile from "./pages/Profile.jsx";
import LoadingSkeleton from "./components/LoadingSkeleton.jsx";
import StaffLayout from "./layouts/StaffLayout.jsx";
import Person2Dashboard from "./pages/Person2Dashboard.jsx";
import EventSubmission from "./pages/EventSubmission.jsx";
import OrganizerRegistration from "./pages/OrganizerRegistration.jsx";
import TeacherDashboard from "./pages/TeacherDashboard.jsx";
import RoleSelect from "./pages/RoleSelect.jsx";
import RoleRegistration from "./pages/RoleRegistration.jsx";
import FacultyAssignments from "./pages/FacultyAssignments.jsx";
import PendingApprovals from "./pages/PendingApprovals.jsx";

function Protected({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <LoadingSkeleton fullPage />;
  return user ? children : <Navigate to="/login" replace />;
}

function RoleWorkspace() {
  const { user } = useAuth();
  return user?.role === "STUDENT" ? <StudentLayout /> : <StaffLayout />;
}

function WorkspaceHome() {
  const { user } = useAuth();
  if (user?.role === "STUDENT") return <Dashboard />;
  if (user?.role === "TEACHER") return <TeacherDashboard />;
  return <Person2Dashboard />;
}

export default function App() {
  const { user } = useAuth();
  return (
    <Routes>
      <Route path="/welcome" element={user ? <Navigate to="/" replace /> : <RoleSelect />} />
      <Route path="/register-role/:role" element={user ? <Navigate to="/" replace /> : <RoleRegistration />} />
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <Login mode="signin" />} />
      <Route path="/register" element={user ? <Navigate to="/" replace /> : <Login mode="register" />} />
      <Route path="/organizer/register" element={<Protected><OrganizerRegistration /></Protected>} />
      <Route path="/" element={<Protected><RoleWorkspace /></Protected>}>
        <Route index element={<WorkspaceHome />} />
        <Route path="events/new" element={<EventSubmission />} />
        <Route path="verification" element={<Person2Dashboard />} />
        <Route path="approvals" element={<PendingApprovals />} />
        <Route path="faculty-assignments" element={<FacultyAssignments />} />
        <Route path="events" element={<ExploreEvents />} />
        <Route path="events/:eventId" element={<EventDetails />} />
        <Route path="activities" element={<MyActivities />} />
        <Route path="notifications" element={<Notifications />} />
        <Route path="leaderboard" element={<Leaderboard />} />
        <Route path="profile" element={<Profile />} />
      </Route>
      <Route path="*" element={<Navigate to={user ? "/" : "/welcome"} replace />} />
    </Routes>
  );
}
