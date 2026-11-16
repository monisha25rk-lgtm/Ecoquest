import { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { notificationService } from "../services/notificationService.js";
import Sidebar from "../components/Sidebar.jsx";
import Topbar from "../components/Topbar.jsx";

const pageTitles = {
  "/": "Dashboard",
  "/events": "Explore events",
  "/activities": "My activities",
  "/notifications": "Notifications",
  "/leaderboard": "Leaderboard",
  "/profile": "My profile",
};

export default function StudentLayout() {
  const [unreadCount, setUnreadCount] = useState(0);
  const location = useLocation();

  useEffect(() => {
    let active = true;
    notificationService.unreadCount().then(({ unread_count }) => {
      if (active) setUnreadCount(unread_count);
    }).catch(() => {
      if (active) setUnreadCount(0);
    });
    return () => { active = false; };
  }, [location.pathname]);

  const refreshUnread = async () => {
    try { setUnreadCount((await notificationService.unreadCount()).unread_count); } catch { setUnreadCount(0); }
  };
  return (
    <div className="app-shell">
      <Sidebar unreadCount={unreadCount} />
      <div className="app-main">
        <Topbar title={pageTitles[location.pathname] || (location.pathname.startsWith("/events/") ? "Event details" : "EcoQuest")} unreadCount={unreadCount} />
        <main className="page-content"><Outlet context={{ refreshUnread }} /></main>
      </div>
    </div>
  );
}
