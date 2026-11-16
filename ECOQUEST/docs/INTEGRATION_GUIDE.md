# EcoQuest module integration guide

## Shared application and database

All three modules must run against one SQLite file and one SQLAlchemy `Base`/engine. Use `app.database.base.Base`, `app.database.connection.engine`, `SessionLocal`, and `get_db`; do not create a second database, Base, user table, category table, or events table. Import all model modules before a full metadata initialization. Keep the shared database at `backend/ecoquest.db` by default, or agree on one `DATABASE_URL` for all processes.

Student-owned models live in `app.models.user`, `category`, `registration`, and `notification`. Models for registrations and notifications declare foreign keys to the Person 2-owned `events.id`. The application postpones creating those two tables until the shared events table exists; it never creates an events table.

## Person 2: events and publication

Provide the shared `events` table with integer primary key and at minimum these columns: `id`, `title`, `category_id`, `start_date`, `end_date`, `venue`, `registration_deadline`, `capacity`, and `status`. The student adapter also returns optional `description`, `organization_id`, eligibility/participation/evidence requirements, poster path, and approved Eco Points when present. Event statuses are `PENDING`, `PUBLISHED`, `REJECTED`, and `CLOSED`.

The event organization table's display name should be exposed as `organizations.name` or `organizations.organization_name`; otherwise discovery remains available but cannot display the organizer's name. Event search currently searches the event title; extend the agreed shared query once Person 2 confirms the organization relationship and display column.

After an event has been committed as `PUBLISHED`, create a session and invoke:

```python
from app.services.notification_service import notify_event_published

notify_event_published(db, event_id)
```

Provide `recipient_ids=[...]` when the event is targeted to a known audience. Calls are safe to retry. The event must already be published in the shared database.

Person 2 can query student signups from `app.models.registration.EventRegistration`. `student_id` references `users.id`, and the status is one of `REGISTERED`, `COMPLETED`, `CANCELLED`. Only `REGISTERED` occupies event capacity. There is one unique registration row per student/event pair; a cancelled row can be reactivated.

Shared authentication and role dependencies:

```python
from app.dependencies.auth import get_current_user, require_role

router.add_api_route("/protected", handler, dependencies=[Depends(require_role("ADMIN"))])
```

For code that needs the principal, declare `user: User = Depends(require_role("ADMIN"))`. The same `get_current_user` supports `STUDENT`, `ORGANIZER`, and `ADMIN` accounts.

## Person 3: gamification

Person 3 should use the shared `users.id` identity and database. Do not calculate points, award badges, rank students, or generate reports in the Person 1 module.

Agree on URLs and response structures before wiring gamification. Once agreed, set the three full endpoint URLs in the frontend environment:

- `VITE_GAMIFICATION_SUMMARY_URL`
- `VITE_GAMIFICATION_BADGES_URL`
- `VITE_GAMIFICATION_LEADERBOARD_URL`

The adapter passes the current JWT and renders the returned service data. Without configured endpoints it explicitly reports that the feature is unavailable; it does not fabricate a score or rank.

## Student web client

Frontend API wrappers are centralized in `frontend/src/services`. The base API URL is `VITE_API_BASE_URL`. All authenticated service calls use the JWT from `AuthContext`'s API token storage. CORS allows the configured `FRONTEND_URL` origin.

## Known integration boundary

This checkout did not contain Person 2 or Person 3 source files or schemas. Person 2 must integrate the shared events and organizations schema and publication callback; Person 3 must supply agreed endpoint URLs and response formats. Until then, accounts and categories initialize normally and event-dependent tables/endpoints remain clearly unavailable.
