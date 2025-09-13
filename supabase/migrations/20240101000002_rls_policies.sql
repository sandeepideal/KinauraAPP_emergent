-- Row Level Security (RLS) Policies for KinAura
-- This implements comprehensive security policies for multi-tenant access control

-- Enable RLS on all tables
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinicians ENABLE ROW LEVEL SECURITY;
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE patient_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE patient_group_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE patient_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE membership_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE protocols ENABLE ROW LEVEL SECURITY;
ALTER TABLE protocol_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE prepost_sets ENABLE ROW LEVEL SECURITY;
ALTER TABLE longevity_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE formulas ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE services ENABLE ROW LEVEL SECURITY;
ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE segments ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE consents ENABLE ROW LEVEL SECURITY;

-- Helper functions for RLS
CREATE OR REPLACE FUNCTION get_user_org_id() RETURNS UUID AS $$
BEGIN
    RETURN (SELECT org_id FROM profiles WHERE id = auth.uid());
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION get_user_role() RETURNS user_role AS $$
BEGIN
    RETURN (SELECT role FROM profiles WHERE id = auth.uid());
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION is_admin_or_practitioner() RETURNS BOOLEAN AS $$
BEGIN
    RETURN get_user_role() IN ('admin', 'practitioner');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION get_patient_id_from_profile() RETURNS UUID AS $$
BEGIN
    RETURN (SELECT p.id FROM patients p 
            JOIN profiles pr ON pr.id = auth.uid() 
            WHERE p.email = (SELECT raw_user_meta_data->>'email' FROM auth.users WHERE id = auth.uid())
            AND p.org_id = get_user_org_id());
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Organizations: Admin access only
CREATE POLICY "Organizations admin access" ON organizations
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM profiles 
            WHERE id = auth.uid() 
            AND org_id = organizations.id 
            AND role = 'admin'
        )
    );

-- Profiles: Users can read/update their own profile, admins can manage all
CREATE POLICY "Profiles self access" ON profiles
    FOR ALL USING (id = auth.uid());

CREATE POLICY "Profiles admin access" ON profiles
    FOR ALL USING (
        get_user_role() = 'admin' AND org_id = get_user_org_id()
    );

-- Clinicians: Admin and practitioner access within org
CREATE POLICY "Clinicians org access" ON clinicians
    FOR ALL USING (
        org_id = get_user_org_id() AND is_admin_or_practitioner()
    );

-- Patients: Admin/practitioners can access all in org, members can access own data
CREATE POLICY "Patients staff access" ON patients
    FOR ALL USING (
        org_id = get_user_org_id() AND is_admin_or_practitioner()
    );

CREATE POLICY "Patients self access" ON patients
    FOR SELECT USING (
        id = get_patient_id_from_profile() OR 
        (org_id = get_user_org_id() AND is_admin_or_practitioner())
    );

-- Patient Groups: Admin/practitioner access
CREATE POLICY "Patient groups staff access" ON patient_groups
    FOR ALL USING (
        org_id = get_user_org_id() AND is_admin_or_practitioner()
    );

CREATE POLICY "Patient group members staff access" ON patient_group_members
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM patient_groups pg 
            WHERE pg.id = group_id 
            AND pg.org_id = get_user_org_id() 
            AND is_admin_or_practitioner()
        )
    );

-- Patient Notes: Based on visibility and roles
CREATE POLICY "Patient notes staff access" ON patient_notes
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM patients p 
            WHERE p.id = patient_id 
            AND p.org_id = get_user_org_id() 
            AND is_admin_or_practitioner()
        )
    );

-- Membership Plans: Org-scoped for staff
CREATE POLICY "Membership plans org access" ON membership_plans
    FOR ALL USING (
        org_id = get_user_org_id() AND is_admin_or_practitioner()
    );

-- Memberships: Staff can manage, patients can view own
CREATE POLICY "Memberships staff access" ON memberships
    FOR ALL USING (
        org_id = get_user_org_id() AND is_admin_or_practitioner()
    );

CREATE POLICY "Memberships patient self access" ON memberships
    FOR SELECT USING (
        patient_id = get_patient_id_from_profile()
    );

-- Protocols: Staff can manage, patients can view own
CREATE POLICY "Protocols staff access" ON protocols
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM patients p 
            WHERE p.id = patient_id 
            AND p.org_id = get_user_org_id() 
            AND is_admin_or_practitioner()
        )
    );

CREATE POLICY "Protocols patient access" ON protocols
    FOR SELECT USING (
        patient_id = get_patient_id_from_profile()
    );

-- Protocol Sessions: Same as protocols
CREATE POLICY "Protocol sessions staff access" ON protocol_sessions
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM protocols pr 
            JOIN patients p ON p.id = pr.patient_id 
            WHERE pr.id = protocol_id 
            AND p.org_id = get_user_org_id() 
            AND is_admin_or_practitioner()
        )
    );

CREATE POLICY "Protocol sessions patient access" ON protocol_sessions
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM protocols pr 
            WHERE pr.id = protocol_id 
            AND pr.patient_id = get_patient_id_from_profile()
        )
    );

-- Analyses: Staff can manage, patients can view own
CREATE POLICY "Analyses staff access" ON analyses
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM patients p 
            WHERE p.id = patient_id 
            AND p.org_id = get_user_org_id() 
            AND is_admin_or_practitioner()
        )
    );

CREATE POLICY "Analyses patient access" ON analyses
    FOR SELECT USING (
        patient_id = get_patient_id_from_profile()
    );

-- Pre/Post Sets: Same pattern
CREATE POLICY "Prepost sets staff access" ON prepost_sets
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM patients p 
            WHERE p.id = patient_id 
            AND p.org_id = get_user_org_id() 
            AND is_admin_or_practitioner()
        )
    );

CREATE POLICY "Prepost sets patient access" ON prepost_sets
    FOR SELECT USING (
        patient_id = get_patient_id_from_profile()
    );

-- Longevity Scores: Patient can read own, staff can manage
CREATE POLICY "Longevity scores staff access" ON longevity_scores
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM patients p 
            WHERE p.id = patient_id 
            AND p.org_id = get_user_org_id() 
            AND is_admin_or_practitioner()
        )
    );

CREATE POLICY "Longevity scores patient access" ON longevity_scores
    FOR SELECT USING (
        patient_id = get_patient_id_from_profile()
    );

-- Formulas: Patient can read own, staff can manage
CREATE POLICY "Formulas staff access" ON formulas
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM patients p 
            WHERE p.id = patient_id 
            AND p.org_id = get_user_org_id() 
            AND is_admin_or_practitioner()
        )
    );

CREATE POLICY "Formulas patient access" ON formulas
    FOR SELECT USING (
        patient_id = get_patient_id_from_profile()
    );

-- Orders: Same pattern
CREATE POLICY "Orders staff access" ON orders
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM patients p 
            WHERE p.id = patient_id 
            AND p.org_id = get_user_org_id() 
            AND is_admin_or_practitioner()
        )
    );

CREATE POLICY "Orders patient access" ON orders
    FOR SELECT USING (
        patient_id = get_patient_id_from_profile()
    );

-- Services: Org-scoped, all can read active services
CREATE POLICY "Services org access" ON services
    FOR ALL USING (
        org_id = get_user_org_id() AND is_admin_or_practitioner()
    );

CREATE POLICY "Services public read" ON services
    FOR SELECT USING (
        org_id = get_user_org_id() AND is_active = true
    );

-- Appointments: Staff can manage, patients can view/create own
CREATE POLICY "Appointments staff access" ON appointments
    FOR ALL USING (
        org_id = get_user_org_id() AND is_admin_or_practitioner()
    );

CREATE POLICY "Appointments patient access" ON appointments
    FOR SELECT USING (
        patient_id = get_patient_id_from_profile()
    );

CREATE POLICY "Appointments patient create" ON appointments
    FOR INSERT WITH CHECK (
        patient_id = get_patient_id_from_profile() AND 
        org_id = get_user_org_id()
    );

-- Threads: Patients can access own threads, staff can access threads for their org patients
CREATE POLICY "Threads staff access" ON threads
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM patients p 
            WHERE p.id = patient_id 
            AND p.org_id = get_user_org_id() 
            AND is_admin_or_practitioner()
        )
    );

CREATE POLICY "Threads patient access" ON threads
    FOR ALL USING (
        patient_id = get_patient_id_from_profile()
    );

-- Messages: Access based on thread access
CREATE POLICY "Messages thread access" ON messages
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM threads t 
            WHERE t.id = thread_id 
            AND (
                t.patient_id = get_patient_id_from_profile() OR
                (EXISTS (
                    SELECT 1 FROM patients p 
                    WHERE p.id = t.patient_id 
                    AND p.org_id = get_user_org_id() 
                    AND is_admin_or_practitioner()
                ))
            )
        )
    );

-- Segments: Admin only
CREATE POLICY "Segments admin access" ON segments
    FOR ALL USING (
        org_id = get_user_org_id() AND get_user_role() = 'admin'
    );

-- Campaigns: Admin only
CREATE POLICY "Campaigns admin access" ON campaigns
    FOR ALL USING (
        org_id = get_user_org_id() AND get_user_role() = 'admin'
    );

-- Notifications: Patients can read own, staff can manage
CREATE POLICY "Notifications patient access" ON notifications
    FOR SELECT USING (
        patient_id = get_patient_id_from_profile()
    );

CREATE POLICY "Notifications staff access" ON notifications
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM patients p 
            WHERE p.id = patient_id 
            AND p.org_id = get_user_org_id() 
            AND is_admin_or_practitioner()
        )
    );

-- Audit Logs: Admin read only
CREATE POLICY "Audit logs admin access" ON audit_logs
    FOR SELECT USING (
        org_id = get_user_org_id() AND get_user_role() = 'admin'
    );

-- Consents: Patients can manage own, staff can view
CREATE POLICY "Consents patient access" ON consents
    FOR ALL USING (
        patient_id = get_patient_id_from_profile()
    );

CREATE POLICY "Consents staff read" ON consents
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM patients p 
            WHERE p.id = patient_id 
            AND p.org_id = get_user_org_id() 
            AND is_admin_or_practitioner()
        )
    );