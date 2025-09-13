-- KinAura Initial Schema Migration
-- This creates the complete database schema for the KinAura wellness platform

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Custom types and enums
CREATE TYPE user_role AS ENUM ('admin', 'practitioner', 'member', 'guest');
CREATE TYPE gender_type AS ENUM ('male', 'female', 'other', 'prefer_not_to_say');
CREATE TYPE vip_tier AS ENUM ('standard', 'gold', 'platinum', 'elite');
CREATE TYPE membership_status AS ENUM ('active', 'paused', 'canceled', 'expired');
CREATE TYPE billing_period AS ENUM ('monthly', 'quarterly', 'yearly');
CREATE TYPE protocol_status AS ENUM ('active', 'completed', 'paused');
CREATE TYPE session_status AS ENUM ('done', 'scheduled', 'skipped');
CREATE TYPE analysis_kind AS ENUM ('blood', 'hormonal', 'oligoscan', 'dna', 'microbiome', 'skin_scan', 'other');
CREATE TYPE analysis_source AS ENUM ('upload', 'clinic');
CREATE TYPE formula_status AS ENUM ('draft', 'finalized');
CREATE TYPE order_status AS ENUM ('pending', 'paid', 'fulfilled', 'canceled');
CREATE TYPE order_channel AS ENUM ('in_clinic', 'app');
CREATE TYPE appointment_status AS ENUM ('scheduled', 'confirmed', 'rescheduled', 'completed', 'no_show', 'canceled');
CREATE TYPE service_category AS ENUM ('aesthetics', 'regenerative', 'iv_therapy', 'skincare', 'other');
CREATE TYPE sender_role AS ENUM ('patient', 'admin', 'practitioner');
CREATE TYPE notification_channel AS ENUM ('push', 'email', 'sms');
CREATE TYPE notification_status AS ENUM ('queued', 'sent', 'failed');
CREATE TYPE campaign_status AS ENUM ('draft', 'scheduled', 'sending', 'sent', 'paused');
CREATE TYPE note_visibility AS ENUM ('internal', 'practitioner_only');
CREATE TYPE consent_kind AS ENUM ('privacy', 'marketing', 'data_use');
CREATE TYPE packaging_type AS ENUM ('tube', 'jar', 'bottle', 'serum_bottle');

-- Core identity & organization tables
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    timezone TEXT DEFAULT 'Europe/Rome',
    billing_email TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    role user_role DEFAULT 'member',
    locale TEXT DEFAULT 'it-IT',
    marketing_consent BOOLEAN DEFAULT FALSE,
    privacy_consent BOOLEAN DEFAULT FALSE,
    vip_tier vip_tier DEFAULT 'standard',
    avatar_url TEXT,
    full_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE clinicians (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    profile_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    specialization TEXT,
    license_number TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Patients & CRM
CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    code TEXT UNIQUE, -- Patient identifier
    full_name TEXT NOT NULL,
    dob DATE,
    gender gender_type,
    phone TEXT,
    email TEXT,
    country TEXT DEFAULT 'IT',
    tags TEXT[] DEFAULT '{}',
    owner_user_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    notes_summary TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL -- Soft delete
);

CREATE TABLE patient_groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE patient_group_members (
    group_id UUID REFERENCES patient_groups(id) ON DELETE CASCADE,
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    added_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (group_id, patient_id)
);

CREATE TABLE patient_notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    author_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    visibility note_visibility DEFAULT 'practitioner_only',
    content TEXT NOT NULL,
    attachments JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Membership system
CREATE TABLE membership_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    tier vip_tier NOT NULL,
    price_cents INTEGER NOT NULL CHECK (price_cents >= 0),
    perks JSONB DEFAULT '{}',
    billing_period billing_period DEFAULT 'monthly',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE memberships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    plan_id UUID NOT NULL REFERENCES membership_plans(id) ON DELETE RESTRICT,
    status membership_status DEFAULT 'active',
    start_date DATE NOT NULL,
    end_date DATE,
    auto_renew BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Clinical & AI system
CREATE TABLE protocols (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    goals JSONB DEFAULT '{}', -- e.g., {"inflammation": "reduce", "texture": "improve", "detox": "cellular"}
    status protocol_status DEFAULT 'active',
    ai_version TEXT,
    last_ai_update_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE protocol_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    protocol_id UUID NOT NULL REFERENCES protocols(id) ON DELETE CASCADE,
    idx INTEGER NOT NULL, -- Session order
    title TEXT NOT NULL,
    status session_status DEFAULT 'scheduled',
    scheduled_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    clinician_id UUID REFERENCES clinicians(id) ON DELETE SET NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(protocol_id, idx)
);

CREATE TABLE analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    kind analysis_kind NOT NULL,
    metrics JSONB DEFAULT '{}',
    source analysis_source DEFAULT 'upload',
    document_ids JSONB DEFAULT '[]', -- References to Storage objects
    created_by UUID REFERENCES profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE prepost_sets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    treatment_context TEXT,
    before_image TEXT, -- Storage path
    after_image TEXT,  -- Storage path
    diff_meta JSONB DEFAULT '{}', -- Comparison statistics
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE longevity_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    score_numeric INTEGER NOT NULL CHECK (score_numeric >= 0 AND score_numeric <= 100),
    components JSONB DEFAULT '{}', -- adherence, biomarker_deltas, skin_improvements, inflammation_markers
    community_avg_snapshot NUMERIC(5,2),
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Commerce (skincare formulas)
CREATE TABLE formulas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    analysis_id UUID REFERENCES analyses(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    actives JSONB DEFAULT '{}',
    concentration JSONB DEFAULT '{}',
    fragrance TEXT,
    packaging packaging_type DEFAULT 'jar',
    price_cents INTEGER NOT NULL CHECK (price_cents >= 15000), -- Minimum €150
    status formula_status DEFAULT 'draft',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    formula_id UUID REFERENCES formulas(id) ON DELETE SET NULL,
    channel order_channel DEFAULT 'app',
    status order_status DEFAULT 'pending',
    total_cents INTEGER NOT NULL CHECK (total_cents >= 0),
    payment_ref TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Services and bookings
CREATE TABLE services (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    category service_category DEFAULT 'other',
    name TEXT NOT NULL,
    description TEXT,
    duration_min INTEGER DEFAULT 60,
    base_price_cents INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE appointments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    service_id UUID REFERENCES services(id) ON DELETE SET NULL,
    starts_at TIMESTAMPTZ NOT NULL,
    ends_at TIMESTAMPTZ NOT NULL,
    practitioner_id UUID REFERENCES clinicians(id) ON DELETE SET NULL,
    status appointment_status DEFAULT 'scheduled',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Messaging system
CREATE TABLE threads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    last_message_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    thread_id UUID NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    sender_role sender_role NOT NULL,
    body TEXT NOT NULL,
    attachments JSONB DEFAULT '[]',
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Marketing and notifications
CREATE TABLE segments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    definition JSONB NOT NULL, -- Filter criteria as JSON DSL
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    channel notification_channel NOT NULL,
    template_id TEXT,
    segment_id UUID REFERENCES segments(id) ON DELETE SET NULL,
    status campaign_status DEFAULT 'draft',
    sent_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    channel notification_channel NOT NULL,
    title TEXT,
    body TEXT NOT NULL,
    data JSONB DEFAULT '{}',
    status notification_status DEFAULT 'queued',
    provider_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    sent_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Compliance and audit
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    action TEXT NOT NULL,
    entity_table TEXT NOT NULL,
    entity_id UUID NOT NULL,
    diff JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE consents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    kind consent_kind NOT NULL,
    granted BOOLEAN NOT NULL,
    granted_at TIMESTAMPTZ,
    method TEXT, -- How consent was given (web_form, verbal, etc)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(patient_id, kind)
);

-- Indexes for performance
CREATE INDEX idx_patients_org_id ON patients(org_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_patients_owner ON patients(owner_user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_patients_tags ON patients USING GIN(tags);
CREATE INDEX idx_protocols_patient ON protocols(patient_id);
CREATE INDEX idx_protocol_sessions_protocol ON protocol_sessions(protocol_id);
CREATE INDEX idx_analyses_patient ON analyses(patient_id);
CREATE INDEX idx_analyses_kind ON analyses(kind);
CREATE INDEX idx_appointments_patient ON appointments(patient_id);
CREATE INDEX idx_appointments_org_starts ON appointments(org_id, starts_at);
CREATE INDEX idx_messages_thread ON messages(thread_id);
CREATE INDEX idx_notifications_patient_status ON notifications(patient_id, status);
CREATE INDEX idx_audit_logs_org_created ON audit_logs(org_id, created_at);
CREATE INDEX idx_longevity_scores_patient ON longevity_scores(patient_id);

-- GIN indexes for JSONB fields
CREATE INDEX idx_analyses_metrics ON analyses USING GIN(metrics);
CREATE INDEX idx_protocols_goals ON protocols USING GIN(goals);
CREATE INDEX idx_segments_definition ON segments USING GIN(definition);

-- Triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers to relevant tables
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_patients_updated_at BEFORE UPDATE ON patients FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_protocols_updated_at BEFORE UPDATE ON protocols FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_protocol_sessions_updated_at BEFORE UPDATE ON protocol_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_analyses_updated_at BEFORE UPDATE ON analyses FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_formulas_updated_at BEFORE UPDATE ON formulas FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_appointments_updated_at BEFORE UPDATE ON appointments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_messages_updated_at BEFORE UPDATE ON messages FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();