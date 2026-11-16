# Student API

Base URL: `http://127.0.0.1:8000`. Interactive OpenAPI/Swagger: `/docs`. JSON errors use `{"detail": "..."}` unless request validation returns FastAPI's structured validation detail.

All authenticated requests use `Authorization: Bearer <access_token>`. Student tokens are issued by `/auth/login`. User response objects never contain password hashes.

## Authentication

### `POST /auth/register`

Public. Request:

```json
{
  "full_name": "Asha Student",
  "email": "asha@college.edu",
  "usn": "1XX23CS001",
  "department": "Computer Science",
  "semester": 5,
  "password": "AtLeast8Characters"
}
```

Returns `201` with the student profile. The role is assigned as `STUDENT`. Returns `409` if the email or USN is already registered; invalid fields return `422`.

### `POST /auth/login`

Public. Request: `{"email":"asha@college.edu","password":"..."}`. Returns `200` with `access_token`, `token_type`, `expires_in` seconds, and a minimal user object. Invalid credentials return `401`; an inactive account returns `403`.

### `GET /auth/me`

Authenticated. Returns the current user's profile; invalid or expired token returns `401`.

## Categories

### `GET /categories`

Public. Returns the 15 seeded categories ordered by ID.

## Events

### `GET /events`

Public. Returns a paginated `{ "items": [...], "page": 1, "limit": 12, "total": 0 }` response. Query parameters: `search` (event title), `category_id`, `date` (`YYYY-MM-DD` start date), `upcoming` (boolean), `registration_open` (boolean), `page` (1-based), and `limit` (1–100). Results are limited to `PUBLISHED`.

### `GET /events/{event_id}`

Public. Returns one published event and computed available seats. Unpublished or unknown events return `404`.

Both event endpoints return `503` until Person 2's shared `events` table satisfies the integration contract.

## Registrations

### `POST /events/{event_id}/register`

Authenticated `STUDENT` only. No body is accepted. Returns `201` with registration fields and an event summary. Returns `401` if unauthenticated, `403` for another role, `404` for missing/unpublished event, and `409` when the deadline has passed, capacity is reached, or the student already has an active registration. A cancelled row is reactivated if the student registers again.

### `GET /registrations/me`

Authenticated `STUDENT` only. Returns the current student's registrations and event summary. The identity comes from the JWT, not a request-supplied user ID.

## Notifications

### `GET /notifications`

Authenticated. Supports `unread_only` (boolean), `page` (1-based), and `limit` (1–100). Returns `{ "items": [...], "page": 1, "limit": 20, "total": 0 }`, newest first. Only the authenticated user's records are returned.

### `PATCH /notifications/{notification_id}/read`

Authenticated. Marks the current user's notification read and returns it. Unknown or other-user notifications return `404`.

### `PATCH /notifications/read-all`

Authenticated. Marks only the current user's unread notifications as read. Returns `{"updated_count": 0}`.

### `GET /notifications/unread-count`

Authenticated. Returns `{"unread_count": 0}` for the current user.

## Shared service

`app.services.notification_service.notify_event_published(db, event_id, recipient_ids=None)` is called by Person 2's event-publication flow. It creates in-app notices for active students, is idempotent per user/event/title, and does not send email, SMS, or push notifications.
