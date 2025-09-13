# KinAura Entity Relationship Diagram

## Core Entities Overview

```
Organizations (Multi-tenant)
├── Profiles (Users)
├── Clinicians (Staff)
├── Patients (CRM)
├── Services (Catalog)
├── Appointments (Scheduling)
├── Segments (Marketing)
├── Campaigns (Notifications)
└── Audit Logs (Compliance)

Patients (Central Entity)
├── Patient Groups (Segmentation)
├── Patient Notes (Documentation)
├── Memberships (Billing)
├── Protocols (Clinical)
├── Analyses (Lab Results)
├── Pre/Post Sets (Images)
├── Longevity Scores (AI)
├── Formulas (Commerce)
├── Orders (Commerce)
├── Threads (Messaging)
├── Notifications (Alerts)
└── Consents (GDPR)
```

## Detailed Entity Relationships

### Identity & Organization Layer

```sql
organizations
├── id (UUID, PK)
├── name (TEXT)
├── timezone (TEXT)
└── billing_email (TEXT)

profiles
├── id (UUID, PK, FK → auth.users)
├── org_id (UUID, FK → organizations)
├── role (user_role ENUM)
├── vip_tier (vip_tier ENUM)
├── marketing_consent (BOOLEAN)
├── privacy_consent (BOOLEAN)
└── full_name (TEXT)

clinicians
├── id (UUID, PK)
├── org_id (UUID, FK → organizations)
├── profile_id (UUID, FK → profiles)
├── name (TEXT)
├── specialization (TEXT)
└── license_number (TEXT)
```

### Patient Management Layer

```sql
patients
├── id (UUID, PK)
├── org_id (UUID, FK → organizations)
├── code (TEXT, UNIQUE)
├── full_name (TEXT)
├── email (TEXT)
├── phone (TEXT)
├── dob (DATE)
├── gender (gender_type ENUM)
├── tags (TEXT[])
├── owner_user_id (UUID, FK → profiles)
├── notes_summary (TEXT)
├── deleted_at (TIMESTAMPTZ) -- Soft delete
├── created_at (TIMESTAMPTZ)
└── updated_at (TIMESTAMPTZ)

patient_groups
├── id (UUID, PK)
├── org_id (UUID, FK → organizations)
├── name (TEXT)
└── description (TEXT)

patient_group_members
├── group_id (UUID, PK, FK → patient_groups)
├── patient_id (UUID, PK, FK → patients)
└── added_at (TIMESTAMPTZ)

patient_notes
├── id (UUID, PK)
├── patient_id (UUID, FK → patients)
├── author_id (UUID, FK → profiles)
├── visibility (note_visibility ENUM)
├── content (TEXT)
├── attachments (JSONB)
├── created_at (TIMESTAMPTZ)
└── updated_at (TIMESTAMPTZ)
```

### Membership & Billing Layer

```sql
membership_plans
├── id (UUID, PK)
├── org_id (UUID, FK → organizations)
├── name (TEXT)
├── tier (vip_tier ENUM)
├── price_cents (INTEGER)
├── perks (JSONB)
├── billing_period (billing_period ENUM)
└── is_active (BOOLEAN)

memberships
├── id (UUID, PK)
├── patient_id (UUID, FK → patients)
├── org_id (UUID, FK → organizations)
├── plan_id (UUID, FK → membership_plans)
├── status (membership_status ENUM)
├── start_date (DATE)
├── end_date (DATE)
└── auto_renew (BOOLEAN)
```

### Clinical & AI Layer

```sql
protocols
├── id (UUID, PK)
├── patient_id (UUID, FK → patients)
├── name (TEXT)
├── goals (JSONB) -- {"inflammation": "reduce", "texture": "improve"}
├── status (protocol_status ENUM)
├── ai_version (TEXT)
├── last_ai_update_at (TIMESTAMPTZ)
├── created_at (TIMESTAMPTZ)
└── updated_at (TIMESTAMPTZ)

protocol_sessions
├── id (UUID, PK)
├── protocol_id (UUID, FK → protocols)
├── idx (INTEGER) -- Session order
├── title (TEXT)
├── status (session_status ENUM)
├── scheduled_at (TIMESTAMPTZ)
├── completed_at (TIMESTAMPTZ)
├── clinician_id (UUID, FK → clinicians)
├── notes (TEXT)
├── created_at (TIMESTAMPTZ)
└── updated_at (TIMESTAMPTZ)

analyses
├── id (UUID, PK)
├── patient_id (UUID, FK → patients)
├── kind (analysis_kind ENUM) -- blood, hormonal, oligoscan, etc.
├── metrics (JSONB) -- Lab values and biomarkers
├── source (analysis_source ENUM) -- upload vs clinic
├── document_ids (JSONB) -- Storage references
├── created_by (UUID, FK → profiles)
├── created_at (TIMESTAMPTZ)
└── updated_at (TIMESTAMPTZ)

prepost_sets
├── id (UUID, PK)
├── patient_id (UUID, FK → patients)
├── treatment_context (TEXT)
├── before_image (TEXT) -- Storage path
├── after_image (TEXT) -- Storage path
├── diff_meta (JSONB) -- Comparison statistics
├── notes (TEXT)
├── created_at (TIMESTAMPTZ)
└── updated_at (TIMESTAMPTZ)

longevity_scores
├── id (UUID, PK)
├── patient_id (UUID, FK → patients)
├── score_numeric (INTEGER 0-100)
├── components (JSONB) -- Component breakdown
├── community_avg_snapshot (NUMERIC)
├── computed_at (TIMESTAMPTZ)
└── created_at (TIMESTAMPTZ)
```

### Commerce Layer

```sql
formulas
├── id (UUID, PK)
├── patient_id (UUID, FK → patients)
├── analysis_id (UUID, FK → analyses)
├── name (TEXT)
├── actives (JSONB) -- Active ingredients
├── concentration (JSONB) -- Percentages
├── fragrance (TEXT)
├── packaging (packaging_type ENUM)
├── price_cents (INTEGER ≥ 15000) -- Minimum €150
├── status (formula_status ENUM)
├── created_at (TIMESTAMPTZ)
└── updated_at (TIMESTAMPTZ)

orders
├── id (UUID, PK)
├── patient_id (UUID, FK → patients)
├── formula_id (UUID, FK → formulas)
├── channel (order_channel ENUM) -- in_clinic vs app
├── status (order_status ENUM)
├── total_cents (INTEGER)
├── payment_ref (TEXT)
├── created_at (TIMESTAMPTZ)
└── updated_at (TIMESTAMPTZ)
```

### Services & Scheduling Layer

```sql
services
├── id (UUID, PK)
├── org_id (UUID, FK → organizations)
├── category (service_category ENUM)
├── name (TEXT)
├── description (TEXT)
├── duration_min (INTEGER)
├── base_price_cents (INTEGER)
├── is_active (BOOLEAN)
├── created_at (TIMESTAMPTZ)
└── updated_at (TIMESTAMPTZ)

appointments
├── id (UUID, PK)
├── patient_id (UUID, FK → patients)
├── org_id (UUID, FK → organizations)
├── service_id (UUID, FK → services)
├── starts_at (TIMESTAMPTZ)
├── ends_at (TIMESTAMPTZ)
├── practitioner_id (UUID, FK → clinicians)
├── status (appointment_status ENUM)
├── notes (TEXT)
├── created_at (TIMESTAMPTZ)
└── updated_at (TIMESTAMPTZ)
```

### Messaging Layer

```sql
threads
├── id (UUID, PK)
├── patient_id (UUID, FK → patients)
├── created_by (UUID, FK → profiles)
├── last_message_at (TIMESTAMPTZ)
├── created_at (TIMESTAMPTZ)
└── updated_at (TIMESTAMPTZ)

messages
├── id (UUID, PK)
├── thread_id (UUID, FK → threads)
├── sender_id (UUID, FK → profiles)
├── sender_role (sender_role ENUM)
├── body (TEXT)
├── attachments (JSONB)
├── read_at (TIMESTAMPTZ)
├── created_at (TIMESTAMPTZ)
└── updated_at (TIMESTAMPTZ)
```

### Marketing & Notifications Layer

```sql
segments
├── id (UUID, PK)
├── org_id (UUID, FK → organizations)
├── name (TEXT)
├── definition (JSONB) -- Filter criteria DSL
├── created_at (TIMESTAMPTZ)
└── updated_at (TIMESTAMPTZ)

campaigns
├── id (UUID, PK)
├── org_id (UUID, FK → organizations)
├── name (TEXT)
├── channel (notification_channel ENUM)
├── template_id (TEXT)
├── segment_id (UUID, FK → segments)
├── status (campaign_status ENUM)
├── sent_count (INTEGER)
├── metadata (JSONB)
├── created_at (TIMESTAMPTZ)
└── updated_at (TIMESTAMPTZ)

notifications
├── id (UUID, PK)
├── patient_id (UUID, FK → patients)
├── channel (notification_channel ENUM)
├── title (TEXT)
├── body (TEXT)
├── data (JSONB)
├── status (notification_status ENUM)
├── provider_id (TEXT)
├── created_at (TIMESTAMPTZ)
├── sent_at (TIMESTAMPTZ)
└── updated_at (TIMESTAMPTZ)
```

### Compliance Layer

```sql
audit_logs
├── id (UUID, PK)
├── actor_id (UUID, FK → profiles)
├── org_id (UUID, FK → organizations)
├── action (TEXT)
├── entity_table (TEXT)
├── entity_id (UUID)
├── diff (JSONB) -- Before/after changes
└── created_at (TIMESTAMPTZ)

consents
├── id (UUID, PK)
├── patient_id (UUID, FK → patients)
├── kind (consent_kind ENUM) -- privacy, marketing, data_use
├── granted (BOOLEAN)
├── granted_at (TIMESTAMPTZ)
├── method (TEXT) -- How consent was obtained
├── created_at (TIMESTAMPTZ)
└── updated_at (TIMESTAMPTZ)
```

## Key Relationships

### One-to-Many Relationships
- `organizations` → `profiles` (1:N)
- `organizations` → `patients` (1:N)
- `patients` → `protocols` (1:N)
- `patients` → `analyses` (1:N)
- `patients` → `appointments` (1:N)
- `protocols` → `protocol_sessions` (1:N)
- `threads` → `messages` (1:N)

### Many-to-Many Relationships
- `patients` ↔ `patient_groups` (via `patient_group_members`)

### Optional Relationships
- `formulas` → `analyses` (N:1, optional)
- `appointments` → `clinicians` (N:1, optional)
- `protocol_sessions` → `clinicians` (N:1, optional)

## Indexes Strategy

### Primary Access Patterns
```sql
-- Organization-scoped queries
CREATE INDEX idx_patients_org_id ON patients(org_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_appointments_org_starts ON appointments(org_id, starts_at);

-- Patient-centric queries
CREATE INDEX idx_protocols_patient ON protocols(patient_id);
CREATE INDEX idx_analyses_patient ON analyses(patient_id);
CREATE INDEX idx_longevity_scores_patient ON longevity_scores(patient_id);

-- Status and filtering
CREATE INDEX idx_notifications_patient_status ON notifications(patient_id, status);
CREATE INDEX idx_appointments_status ON appointments(status, starts_at);

-- Search and tags
CREATE INDEX idx_patients_tags ON patients USING GIN(tags);
CREATE INDEX idx_analyses_metrics ON analyses USING GIN(metrics);
CREATE INDEX idx_protocols_goals ON protocols USING GIN(goals);

-- Audit and compliance
CREATE INDEX idx_audit_logs_org_created ON audit_logs(org_id, created_at);
```

## Data Flow Examples

### Patient Onboarding Flow
1. Create `patients` record with org association
2. Create `memberships` record with selected plan
3. Create `consents` records for GDPR compliance
4. Create initial `patient_notes` for intake
5. Log creation in `audit_logs`

### Treatment Protocol Flow
1. Ingest `analyses` data from lab results
2. AI generates/updates `protocols` with new goals
3. Create `protocol_sessions` timeline
4. Schedule `appointments` for sessions
5. Track progress in `longevity_scores`
6. Store before/after in `prepost_sets`

### Commerce Flow
1. Create `formulas` based on `analyses`
2. Finalize formula with €150+ validation
3. Create `orders` with payment integration
4. Process payment webhook updates
5. Log all actions in `audit_logs`

### Messaging Flow
1. Create `threads` between patient and staff
2. Send `messages` with real-time delivery
3. Store file attachments in Supabase Storage
4. Track read receipts and notifications
5. Enable search across message history

This ERD supports the complete KinAura platform with proper normalization, performance optimization, and GDPR compliance while maintaining clear relationships between all business entities.