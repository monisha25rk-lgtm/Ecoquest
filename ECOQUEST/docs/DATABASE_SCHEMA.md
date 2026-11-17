# EcoQuest database schema — Person 1

The shared SQLite database is `backend/ecoquest.db`. All application modules must use the same SQLAlchemy `Base`, engine, database URL, integer primary keys, and metadata. SQLite foreign-key enforcement is enabled by the backend connection module.

## Owned tables

### `users`

| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | Primary key, auto-increment |
| `full_name` | String(160) | Required |
| `email` | String(320) | Required, unique, indexed; normalized lowercase |
| `usn` | String(32) | Required, unique, indexed; normalized uppercase |
| `department` | String(120) | Required |
| `semester` | Integer | Required, 1–12 |
| `password_hash` | String(512) | Required; Argon2 encoded hash, never returned by API |
| `role` | String(20) | Required, defaults to `STUDENT`; exact roles `STUDENT`, `ORGANIZER`, `ADMIN` |
| `created_at` | DateTime | Required, database default current time |
| `is_active` | Boolean | Required, defaults to true |

Public registration always assigns `STUDENT`. Organizer and admin accounts must be provisioned by authorized team processes; a public registration request cannot choose a role.

### `categories`

| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | Primary key, auto-increment |
| `name` | String(300) | Required, unique |
| `description` | Text | Optional |
| `created_at` | DateTime | Required, database default current time |

The initialization procedure idempotently seeds all 15 VTU categories.

### `event_registrations`

| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | Primary key, auto-increment |
| `student_id` | Integer | Required; FK `users.id`, indexed |
| `event_id` | Integer | Required; FK `events.id`, indexed |
| `registration_date` | DateTime | Required, database default current time |
| `status` | String(20) | Required, default `REGISTERED`; values `REGISTERED`, `COMPLETED`, `CANCELLED` |

Unique constraint: `(student_id, event_id)`. A cancelled registration can be reactivated without creating a second row. Only `REGISTERED` rows consume capacity.

### `notifications`

| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | Primary key, auto-increment |
| `user_id` | Integer | Required; FK `users.id`, indexed |
| `title` | String(200) | Required |
| `message` | Text | Required |
| `event_id` | Integer | Optional; FK `events.id`, indexed |
| `is_read` | Boolean | Required, defaults false |
| `created_at` | DateTime | Required, database default current time |

Unique constraint `(user_id, event_id, title)` makes retrying a published-event notification idempotent.

## Eco Points ledger

`point_transactions` is the append-only Eco Points ledger. Awards reference the approved faculty evaluation; reversals are separate negative transactions referencing the original award. The student's current total is the sum of their ledger entries.

| Column | Type | Constraints |
|---|---|---|
| `transaction_id` | Integer | Primary key, auto-increment |
| `student_id` | Integer | Required; FK `users.id`, indexed |
| `event_id` | Integer | Required; FK `events.id`, indexed |
| `evaluation_id` | Integer | Required; FK `reviews.id`, indexed |
| `points` | Integer | Required; nonnegative for `AWARD`, nonpositive for `REVERSAL` |
| `transaction_type` | String(20) | Required; `AWARD` or `REVERSAL` |
| `created_at` | DateTime | Required, database default current time |
| `reversal_of` | Integer | Optional; FK `point_transactions.transaction_id`, unique |

The database enforces one award and one reversal per evaluation and prevents multiple awards or reversals for the same student/event pair.

## Shared tables not owned here

Person 2 owns `organizations`, `events`, `progress_logs`, `submissions`, `submission_files`, and `reviews`. Person 3 owns `badges` and `user_badges`. Person 1 does not define or create substitutes for those tables.

Registration and notification models refer to the shared `events.id`. The event-dependent tables are initialized alongside the shared models when the database starts.
