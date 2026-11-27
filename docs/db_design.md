# IdeaScope – Database Design

---

## Member 2 Tables (Sufiyaan Imran)

Migration chain: `0001_foundation` → `0002_accounts` → `0003_jobs`  
Other members chain their migrations on top of `0003_jobs`.

---

### users

| Column | Type | Constraints |
|--------|------|-------------|
| id | BIGINT | PK auto |
| username | TEXT | NOT NULL, UNIQUE (`uq_users_username`) |
| full_name | TEXT | NOT NULL |
| email | TEXT | UNIQUE nullable (`uq_users_email`) |
| roll_no | TEXT | UNIQUE nullable (`uq_users_roll_no`) |
| password_hash | TEXT | NOT NULL |
| role | TEXT | NOT NULL, CHECK `role IN ('student','admin')` (`ck_users_role`) |
| is_main_admin | BOOLEAN | NOT NULL default false |
| is_active | BOOLEAN | NOT NULL default true |
| must_change_password | BOOLEAN | NOT NULL default true |
| failed_logins | SMALLINT | NOT NULL default 0 |
| locked_until | TIMESTAMPTZ | nullable |
| last_login_at | TIMESTAMPTZ | nullable |
| created_by | BIGINT | FK users.id nullable, INDEX `ix_users_created_by` |
| created_at | TIMESTAMPTZ | NOT NULL default now() |
| updated_at | TIMESTAMPTZ | NOT NULL default now() |

**Additional constraints:**
- CHECK `NOT is_main_admin OR role = 'admin'` (`ck_users_main_admin_must_be_admin`)
- PARTIAL UNIQUE INDEX `ix_users_is_main_admin_partial` ON `is_main_admin` WHERE `is_main_admin = true` (only one main admin)

**Rules:**
- Users are NEVER deleted – deactivate with `is_active = false`
- For students, `username = lower(roll_no)`
- Login increments `failed_logins`; reaching 5 sets `locked_until = now() + 15 min`

---

### refresh_tokens

| Column | Type | Constraints |
|--------|------|-------------|
| id | BIGINT | PK auto |
| user_id | BIGINT | NOT NULL, FK users.id ON DELETE CASCADE, INDEX `ix_refresh_tokens_user_id` |
| token_hash | TEXT | NOT NULL, UNIQUE (`uq_refresh_tokens_token_hash`) |
| expires_at | TIMESTAMPTZ | NOT NULL |
| revoked_at | TIMESTAMPTZ | nullable (null = not revoked) |
| created_at | TIMESTAMPTZ | NOT NULL default now() |

---

### groups

| Column | Type | Constraints |
|--------|------|-------------|
| id | BIGINT | PK auto |
| name | TEXT | NOT NULL |
| batch | TEXT | NOT NULL (derived from roll_no, e.g. '2023F') |
| leader_id | BIGINT | NOT NULL, FK users.id, INDEX `ix_groups_leader_id` |
| created_at | TIMESTAMPTZ | NOT NULL default now() |

---

### group_members

| Column | Type | Constraints |
|--------|------|-------------|
| group_id | BIGINT | FK groups.id ON DELETE CASCADE, INDEX `ix_group_members_group_id` |
| user_id | BIGINT | FK users.id, UNIQUE (`uq_group_members_user_id`) |
| joined_at | TIMESTAMPTZ | NOT NULL default now() |

**PK:** composite `(group_id, user_id)` (`pk_group_members`)  
**Rule:** a student can only be in ONE group at a time (enforced by UNIQUE on user_id)

---

### categories

| Column | Type | Constraints |
|--------|------|-------------|
| id | SMALLINT | PK (1–12, NOT auto-generated) |
| name | TEXT | NOT NULL, UNIQUE (`uq_categories_name`) |

**12 categories (SSUET proposal form):**

| id | name |
|----|------|
| 1 | Artificial Intelligence and Big Data |
| 2 | Augmented and Virtual Reality |
| 3 | E-Health |
| 4 | E-Commerce |
| 5 | Internet of Things (IoT) |
| 6 | Block Chain |
| 7 | Cloud Computing and Cyber Security |
| 8 | Game Development |
| 9 | Graphics Animation |
| 10 | Nano Technology |
| 11 | Shared Economy |
| 12 | Other |

---

### sdgs

| Column | Type | Constraints |
|--------|------|-------------|
| number | SMALLINT | PK (1–17, NOT auto-generated) |
| name | TEXT | NOT NULL, UNIQUE (`uq_sdgs_name`) |

**17 SDGs:**

| number | name |
|--------|------|
| 1 | No Poverty |
| 2 | Zero Hunger |
| 3 | Good Health and Well-Being |
| 4 | Quality Education |
| 5 | Gender Equality |
| 6 | Clean Water and Sanitation |
| 7 | Affordable and Clean Energy |
| 8 | Decent Work and Economic Growth |
| 9 | Industry, Innovation and Infrastructure |
| 10 | Reduce Inequalities |
| 11 | Sustainable Cities and Communities |
| 12 | Responsible Consumption and Production |
| 13 | Climate Action |
| 14 | Life Below Water |
| 15 | Life On Land |
| 16 | Peace, Justice and Strong Institutions |
| 17 | Partnerships for the Goals |

---

### audit_logs

| Column | Type | Constraints |
|--------|------|-------------|
| id | BIGINT | PK auto |
| actor_id | BIGINT | FK users.id nullable (null = system action), INDEX `ix_audit_logs_actor_id` |
| action | TEXT | NOT NULL (dotted, e.g. `user.created`) |
| target_type | TEXT | nullable |
| target_id | BIGINT | nullable |
| details | JSONB | nullable (old/new values) |
| created_at | TIMESTAMPTZ | NOT NULL default now() |

**INDEX:** `ix_audit_logs_target_type_target_id` ON (target_type, target_id)

**Immutability trigger:** `trg_audit_logs_immutable` BEFORE UPDATE OR DELETE calls  
`audit_logs_immutable()` which raises an exception. No row can ever be changed or deleted.

---

### jobs

| Column | Type | Constraints |
|--------|------|-------------|
| id | BIGINT | PK auto |
| type | TEXT | NOT NULL, CHECK `type IN ('import_file','process_abstract','analyze_proposal','generate_proposal')` (`ck_jobs_type`) |
| target_id | BIGINT | NOT NULL (entity the job operates on; no payload column) |
| status | TEXT | NOT NULL default 'queued', CHECK `status IN ('queued','running','done','failed')` (`ck_jobs_status`) |
| progress | SMALLINT | NOT NULL default 0, CHECK 0–100 (`ck_jobs_progress`) |
| attempts | SMALLINT | NOT NULL default 0 |
| error | TEXT | nullable |
| result | JSONB | nullable |
| created_by | BIGINT | FK users.id nullable, INDEX `ix_jobs_created_by` |
| created_at | TIMESTAMPTZ | NOT NULL default now() |
| started_at | TIMESTAMPTZ | nullable |
| finished_at | TIMESTAMPTZ | nullable |

**INDEX:** `ix_jobs_status_created_at` ON (status, created_at) — used by worker poll query

---

## Migration chain

```
(none) ──► 0001_foundation  (vector extension, categories, sdgs)
              ──► 0002_accounts  (users, refresh_tokens, groups, group_members, audit_logs + trigger)
                     ──► 0003_jobs  (jobs)
                            ──► [Member 3 migrations chain here]
                            ──► [Member 1 migrations chain here]
```
