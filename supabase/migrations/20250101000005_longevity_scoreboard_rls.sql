-- Row Level Security Policies for Longevity Scoreboard
-- This implements strict security for all longevity scoreboard tables

-- Enable RLS on all new tables
ALTER TABLE biological_ages ENABLE ROW LEVEL SECURITY;
ALTER TABLE longevity_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE cohorts ENABLE ROW LEVEL SECURITY;
ALTER TABLE leaderboard_visibility ENABLE ROW LEVEL SECURITY;
ALTER TABLE score_constants ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- BIOLOGICAL_AGES POLICIES
-- =====================================================

-- Admin/practitioners can manage all biological ages in their org
CREATE POLICY "biological_ages_admin_access" ON biological_ages
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM patients p
            JOIN profiles pr ON pr.org_id = p.org_id
            WHERE p.id = patient_id
            AND pr.id = auth.uid()
            AND pr.role IN ('admin', 'practitioner')
        )
    );

-- Patients can read their own biological ages
CREATE POLICY "biological_ages_patient_read" ON biological_ages
    FOR SELECT USING (
        patient_id = (
            SELECT p.id FROM patients p
            JOIN profiles pr ON pr.id = auth.uid()
            WHERE p.email = (SELECT raw_user_meta_data->>'email' FROM auth.users WHERE id = auth.uid())
            AND p.org_id = pr.org_id
        )
    );

-- =====================================================
-- LONGEVITY_SCORES POLICIES
-- =====================================================

-- Admin/practitioners can access all longevity scores in their org
CREATE POLICY "longevity_scores_staff_access" ON longevity_scores
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM patients p
            JOIN profiles pr ON pr.org_id = p.org_id
            WHERE p.id = patient_id
            AND pr.id = auth.uid()
            AND pr.role IN ('admin', 'practitioner')
        )
    );

-- Patients can read their own longevity scores
CREATE POLICY "longevity_scores_patient_read" ON longevity_scores
    FOR SELECT USING (
        patient_id = (
            SELECT p.id FROM patients p
            JOIN profiles pr ON pr.id = auth.uid()
            WHERE p.email = (SELECT raw_user_meta_data->>'email' FROM auth.users WHERE id = auth.uid())
            AND p.org_id = pr.org_id
        )
    );

-- System can insert/update scores (for compute functions)
CREATE POLICY "longevity_scores_system_write" ON longevity_scores
    FOR INSERT WITH CHECK (true);

CREATE POLICY "longevity_scores_system_update" ON longevity_scores
    FOR UPDATE USING (true);

-- =====================================================
-- COHORTS POLICIES
-- =====================================================

-- Admin/practitioners can manage cohorts in their org
CREATE POLICY "cohorts_staff_access" ON cohorts
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM profiles pr
            WHERE pr.id = auth.uid()
            AND pr.org_id = org_id
            AND pr.role IN ('admin', 'practitioner')
        )
    );

-- Anyone can read cohorts (for leaderboard display)
CREATE POLICY "cohorts_public_read" ON cohorts
    FOR SELECT USING (true);

-- =====================================================
-- LEADERBOARD_VISIBILITY POLICIES
-- =====================================================

-- Admin/practitioners can manage visibility settings in their org
CREATE POLICY "leaderboard_visibility_admin_access" ON leaderboard_visibility
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM patients p
            JOIN profiles pr ON pr.org_id = p.org_id
            WHERE p.id = patient_id
            AND pr.id = auth.uid()
            AND pr.role IN ('admin', 'practitioner')
        )
    );

-- Patients can manage their own visibility settings
CREATE POLICY "leaderboard_visibility_patient_access" ON leaderboard_visibility
    FOR ALL USING (
        patient_id = (
            SELECT p.id FROM patients p
            JOIN profiles pr ON pr.id = auth.uid()
            WHERE p.email = (SELECT raw_user_meta_data->>'email' FROM auth.users WHERE id = auth.uid())
            AND p.org_id = pr.org_id
        )
    );

-- =====================================================
-- SCORE_CONSTANTS POLICIES
-- =====================================================

-- Only admins can modify score constants
CREATE POLICY "score_constants_admin_write" ON score_constants
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM profiles pr
            WHERE pr.id = auth.uid()
            AND pr.role = 'admin'
        )
    );

-- Anyone can read score constants (needed for score computation)
CREATE POLICY "score_constants_public_read" ON score_constants
    FOR SELECT USING (true);

-- =====================================================
-- SECURITY FUNCTIONS FOR VIEWS
-- =====================================================

-- Create security function to check if user can see patient data
CREATE OR REPLACE FUNCTION can_access_patient_data(target_patient_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    -- Admin/practitioner in same org
    IF EXISTS (
        SELECT 1 FROM patients p
        JOIN profiles pr ON pr.org_id = p.org_id
        WHERE p.id = target_patient_id
        AND pr.id = auth.uid()
        AND pr.role IN ('admin', 'practitioner')
    ) THEN
        RETURN TRUE;
    END IF;
    
    -- Patient accessing own data
    IF target_patient_id = (
        SELECT p.id FROM patients p
        JOIN profiles pr ON pr.id = auth.uid()
        WHERE p.email = (SELECT raw_user_meta_data->>'email' FROM auth.users WHERE id = auth.uid())
        AND p.org_id = pr.org_id
    ) THEN
        RETURN TRUE;
    END IF;
    
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to check leaderboard visibility
CREATE OR REPLACE FUNCTION is_patient_visible_on_leaderboard(target_patient_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    patient_org UUID;
    is_opted_in BOOLEAN := FALSE;
BEGIN
    -- Get patient org
    SELECT org_id INTO patient_org FROM patients WHERE id = target_patient_id;
    
    -- Check visibility settings
    SELECT COALESCE(
        (SELECT lv.opt_in FROM leaderboard_visibility lv WHERE lv.patient_id = target_patient_id),
        (SELECT pr.publish_on_leaderboard FROM profiles pr WHERE pr.org_id = patient_org AND pr.id = auth.uid()),
        FALSE
    ) INTO is_opted_in;
    
    RETURN is_opted_in;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- REALTIME PUBLICATION
-- =====================================================

-- Create publication for realtime updates
CREATE PUBLICATION longevity_scoreboard_updates FOR TABLE 
    longevity_scores,
    biological_ages,
    leaderboard_visibility;

-- =====================================================
-- HELPER FUNCTIONS FOR EDGE FUNCTIONS
-- =====================================================

-- Function to safely get patient scores (respects RLS)
CREATE OR REPLACE FUNCTION get_patient_score_data(target_patient_id UUID)
RETURNS TABLE(
    patient_id UUID,
    chronological_age_years NUMERIC,
    biological_age_years NUMERIC,
    delta_years NUMERIC,
    score NUMERIC,
    cohort_key TEXT,
    rank BIGINT,
    total_in_cohort BIGINT,
    computed_at TIMESTAMPTZ
) 
SECURITY DEFINER
AS $$
BEGIN
    -- Check access permission
    IF NOT can_access_patient_data(target_patient_id) THEN
        RAISE EXCEPTION 'Access denied to patient data';
    END IF;
    
    RETURN QUERY
    SELECT 
        ls.patient_id,
        ls.chronological_age_years,
        ls.biological_age_years,
        ls.delta_years,
        ls.score,
        ls.cohort_key,
        vcr.rank,
        vcr.total_in_cohort,
        ls.computed_at
    FROM longevity_scores ls
    JOIN v_cohort_ranking vcr ON vcr.patient_id = ls.patient_id
    WHERE ls.patient_id = target_patient_id
    ORDER BY ls.computed_at DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Function to get public leaderboard data (with pagination)
CREATE OR REPLACE FUNCTION get_public_leaderboard_data(
    target_cohort_key TEXT DEFAULT NULL,
    page_num INTEGER DEFAULT 1,
    page_size INTEGER DEFAULT 25,
    target_org_id UUID DEFAULT NULL
)
RETURNS TABLE(
    rank BIGINT,
    score NUMERIC,
    display JSONB,
    cohort_key TEXT,
    total_entries BIGINT,
    pinned BOOLEAN
)
SECURITY DEFINER
AS $$
DECLARE
    offset_count INTEGER;
BEGIN
    -- Calculate offset
    offset_count := (page_num - 1) * page_size;
    
    RETURN QUERY
    SELECT 
        vpl.rank,
        vpl.score,
        vpl.display,
        vpl.cohort_key,
        COUNT(*) OVER() as total_entries,
        vpl.pinned
    FROM v_public_leaderboard vpl
    WHERE 
        (target_cohort_key IS NULL OR vpl.cohort_key = target_cohort_key)
        AND (target_org_id IS NULL OR vpl.org_id = target_org_id)
    ORDER BY 
        vpl.pinned DESC, -- Pinned entries first
        vpl.rank ASC
    LIMIT page_size
    OFFSET offset_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get available cohorts for an org
CREATE OR REPLACE FUNCTION get_org_cohorts(target_org_id UUID)
RETURNS TABLE(
    cohort_key TEXT,
    patient_count BIGINT,
    avg_score NUMERIC,
    description TEXT
)
SECURITY DEFINER
AS $$
BEGIN
    -- Check if user has access to org
    IF NOT EXISTS (
        SELECT 1 FROM profiles pr
        WHERE pr.id = auth.uid()
        AND (pr.org_id = target_org_id OR pr.role = 'admin')
    ) THEN
        RAISE EXCEPTION 'Access denied to organization data';
    END IF;
    
    RETURN QUERY
    SELECT 
        ls.cohort_key,
        COUNT(*)::BIGINT as patient_count,
        ROUND(AVG(ls.score), 2) as avg_score,
        CASE 
            WHEN ls.cohort_key LIKE '%age:18-29%' THEN 'Young Adults (18-29)'
            WHEN ls.cohort_key LIKE '%age:30-39%' THEN 'Adults (30-39)'
            WHEN ls.cohort_key LIKE '%age:40-49%' THEN 'Middle-aged (40-49)'
            WHEN ls.cohort_key LIKE '%age:50-59%' THEN 'Mature Adults (50-59)'
            WHEN ls.cohort_key LIKE '%age:60+%' THEN 'Seniors (60+)'
            ELSE 'Other'
        END as description
    FROM longevity_scores ls
    JOIN patients p ON p.id = ls.patient_id
    WHERE p.org_id = target_org_id
    GROUP BY ls.cohort_key
    ORDER BY patient_count DESC;
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON FUNCTION can_access_patient_data IS 'Security function to check patient data access permissions';
COMMENT ON FUNCTION is_patient_visible_on_leaderboard IS 'Checks if patient has opted into leaderboard visibility';
COMMENT ON FUNCTION get_patient_score_data IS 'Safely retrieves patient score data respecting RLS';
COMMENT ON FUNCTION get_public_leaderboard_data IS 'Retrieves paginated public leaderboard data';
COMMENT ON FUNCTION get_org_cohorts IS 'Gets available cohorts and statistics for an organization';