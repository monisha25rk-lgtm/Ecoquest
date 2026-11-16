import { CheckCheck } from "lucide-react";
import { useEffect, useState } from "react";
import EmptyState from "../components/EmptyState.jsx";
import LoadingSkeleton from "../components/LoadingSkeleton.jsx";
import NotificationItem from "../components/NotificationItem.jsx";
import { useOutletContext } from "react-router-dom";
import { notificationService } from "../services/notificationService.js";

export default function Notifications() {
  const { refreshUnread } = useOutletContext();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const load = () => notificationService.list({ page: 1, limit: 100 }).then((response) => setNotifications(response.items)).catch((requestError) => setError(requestError.message)).finally(() => setLoading(false));
  useEffect(() => { load(); }, []);
  const markRead = async (id) => {
    try {
      const updated = await notificationService.markRead(id);
      setNotifications((current) => current.map((item) => item.id === id ? updated : item));
      refreshUnread();
    } catch (requestError) { setError(requestError.message); }
  };
  const markAll = async () => {
    try {
      await notificationService.markAllRead();
      setNotifications((current) => current.map((item) => ({ ...item, is_read: true })));
      refreshUnread();
    } catch (requestError) { setError(requestError.message); }
  };
  return (
    <div className="notifications-page"><section className="page-intro"><div><span className="eyebrow">STAY IN THE LOOP</span><h1>Notifications</h1><p>Updates about the opportunities and activities you care about.</p></div><button className="button-secondary mark-all-button" onClick={markAll}><CheckCheck size={16} /> Mark all as read</button></section>
      {error && <div className="inline-error" role="status">{error}</div>}
      {loading ? <LoadingSkeleton /> : notifications.length ? <div className="notification-list">{notifications.map((item) => <NotificationItem key={item.id} notification={item} onRead={markRead} />)}</div> : <EmptyState title="You’re all caught up" message="When there’s news to share, you’ll find it here." />}
    </div>
  );
}
