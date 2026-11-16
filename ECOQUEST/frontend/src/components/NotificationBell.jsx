import { Bell } from "lucide-react";
import { Link } from "react-router-dom";

export default function NotificationBell({ count = 0 }) {
  return <Link className="icon-button notification-bell" to="/notifications" aria-label={`${count} unread notifications`}><Bell size={19} />{count > 0 && <span className="notification-count">{count > 99 ? "99+" : count}</span>}</Link>;
}
