# IdeaScope – API Contracts

---

## Member 2 – Auth, Users, Groups, Jobs

Owner: Sufiyaan Imran  
Base URL: `http://localhost:8000`  
Auth header: `Authorization: Bearer <access_token>`

---

### Common error codes

| HTTP | detail | Meaning |
|------|--------|---------|
| 400 | `wrong_current_password` | Supplied current password is incorrect |
| 400 | `use_change_password` | Cannot reset your own password via admin endpoint |
| 400 | `roll_no_required_for_student` | roll_no missing when creating a student |
| 400 | `username_required_for_admin` | username missing when creating an admin |
| 400 | `new_password_same_as_current` | New password must differ |
| 401 | `invalid_credentials` | Bad username or password on login |
| 401 | `invalid_token` | Access token missing, expired, or wrong type |
| 401 | `invalid_refresh_token` | Refresh token invalid, revoked, or expired |
| 403 | `forbidden` | Role does not allow this action |
| 403 | `account_deactivated` | Account exists but is_active = false |
| 403 | `password_change_required` | must_change_password = true; use /auth/change-password first |
| 403 | `main_admin_protected` | Operation not allowed on/by the main admin |
| 403 | `cannot_change_own_role` | A user cannot change their own role |
| 404 | `user_not_found` | No user with that ID |
| 404 | `group_not_found` | No group with that ID |
| 404 | `no_group` | The user is not in any group |
| 404 | `not_a_member` | Target user is not a member of this group |
| 404 | `job_not_found` | No job with that ID |
| 409 | `username_already_exists` | Username taken |
| 409 | `email_already_exists` | Email taken |
| 409 | `roll_no_already_exists` | Roll number taken |
| 409 | `already_in_group` | Student is already in a group |
| 409 | `not_a_student` | Target user is not an active student |
| 409 | `group_full` | Group has reached max_group_size |
| 409 | `user_in_group` | Cannot promote to admin while student is in a group |
| 409 | `roll_no_required` | Cannot demote to student without a roll_no |
| 409 | `group_has_proposals` | Cannot delete the group (FK constraint from proposals) |
| 423 | `account_locked` | Account is locked due to too many failed login attempts |

---

### Paginated list response shape

```json
{
  "items": [...],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

Query params: `page` (default 1), `page_size` (default 20, max 100), `q` (search string).

---

### User object (never includes password_hash or failed_logins)

```json
{
  "id": 1,
  "username": "2023f-bse-001",
  "full_name": "Ali Ahmed",
  "email": "ali@example.com",
  "roll_no": "2023F-BSE-001",
  "role": "student",
  "is_main_admin": false,
  "is_active": true,
  "must_change_password": true,
  "locked_until": null,
  "last_login_at": "2025-01-10T09:30:00+00:00",
  "created_by": 1,
  "created_at": "2025-01-01T00:00:00+00:00",
  "updated_at": "2025-01-01T00:00:00+00:00"
}
```

---

### Token response

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "must_change_password": true,
  "user": { ...user object... }
}
```

---

### 1. GET /health

No auth required.

**Response 200:**
```json
{ "status": "ok", "database": "ok" }
```

---

### 2. POST /auth/login

**Request:**
```json
{ "username": "2023f-bse-001", "password": "Password1" }
```

**Response 200:** Token response  
**Errors:** 401 `invalid_credentials`, 403 `account_deactivated`, 423 `account_locked`

---

### 3. POST /auth/refresh

**Request:**
```json
{ "refresh_token": "eyJ..." }
```

**Response 200:** Token response (new pair; old refresh token revoked)  
**Errors:** 401 `invalid_refresh_token`

---

### 4. POST /auth/logout *(get_current_user_any)*

**Request:**
```json
{ "refresh_token": "eyJ..." }
```

**Response 204** (always, even if token was already revoked)

---

### 5. GET /auth/me *(get_current_user_any)*

**Response 200:** User object

---

### 6. POST /auth/change-password *(get_current_user_any)*

**Request:**
```json
{ "current_password": "OldPass1", "new_password": "NewPass99" }
```

**Response 200:** Token response (new pair; ALL refresh tokens revoked)  
**Errors:** 400 `wrong_current_password`, 400 `new_password_same_as_current`

---

### 7. GET /users *(require_admin)*

Query: `role`, `is_active`, `q`, `page`, `page_size`  
**Response 200:** Paginated users

---

### 8. POST /users *(require_admin)*

**Request:**
```json
{
  "full_name": "Ali Ahmed",
  "role": "student",
  "roll_no": "2023F-BSE-001",
  "email": "ali@example.com",
  "password": "optional"
}
```

For `role=admin`: `username` is required instead of `roll_no`.

**Response 201:**
```json
{
  "user": { ...user object... },
  "temporary_password": "Abc123Xyz9" 
}
```
`temporary_password` is only present when the password was auto-generated.

---

### 9. GET /users/{id} *(require_admin)*

**Response 200:** User object  
**Errors:** 404 `user_not_found`

---

### 10. PATCH /users/{id} *(require_admin)*

**Request:** (all fields optional)
```json
{ "full_name": "New Name", "email": "new@example.com", "roll_no": "2023F-BSE-002" }
```

For a student: changing `roll_no` also updates `username`.  
**Response 200:** User object

---

### 11. PATCH /users/{id}/role *(require_admin)*

**Request:**
```json
{ "role": "admin" }
```

**Response 200:** User object  
**Errors:** 403 `main_admin_protected`, 403 `cannot_change_own_role`, 409 `user_in_group`, 409 `roll_no_required`

---

### 12. POST /users/{id}/reset-password *(require_admin)*

**Response 200:**
```json
{ "temporary_password": "Abc123Xyz9" }
```

**Errors:** 400 `use_change_password`, 403 `main_admin_protected`

---

### 13. PATCH /users/{id}/status *(require_main_admin)*

**Request:**
```json
{ "is_active": false }
```

**Response 200:** User object  
**Errors:** 403 `main_admin_protected`

---

### 14. POST /groups *(get_current_user, student only)*

**Request:**
```json
{ "name": "Team Alpha" }
```

**Response 201:** Group object  
`batch` is extracted from `roll_no` (part before first `-`).

---

### 15. GET /groups/me *(get_current_user)*

**Response 200:** Group object  
**Errors:** 404 `no_group`

---

### 16. POST /groups/{id}/members *(get_current_user)*

**Request:**
```json
{ "user_id": 5 }
```

`user_id` is optional; omitting it means "join myself".  
**Response 201:** Group object  
**Errors:** 409 `not_a_student`, 409 `already_in_group`, 409 `group_full`

---

### 17. DELETE /groups/{id}/members/{userId} *(get_current_user)*

**Response 204**  
If leader leaves: leadership transfers to earliest-joined remaining member.  
If last member leaves: group is deleted.  
**Errors:** 404 `not_a_member`, 409 `group_has_proposals`

---

### 18. GET /groups *(require_admin)*

Query: `q`, `page`, `page_size`  
**Response 200:** Paginated list; each item includes `member_count`.

---

### 19. GET /groups/{id} *(get_current_user)*

Allowed for group members and admins.  
**Response 200:** Group object  
**Errors:** 403 `forbidden`

### Group object shape

```json
{
  "id": 1,
  "name": "Team Alpha",
  "batch": "2023F",
  "leader_id": 2,
  "created_at": "2025-01-01T00:00:00+00:00",
  "members": [
    {
      "user_id": 2,
      "full_name": "Ali Ahmed",
      "username": "2023f-bse-001",
      "roll_no": "2023F-BSE-001",
      "email": null,
      "joined_at": "2025-01-01T00:00:00+00:00",
      "is_leader": true
    }
  ]
}
```

---

### 20. GET /jobs/{id} *(get_current_user)*

Allowed for the job creator or any admin.  
**Response 200:**
```json
{
  "id": 1,
  "type": "process_abstract",
  "target_id": 42,
  "status": "done",
  "progress": 100,
  "attempts": 1,
  "error": null,
  "result": { "extracted_fields": 7 },
  "created_by": 3,
  "created_at": "...",
  "started_at": "...",
  "finished_at": "..."
}
```

---

## JOB CONTRACT (for Members 1 and 3)

### Enqueue a job

```python
from app.worker.queue import enqueue_job

job = enqueue_job(
    db=db,
    job_type="process_abstract",   # see valid types below
    target_id=past_project.id,     # the entity the job operates on
    created_by=current_user.id,    # optional, can be None
)
db.commit()
# Poll status at GET /jobs/{job.id}
```

### Valid job types

| Constant | Value | Used for |
|----------|-------|---------|
| `JOB_TYPE_IMPORT_FILE` | `"import_file"` | Excel/CSV batch import (M3) |
| `JOB_TYPE_PROCESS_ABSTRACT` | `"process_abstract"` | AI extraction on a past project (M1) |
| `JOB_TYPE_ANALYZE_PROPOSAL` | `"analyze_proposal"` | Full readiness analysis of a proposal (M1) |
| `JOB_TYPE_GENERATE_PROPOSAL` | `"generate_proposal"` | AI document generation (M1) |

### Handler locations and signatures

| Job type | Module | Function |
|----------|--------|---------|
| `import_file` | `app.ingestion.excel_import` | `handle_import_file(db, job)` |
| `process_abstract` | `app.ai.pipelines` | `handle_process_abstract(db, job)` |
| `analyze_proposal` | `app.ai.pipelines` | `handle_analyze_proposal(db, job)` |
| `generate_proposal` | `app.ai.pipelines` | `handle_generate_proposal(db, job)` |

### Handler contract

```python
def handle_xxx(db: Session, job: Job) -> None:
    """
    - Read job.target_id to find the entity to process.
    - Update job.progress (0–100) during long operations.
    - Set job.result = {...} with any output data before returning.
    - Raise any Exception on failure; the worker handles retry and status.
    - Do NOT commit the job row; the worker owns that.
    - The worker DOES commit your other DB changes on success, so flush 
      intermediate writes but let the worker commit them.
    """
```

### Retry behaviour

- On exception: the worker rolls back, increments `job.attempts`.
- If `attempts < MAX_JOB_ATTEMPTS` (3): status → `queued` (retried next poll).
- If `attempts == MAX_JOB_ATTEMPTS`: status → `failed`, `error` = traceback text.
- `job.progress` and `job.result` are for informational use; poll `GET /jobs/{id}`.
