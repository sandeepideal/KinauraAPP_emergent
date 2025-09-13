-- Longevity Scoreboard Schema Migration
-- This creates the complete data model for patient longevity scoring and ranking

-- First, extend the existing profiles table with longevity scoreboard fields
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS display_avatar_url TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS publish_on_leaderboard BOOLEAN DEFAULT FALSE;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS publish_identity TEXT DEFAULT 'avatar' CHECK (publish_identity IN ('name', 'avatar', 'anonymous'));
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS public_handle TEXT UNIQUE;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS dob DATE;

-- Add comment for clarity
COMMENT ON COLUMN profiles.display_avatar_url IS 'Storage path for patient avatar in private bucket';
COMMENT ON COLUMN profiles.publish_on_leaderboard IS 'Explicit opt-in for appearing on leaderboard';
COMMENT ON COLUMN profiles.publish_identity IS 'How patient identity appears on leaderboard';
COMMENT ON COLUMN profiles.public_handle IS 'Optional handle for anonymous mode';

-- Create biological_ages table for storing different types of biological age measurements
CREATE TABLE biological_ages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    method TEXT NOT NULL CHECK (method IN ('blood', 'saliva', 'epigenetic', 'device', 'composite')),
    biological_age_years NUMERIC(5,2) NOT NULL CHECK (biological_age_years > 0 AND biological_age_years < 150),
    measured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source JSONB DEFAULT '{}', -- metadata: device, lab, file references
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create partial index for fast lookups of latest biological age per patient
CREATE INDEX idx_biological_ages_patient_recent ON biological_ages(patient_id, measured_at DESC);
CREATE INDEX idx_biological_ages_method ON biological_ages(method);

-- Create longevity_scores table for computed scores and rankings
CREATE TABLE longevity_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    chronological_age_years NUMERIC(5,2) NOT NULL CHECK (chronological_age_years > 0 AND chronological_age_years < 150),
    biological_age_years NUMERIC(5,2) NOT NULL CHECK (biological_age_years > 0 AND biological_age_years < 150),
    delta_years NUMERIC(5,2) NOT NULL, -- chronological - biological (positive = younger biologically)
    score NUMERIC(5,2) NOT NULL CHECK (score >= 0 AND score <= 100),
    cohort_key TEXT NOT NULL, -- e.g., 'age:30-39|gender:f|org:UUID'
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Ensure only one current score per patient
    UNIQUE(patient_id, computed_at)
);

-- Create indexes for fast ranking and filtering
CREATE INDEX idx_longevity_scores_patient ON longevity_scores(patient_id);
CREATE INDEX idx_longevity_scores_cohort_score ON longevity_scores(cohort_key, score DESC, computed_at DESC);
CREATE INDEX idx_longevity_scores_computed_at ON longevity_scores(computed_at DESC);

-- Create cohorts helper table for managing cohort definitions
CREATE TABLE cohorts (
    key TEXT PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    definition JSONB NOT NULL DEFAULT '{}', -- age band, gender, membership tier, etc.
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create leaderboard_visibility table for per-patient overrides
CREATE TABLE leaderboard_visibility (
    patient_id UUID PRIMARY KEY REFERENCES patients(id) ON DELETE CASCADE,
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    opt_in BOOLEAN DEFAULT FALSE,
    identity TEXT DEFAULT 'avatar' CHECK (identity IN ('name', 'avatar', 'anonymous')),
    pinned BOOLEAN DEFAULT FALSE, -- admins can pin featured entries
    pinned_by UUID REFERENCES profiles(id) ON DELETE SET NULL,
    pinned_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create score_constants table for configurable scoring parameters
CREATE TABLE score_constants (
    key TEXT PRIMARY KEY,
    value NUMERIC(10,4) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Insert default scoring constants
INSERT INTO score_constants (key, value, description) VALUES
('base_score', 50.0, 'Base score when delta is 0'),
('delta_multiplier', 5.0, 'Points per year of biological age advantage'),
('min_score', 0.0, 'Minimum possible score'),
('max_score', 100.0, 'Maximum possible score');

-- Create scoring function
CREATE OR REPLACE FUNCTION fn_longevity_score(delta_years NUMERIC)
RETURNS NUMERIC AS $$
DECLARE
    base_score NUMERIC;
    multiplier NUMERIC;
    min_score NUMERIC;
    max_score NUMERIC;
    computed_score NUMERIC;
BEGIN
    -- Get scoring constants
    SELECT value INTO base_score FROM score_constants WHERE key = 'base_score';
    SELECT value INTO multiplier FROM score_constants WHERE key = 'delta_multiplier';
    SELECT value INTO min_score FROM score_constants WHERE key = 'min_score';
    SELECT value INTO max_score FROM score_constants WHERE key = 'max_score';
    
    -- Compute score: base + (delta * multiplier)
    computed_score := base_score + (delta_years * multiplier);
    
    -- Clamp to min/max bounds
    RETURN GREATEST(min_score, LEAST(max_score, computed_score));
END;
$$ LANGUAGE plpgsql STABLE;

-- Create cohort key generation function
CREATE OR REPLACE FUNCTION fn_cohort_key(patient_id_param UUID, org_id_param UUID)
RETURNS TEXT AS $$
DECLARE
    patient_record RECORD;
    age_band TEXT;
    gender_part TEXT;
    cohort_key TEXT;
BEGIN
    -- Get patient info with calculated age
    SELECT 
        p.gender,
        COALESCE(pr.dob, p.dob) as dob,
        EXTRACT(YEAR FROM AGE(COALESCE(pr.dob, p.dob)))::INTEGER as age
    INTO patient_record
    FROM patients p
    LEFT JOIN profiles pr ON pr.id = (SELECT id FROM profiles WHERE id = auth.uid() AND org_id = p.org_id)
    WHERE p.id = patient_id_param;
    
    -- Determine age band
    CASE 
        WHEN patient_record.age < 30 THEN age_band := '18-29';
        WHEN patient_record.age < 40 THEN age_band := '30-39';
        WHEN patient_record.age < 50 THEN age_band := '40-49';
        WHEN patient_record.age < 60 THEN age_band := '50-59';
        ELSE age_band := '60+';
    END CASE;
    
    -- Build gender part
    gender_part := COALESCE(
        CASE patient_record.gender
            WHEN 'male' THEN 'gender:m'
            WHEN 'female' THEN 'gender:f'
            ELSE 'gender:other'
        END,
        'gender:unknown'
    );
    
    -- Build cohort key
    cohort_key := 'age:' || age_band || '|' || gender_part || '|org:' || org_id_param;
    
    RETURN cohort_key;
END;
$$ LANGUAGE plpgsql STABLE;

-- Create patient score computation function
CREATE OR REPLACE FUNCTION fn_compute_patient_score(patient_id_param UUID)
RETURNS TABLE(
    patient_id UUID,
    chronological_age_years NUMERIC,
    biological_age_years NUMERIC,
    delta_years NUMERIC,
    score NUMERIC,
    cohort_key TEXT
) AS $$
DECLARE
    patient_record RECORD;
    latest_bio_age RECORD;
    computed_delta NUMERIC;
    computed_score NUMERIC;
    computed_cohort_key TEXT;
    computed_chrono_age NUMERIC;
BEGIN
    -- Get patient info
    SELECT p.*, pr.dob as profile_dob
    INTO patient_record
    FROM patients p
    LEFT JOIN profiles pr ON pr.id = (
        SELECT id FROM profiles 
        WHERE id = auth.uid() AND org_id = p.org_id
    )
    WHERE p.id = patient_id_param;
    
    IF patient_record IS NULL THEN
        RAISE EXCEPTION 'Patient not found: %', patient_id_param;
    END IF;
    
    -- Get latest biological age
    SELECT ba.biological_age_years, ba.measured_at
    INTO latest_bio_age
    FROM biological_ages ba
    WHERE ba.patient_id = patient_id_param
    ORDER BY ba.measured_at DESC
    LIMIT 1;
    
    IF latest_bio_age IS NULL THEN
        RAISE EXCEPTION 'No biological age measurement found for patient: %', patient_id_param;
    END IF;
    
    -- Calculate chronological age at measurement time
    computed_chrono_age := EXTRACT(
        EPOCH FROM (latest_bio_age.measured_at - COALESCE(patient_record.profile_dob, patient_record.dob))
    ) / (365.25 * 24 * 3600);
    
    -- Calculate delta (positive means biologically younger)
    computed_delta := computed_chrono_age - latest_bio_age.biological_age_years;
    
    -- Calculate score
    computed_score := fn_longevity_score(computed_delta);
    
    -- Generate cohort key
    computed_cohort_key := fn_cohort_key(patient_id_param, patient_record.org_id);
    
    -- Return computed values
    RETURN QUERY SELECT 
        patient_id_param,
        computed_chrono_age,
        latest_bio_age.biological_age_years,
        computed_delta,
        computed_score,
        computed_cohort_key;
END;
$$ LANGUAGE plpgsql;

-- Create view for cohort rankings
CREATE OR REPLACE VIEW v_cohort_ranking AS
SELECT 
    ls.patient_id,
    p.org_id,
    ls.cohort_key,
    ls.score,
    ls.computed_at,
    RANK() OVER (
        PARTITION BY ls.cohort_key 
        ORDER BY ls.score DESC, ls.computed_at DESC
    ) as rank,
    COUNT(*) OVER (PARTITION BY ls.cohort_key) as total_in_cohort
FROM longevity_scores ls
JOIN patients p ON p.id = ls.patient_id
WHERE p.deleted_at IS NULL;

-- Create view for public leaderboard
CREATE OR REPLACE VIEW v_public_leaderboard AS
SELECT 
    vcr.rank,
    vcr.score,
    vcr.cohort_key,
    vcr.org_id,
    vcr.computed_at,
    vcr.total_in_cohort,
    -- Display fields based on privacy settings
    CASE 
        WHEN COALESCE(lv.identity, pr.publish_identity, 'avatar') = 'name' 
        THEN jsonb_build_object(
            'mode', 'name',
            'name', COALESCE(SPLIT_PART(p.full_name, ' ', 1) || ' ' || LEFT(SPLIT_PART(p.full_name, ' ', 2), 1) || '.', 'Anonymous')
        )
        WHEN COALESCE(lv.identity, pr.publish_identity, 'avatar') = 'avatar'
        THEN jsonb_build_object(
            'mode', 'avatar',
            'avatar_url', pr.display_avatar_url,
            'name', COALESCE(SPLIT_PART(p.full_name, ' ', 1), 'Anonymous')
        )
        ELSE jsonb_build_object(
            'mode', 'anonymous',
            'handle', COALESCE(pr.public_handle, 'Anonymous_' || RIGHT(vcr.patient_id::TEXT, 4))
        )
    END as display,
    -- Admin fields (for admin queries)
    p.full_name,
    vcr.patient_id,
    COALESCE(lv.pinned, FALSE) as pinned
FROM v_cohort_ranking vcr
JOIN patients p ON p.id = vcr.patient_id
LEFT JOIN profiles pr ON pr.id = (
    SELECT id FROM profiles 
    WHERE org_id = p.org_id 
    AND id = auth.uid()
)
LEFT JOIN leaderboard_visibility lv ON lv.patient_id = vcr.patient_id
WHERE 
    -- Only show opted-in patients
    (COALESCE(lv.opt_in, pr.publish_on_leaderboard, FALSE) = TRUE)
    -- Only show non-deleted patients
    AND p.deleted_at IS NULL;

-- Create function to get patient neighbors on leaderboard
CREATE OR REPLACE FUNCTION fn_get_patient_neighbors(
    patient_id_param UUID,
    neighbor_count INTEGER DEFAULT 3
)
RETURNS TABLE(
    rank BIGINT,
    score NUMERIC,
    display JSONB,
    is_current_patient BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    WITH patient_rank AS (
        SELECT vcr.rank, vcr.cohort_key
        FROM v_cohort_ranking vcr
        WHERE vcr.patient_id = patient_id_param
    ),
    neighbors AS (
        SELECT 
            vpl.rank,
            vpl.score,
            vpl.display,
            (vpl.patient_id = patient_id_param) as is_current_patient
        FROM v_public_leaderboard vpl
        CROSS JOIN patient_rank pr
        WHERE vpl.cohort_key = pr.cohort_key
        AND vpl.rank BETWEEN (pr.rank - neighbor_count) AND (pr.rank + neighbor_count)
        ORDER BY vpl.rank
    )
    SELECT n.rank, n.score, n.display, n.is_current_patient
    FROM neighbors n;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create updated_at triggers for all tables
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers
CREATE TRIGGER update_biological_ages_updated_at BEFORE UPDATE ON biological_ages FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_longevity_scores_updated_at BEFORE UPDATE ON longevity_scores FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_cohorts_updated_at BEFORE UPDATE ON cohorts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_leaderboard_visibility_updated_at BEFORE UPDATE ON leaderboard_visibility FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_score_constants_updated_at BEFORE UPDATE ON score_constants FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function to upsert patient score (used by compute jobs)
CREATE OR REPLACE FUNCTION fn_upsert_patient_score(patient_id_param UUID)
RETURNS longevity_scores AS $$
DECLARE
    computed_data RECORD;
    result_record longevity_scores;
BEGIN
    -- Get computed score data
    SELECT * INTO computed_data
    FROM fn_compute_patient_score(patient_id_param)
    LIMIT 1;
    
    -- Upsert into longevity_scores
    INSERT INTO longevity_scores (
        patient_id,
        chronological_age_years,
        biological_age_years,
        delta_years,
        score,
        cohort_key,
        computed_at
    ) VALUES (
        computed_data.patient_id,
        computed_data.chronological_age_years,
        computed_data.biological_age_years,
        computed_data.delta_years,
        computed_data.score,
        computed_data.cohort_key,
        NOW()
    )
    ON CONFLICT (patient_id, computed_at) DO UPDATE SET
        chronological_age_years = EXCLUDED.chronological_age_years,
        biological_age_years = EXCLUDED.biological_age_years,
        delta_years = EXCLUDED.delta_years,
        score = EXCLUDED.score,
        cohort_key = EXCLUDED.cohort_key,
        updated_at = NOW()
    RETURNING * INTO result_record;
    
    RETURN result_record;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Add comments for documentation
COMMENT ON TABLE biological_ages IS 'Stores biological age measurements from various methods';
COMMENT ON TABLE longevity_scores IS 'Computed longevity scores with cohort rankings';
COMMENT ON TABLE cohorts IS 'Cohort definitions for grouping patients';
COMMENT ON TABLE leaderboard_visibility IS 'Per-patient visibility and identity settings';
COMMENT ON TABLE score_constants IS 'Configurable parameters for score computation';
COMMENT ON VIEW v_cohort_ranking IS 'Ranked patients by cohort with scores';
COMMENT ON VIEW v_public_leaderboard IS 'Public leaderboard respecting privacy settings';
COMMENT ON FUNCTION fn_longevity_score IS 'Computes 0-100 score from age delta';
COMMENT ON FUNCTION fn_cohort_key IS 'Generates cohort key from patient demographics';
COMMENT ON FUNCTION fn_compute_patient_score IS 'Computes all score components for a patient';