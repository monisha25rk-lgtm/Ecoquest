import { ArrowUpRight, Bell, Check } from "lucide-react";
import { Link } from "react-router-dom";

export default function NotificationItem({ notification, onRead }) {
  const content = <><span className="notification-item-icon"><Bell size={17} /></span><span className="notification-item-body"><strong>{notification.title}</strong><span>{notification.message}</span><time>{new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(notification.created_at))}</time></span>{!notification.is_read && <span className="unread-dot" />}</>;
  return (
    <article className={`notification-item ${notification.is_read ? "is-read" : "is-unread"}`}>
      {notification.event_id ? <Link className="notification-link" to={`/events/${notification.event_id}`}>{content}<ArrowUpRight size={16} /></Link> : <div className="notification-link">{content}</div>}
      {!notification.is_read && <button className="mark-read-button" type="button" onClick={() => onRead(notification.id)} aria-label="Mark as read"><Check size={16} /></button>}
    </article>
  );
}
