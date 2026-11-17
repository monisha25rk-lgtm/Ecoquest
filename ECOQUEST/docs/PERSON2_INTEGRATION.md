# Person 2 integration contract

Person 2 uses the shared `users`, `categories`, `event_registrations`, and `notifications` tables and the same JWT dependency. Person 1's published-event routes read the Person 2 `events` table, so an event is visible only after an admin decision of `PUBLISHED`.

## Endpoints

| Method | Path | Role | Purpose |
|---|---|---|---|
| POST | `/organizations/register` | Public | Create an `ORGANIZER` account and a `PENDING` organization |
| GET | `/organizations/me` | ORGANIZER | Read organization approval status |
| GET/PATCH | `/organizations`, `/organizations/{id}/decision` | ADMIN | Review organization requests |
| POST | `/organizer/events` | ORGANIZER | Submit a proposal; organization must be `APPROVED` |
| POST | `/organizer/events/{id}/poster` | ORGANIZER | Upload a JPG/PNG/WEBP poster |
| GET/PATCH | `/admin/events`, `/admin/events/{id}/decision` | ADMIN | Publish or reject proposals |
| POST | `/registrations/{id}/progress` | STUDENT | Add a participation log |
| POST | `/registrations/{id}/submission` | STUDENT | Upload evidence and submit for review |
| GET/PATCH | `/admin/submissions`, `/admin/submissions/{id}/review` | ADMIN | Review evidence |

Evidence accepts JPG, PNG, WEBP, DOC, DOCX, and PDF files up to 10 MB each. Stored filenames are randomized and original filenames are never used as filesystem paths.

## Publication and rewards

Publishing calls Person 1's `notify_event_published` service after commit, making publication notifications idempotent. Approving evidence records a `reviews` row and calls `trigger_reward_allocation` with the registration and evaluation IDs. The connected Eco Points service records one award for the approved evaluation in `point_transactions`, using the approved event points and faculty grade. Repeated approval requests reuse the existing evaluation and award.

An authorized evaluating faculty member or college admin can reverse an award through `POST /points/transactions/{transaction_id}/reverse`. Reversals are retained as separate negative transactions and can only be recorded once per award. Students read their live total and transaction history from `GET /points/me`.

The implementation uses the specification's exact status values, including `PENDING`, `APPROVED`, `REJECTED`, `PUBLISHED`, `REGISTERED`, `COMPLETED`, `CANCELLED`, `DRAFT`, and `CHANGES_REQUESTED`.
