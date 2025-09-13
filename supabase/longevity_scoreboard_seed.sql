-- Comprehensive seed data for Longevity Scoreboard
-- This populates all tables with realistic test data

-- First, ensure we have extended profiles with DOB data for existing patients
UPDATE profiles SET 
  dob = CASE 
    WHEN id = (SELECT id FROM profiles WHERE full_name ILIKE '%Elena%' LIMIT 1) THEN '1985-03-15'
    WHEN id = (SELECT id FROM profiles WHERE full_name ILIKE '%Francesco%' LIMIT 1) THEN '1978-07-22'
    WHEN id = (SELECT id FROM profiles WHERE full_name ILIKE '%Giulia%' LIMIT 1) THEN '1992-11-08'
    WHEN id = (SELECT id FROM profiles WHERE full_name ILIKE '%Marco%' LIMIT 1) THEN '1980-05-12'
    WHEN id = (SELECT id FROM profiles WHERE full_name ILIKE '%Sofia%' LIMIT 1) THEN '1988-09-30'
    ELSE dob
  END,
  publish_on_leaderboard = CASE 
    WHEN id = (SELECT id FROM profiles WHERE full_name ILIKE '%Elena%' LIMIT 1) THEN true
    WHEN id = (SELECT id FROM profiles WHERE full_name ILIKE '%Francesco%' LIMIT 1) THEN true
    WHEN id = (SELECT id FROM profiles WHERE full_name ILIKE '%Giulia%' LIMIT 1) THEN true
    ELSE false
  END,
  publish_identity = CASE 
    WHEN id = (SELECT id FROM profiles WHERE full_name ILIKE '%Elena%' LIMIT 1) THEN 'avatar'
    WHEN id = (SELECT id FROM profiles WHERE full_name ILIKE '%Francesco%' LIMIT 1) THEN 'name'
    WHEN id = (SELECT id FROM profiles WHERE full_name ILIKE '%Giulia%' LIMIT 1) THEN 'anonymous'
    ELSE publish_identity
  END,
  public_handle = CASE 
    WHEN id = (SELECT id FROM profiles WHERE full_name ILIKE '%Giulia%' LIMIT 1) THEN 'WellnessQueen92'
    WHEN id = (SELECT id FROM profiles WHERE full_name ILIKE '%Sofia%' LIMIT 1) THEN 'LongevityExpert'
    ELSE public_handle
  END,
  display_avatar_url = CASE 
    WHEN id = (SELECT id FROM profiles WHERE full_name ILIKE '%Elena%' LIMIT 1) THEN 'avatars/elena_avatar.jpg'
    WHEN id = (SELECT id FROM profiles WHERE full_name ILIKE '%Marco%' LIMIT 1) THEN 'avatars/marco_avatar.jpg'
    ELSE display_avatar_url
  END
WHERE id IN (
  SELECT id FROM profiles WHERE full_name ILIKE '%Elena%' 
  UNION SELECT id FROM profiles WHERE full_name ILIKE '%Francesco%'
  UNION SELECT id FROM profiles WHERE full_name ILIKE '%Giulia%'
  UNION SELECT id FROM profiles WHERE full_name ILIKE '%Marco%'
  UNION SELECT id FROM profiles WHERE full_name ILIKE '%Sofia%'
);

-- Add DOB to existing patients if not already set
UPDATE patients SET 
  dob = CASE 
    WHEN full_name ILIKE '%Elena%' THEN '1985-03-15'
    WHEN full_name ILIKE '%Francesco%' THEN '1978-07-22'
    WHEN full_name ILIKE '%Giulia%' THEN '1992-11-08'
    WHEN full_name ILIKE '%Marco%' THEN '1980-05-12'
    WHEN full_name ILIKE '%Sofia%' THEN '1988-09-30'
    WHEN full_name ILIKE '%Alessandro%' THEN '1975-12-03'
    WHEN full_name ILIKE '%Isabella%' THEN '1990-06-18'
    WHEN full_name ILIKE '%Lorenzo%' THEN '1983-01-25'
    WHEN full_name ILIKE '%Valentina%' THEN '1987-04-14'
    WHEN full_name ILIKE '%Matteo%' THEN '1995-08-07'
    WHEN full_name ILIKE '%Chiara%' THEN '1982-10-29'
    WHEN full_name ILIKE '%Andrea%' THEN '1979-02-16'
    WHEN full_name ILIKE '%Francesca%' THEN '1991-12-11'
    WHEN full_name ILIKE '%Davide%' THEN '1984-07-03'
    WHEN full_name ILIKE '%Martina%' THEN '1989-05-20'
    ELSE COALESCE(dob, '1985-01-01'::date + (random() * interval '20 years'))
  END
WHERE dob IS NULL OR id IN (
  SELECT id FROM patients WHERE full_name ILIKE ANY(ARRAY[
    '%Elena%', '%Francesco%', '%Giulia%', '%Marco%', '%Sofia%',
    '%Alessandro%', '%Isabella%', '%Lorenzo%', '%Valentina%', '%Matteo%',
    '%Chiara%', '%Andrea%', '%Francesca%', '%Davide%', '%Martina%'
  ])
);

-- Create diverse biological age measurements for existing patients
INSERT INTO biological_ages (patient_id, method, biological_age_years, measured_at, source) 
SELECT 
    p.id as patient_id,
    (ARRAY['blood', 'saliva', 'epigenetic', 'device', 'composite'])[1 + floor(random() * 5)] as method,
    -- Generate realistic biological ages (some younger, some older than chronological)
    CASE 
        -- High performers (younger biological age)
        WHEN p.full_name ILIKE '%Elena%' THEN 32.5 -- Chrono: ~39, Delta: +6.5
        WHEN p.full_name ILIKE '%Giulia%' THEN 28.2 -- Chrono: ~32, Delta: +3.8  
        WHEN p.full_name ILIKE '%Francesco%' THEN 40.1 -- Chrono: ~46, Delta: +5.9
        WHEN p.full_name ILIKE '%Sofia%' THEN 31.8 -- Chrono: ~36, Delta: +4.2
        WHEN p.full_name ILIKE '%Matteo%' THEN 24.5 -- Chrono: ~29, Delta: +4.5
        
        -- Average performers (close to chronological age)  
        WHEN p.full_name ILIKE '%Marco%' THEN 43.2 -- Chrono: ~44, Delta: +0.8
        WHEN p.full_name ILIKE '%Valentina%' THEN 36.8 -- Chrono: ~37, Delta: +0.2
        WHEN p.full_name ILIKE '%Lorenzo%' THEN 41.5 -- Chrono: ~41, Delta: -0.5
        WHEN p.full_name ILIKE '%Chiara%' THEN 42.1 -- Chrono: ~42, Delta: -0.1
        
        -- Below average performers (older biological age)
        WHEN p.full_name ILIKE '%Alessandro%' THEN 52.3 -- Chrono: ~49, Delta: -3.3
        WHEN p.full_name ILIKE '%Isabella%' THEN 36.7 -- Chrono: ~34, Delta: -2.7
        WHEN p.full_name ILIKE '%Andrea%' THEN 48.9 -- Chrono: ~45, Delta: -3.9
        WHEN p.full_name ILIKE '%Francesca%' THEN 35.4 -- Chrono: ~33, Delta: -2.4
        WHEN p.full_name ILIKE '%Davide%' THEN 43.8 -- Chrono: ~40, Delta: -3.8
        WHEN p.full_name ILIKE '%Martina%' THEN 38.2 -- Chrono: ~35, Delta: -3.2
        
        -- Random for others
        ELSE EXTRACT(YEAR FROM AGE(p.dob))::numeric + (random() * 20 - 10)
    END as biological_age_years,
    NOW() - interval '30 days' + (random() * interval '25 days') as measured_at,
    jsonb_build_object(
        'lab', CASE (random() * 3)::int 
            WHEN 0 THEN 'TruAge Labs'
            WHEN 1 THEN 'Elysium Health'
            ELSE 'Longevity Institute'
        END,
        'test_type', CASE (random() * 4)::int
            WHEN 0 THEN 'DNA Methylation Panel'
            WHEN 1 THEN 'Telomere Length Analysis'
            WHEN 2 THEN 'Comprehensive Biomarker Panel'
            ELSE 'Epigenetic Age Assessment'
        END,
        'confidence_score', 85 + (random() * 15)
    ) as source
FROM patients p 
WHERE p.deleted_at IS NULL
AND p.dob IS NOT NULL
ON CONFLICT DO NOTHING;

-- Add some historical measurements for select patients (showing progression)
INSERT INTO biological_ages (patient_id, method, biological_age_years, measured_at, source) 
SELECT 
    p.id as patient_id,
    'composite' as method,
    -- Show improvement over time for some patients
    CASE 
        WHEN p.full_name ILIKE '%Elena%' THEN 35.1 -- Previous measurement was worse
        WHEN p.full_name ILIKE '%Francesco%' THEN 42.8 -- Improved from here
        WHEN p.full_name ILIKE '%Giulia%' THEN 30.5 -- Gradual improvement  
        ELSE EXTRACT(YEAR FROM AGE(p.dob))::numeric + (random() * 10 - 5)
    END as biological_age_years,
    NOW() - interval '120 days' as measured_at, -- 4 months ago
    jsonb_build_object(
        'lab', 'Longevity Institute',
        'test_type', 'Baseline Assessment',
        'confidence_score', 80 + (random() * 10)
    ) as source
FROM patients p 
WHERE p.full_name ILIKE ANY(ARRAY['%Elena%', '%Francesco%', '%Giulia%', '%Marco%', '%Sofia%'])
AND p.deleted_at IS NULL
ON CONFLICT DO NOTHING;

-- Compute longevity scores for all patients with biological age data
SELECT fn_upsert_patient_score(patient_id) 
FROM biological_ages ba
JOIN patients p ON p.id = ba.patient_id
WHERE p.deleted_at IS NULL
GROUP BY patient_id;

-- Set up leaderboard visibility for diverse showcase
INSERT INTO leaderboard_visibility (patient_id, org_id, opt_in, identity, pinned)
SELECT 
    p.id as patient_id,
    p.org_id,
    CASE 
        -- High performers opt in more often
        WHEN p.full_name ILIKE ANY(ARRAY['%Elena%', '%Giulia%', '%Francesco%', '%Sofia%', '%Matteo%']) THEN true
        -- Some average performers opt in
        WHEN p.full_name ILIKE ANY(ARRAY['%Marco%', '%Valentina%', '%Lorenzo%']) THEN true
        -- Most below average don't opt in (realistic behavior)
        WHEN p.full_name ILIKE ANY(ARRAY['%Isabella%', '%Chiara%']) THEN true
        ELSE false
    END as opt_in,
    CASE 
        WHEN p.full_name ILIKE '%Elena%' THEN 'avatar'
        WHEN p.full_name ILIKE '%Francesco%' THEN 'name'
        WHEN p.full_name ILIKE '%Giulia%' THEN 'anonymous'
        WHEN p.full_name ILIKE '%Sofia%' THEN 'avatar'
        WHEN p.full_name ILIKE '%Marco%' THEN 'name'
        WHEN p.full_name ILIKE '%Matteo%' THEN 'avatar'
        WHEN p.full_name ILIKE '%Valentina%' THEN 'name'
        WHEN p.full_name ILIKE '%Lorenzo%' THEN 'anonymous'
        WHEN p.full_name ILIKE '%Isabella%' THEN 'avatar'
        WHEN p.full_name ILIKE '%Chiara%' THEN 'name'
        ELSE 'avatar'
    END as identity,
    CASE 
        -- Pin top performers
        WHEN p.full_name ILIKE '%Elena%' THEN true
        WHEN p.full_name ILIKE '%Francesco%' THEN true
        ELSE false
    END as pinned
FROM patients p
WHERE p.deleted_at IS NULL
AND EXISTS (
    SELECT 1 FROM biological_ages ba WHERE ba.patient_id = p.id
)
ON CONFLICT (patient_id) DO UPDATE SET
    opt_in = EXCLUDED.opt_in,
    identity = EXCLUDED.identity,
    pinned = EXCLUDED.pinned,
    updated_at = NOW();

-- Create additional diverse patients for richer leaderboard data
DO $$
DECLARE
    org_record RECORD;
    new_patient_id UUID;
    patient_names TEXT[] := ARRAY[
        'Alessio Romano', 'Bianca Conti', 'Cristiano Ricci', 'Diana Moretti',
        'Emilio Ferrari', 'Federica Russo', 'Gabriele Marino', 'Helena Greco',
        'Ignazio Bruno', 'Jessica Colombo', 'Kevin Rizzo', 'Lucia Barbieri',
        'Michele Fontana', 'Noemi Villa', 'Oscar De Luca', 'Paola Caruso',
        'Quirino Rinaldi', 'Roberta Marchetti', 'Simone Leone', 'Teresa Galli'
    ];
    birth_dates DATE[] := ARRAY[
        '1976-03-20', '1989-07-14', '1993-11-25', '1981-05-08',
        '1987-12-03', '1990-01-17', '1983-09-29', '1985-06-12',
        '1992-04-05', '1988-10-18', '1979-08-07', '1986-02-23',
        '1991-12-15', '1984-07-31', '1982-03-09', '1994-09-22',
        '1977-11-06', '1989-05-25', '1985-01-13', '1990-08-28'
    ];
    genders TEXT[] := ARRAY[
        'male', 'female', 'male', 'female',
        'male', 'female', 'male', 'female', 
        'male', 'female', 'male', 'female',
        'male', 'female', 'male', 'female',
        'male', 'female', 'male', 'female'
    ];
    i INTEGER;
BEGIN
    -- Get first organization
    SELECT * INTO org_record FROM organizations LIMIT 1;
    
    IF org_record.id IS NOT NULL THEN
        FOR i IN 1..20 LOOP
            -- Create patient
            INSERT INTO patients (
                full_name,
                email,
                phone,
                dob,
                gender,
                org_id,
                membership_tier,
                tags
            ) VALUES (
                patient_names[i],
                LOWER(REPLACE(patient_names[i], ' ', '.')) || '@example.com',
                '+39 3' || LPAD((300000000 + i * 1234567)::text, 9, '0'),
                birth_dates[i],
                genders[i],
                org_record.id,
                CASE (i % 4)
                    WHEN 0 THEN 'elite'
                    WHEN 1 THEN 'platinum' 
                    WHEN 2 THEN 'gold'
                    ELSE 'not_member'
                END,
                CASE (i % 3)
                    WHEN 0 THEN ARRAY['wellness', 'longevity']
                    WHEN 1 THEN ARRAY['anti-aging', 'performance']
                    ELSE ARRAY['detox', 'regenerative']
                END
            ) RETURNING id INTO new_patient_id;
            
            -- Add biological age measurement
            INSERT INTO biological_ages (
                patient_id,
                method,
                biological_age_years,
                measured_at,
                source
            ) VALUES (
                new_patient_id,
                (ARRAY['blood', 'saliva', 'epigenetic', 'device', 'composite'])[1 + (i % 5)],
                -- Create realistic distribution of biological ages
                EXTRACT(YEAR FROM AGE(birth_dates[i]))::numeric + 
                CASE 
                    WHEN i <= 5 THEN random() * 8 - 2  -- Top performers (mostly younger)
                    WHEN i <= 12 THEN random() * 6 - 3 -- Average (mixed)  
                    ELSE random() * 4 - 6              -- Lower performers (mostly older)
                END,
                NOW() - interval '1 day' * (random() * 60)::int,
                jsonb_build_object(
                    'lab', (ARRAY['TruAge Labs', 'Elysium Health', 'Longevity Institute'])[1 + (i % 3)],
                    'test_type', 'Comprehensive Panel',
                    'confidence_score', 82 + (random() * 15)
                )
            );
            
            -- Set leaderboard visibility (realistic opt-in rates)
            INSERT INTO leaderboard_visibility (
                patient_id,
                org_id,
                opt_in,
                identity,
                pinned
            ) VALUES (
                new_patient_id,
                org_record.id,
                CASE WHEN i <= 12 THEN true ELSE random() < 0.3 END, -- 60% opt-in for first 12, 30% for others
                (ARRAY['name', 'avatar', 'anonymous'])[1 + (i % 3)],
                false
            );
            
        END LOOP;
        
        RAISE NOTICE 'Created 20 additional patients with biological age data';
    END IF;
END $$;

-- Compute scores for all new patients
SELECT fn_upsert_patient_score(ba.patient_id) 
FROM biological_ages ba
WHERE ba.created_at > NOW() - interval '1 hour'
GROUP BY ba.patient_id;

-- Create cohort definitions for better organization
INSERT INTO cohorts (key, org_id, definition) 
SELECT DISTINCT
    ls.cohort_key,
    p.org_id,
    jsonb_build_object(
        'age_band', SPLIT_PART(SPLIT_PART(ls.cohort_key, '|', 1), ':', 2),
        'gender', SPLIT_PART(SPLIT_PART(ls.cohort_key, '|', 2), ':', 2),
        'organization', SPLIT_PART(SPLIT_PART(ls.cohort_key, '|', 3), ':', 2),
        'created_at', NOW()
    )
FROM longevity_scores ls
JOIN patients p ON p.id = ls.patient_id
WHERE p.deleted_at IS NULL
ON CONFLICT (key) DO NOTHING;

-- Update scoring constants to realistic values
UPDATE score_constants SET value = 50.0, description = 'Base score when delta is 0 (neutral)' WHERE key = 'base_score';
UPDATE score_constants SET value = 4.0, description = 'Points per year of biological age advantage' WHERE key = 'delta_multiplier';  
UPDATE score_constants SET value = 0.0, description = 'Minimum possible score' WHERE key = 'min_score';
UPDATE score_constants SET value = 100.0, description = 'Maximum possible score' WHERE key = 'max_score';

-- Insert additional scoring constants
INSERT INTO score_constants (key, value, description) VALUES
('age_penalty_threshold', 10.0, 'Chronological age above which slight penalty applies'),
('cohort_bonus_threshold', 20, 'Minimum cohort size to apply ranking bonuses'),
('measurement_recency_weight', 0.95, 'Weight factor for measurement recency (0-1)')
ON CONFLICT (key) DO UPDATE SET
    value = EXCLUDED.value,
    description = EXCLUDED.description;

-- Create some audit log entries for realistic history
INSERT INTO audit_logs (actor_id, action, entity_table, entity_id, diff, metadata)
SELECT 
    (SELECT id FROM profiles WHERE role = 'admin' LIMIT 1),
    'longevity_score_computed',
    'longevity_scores',
    ls.patient_id,
    jsonb_build_object(
        'score', ls.score,
        'delta_years', ls.delta_years,
        'cohort_key', ls.cohort_key
    ),
    jsonb_build_object(
        'method', 'batch_computation',
        'timestamp', ls.computed_at
    )
FROM longevity_scores ls
WHERE ls.computed_at > NOW() - interval '1 hour'
LIMIT 10;

-- Final verification and statistics
DO $$
DECLARE
    stats RECORD;
BEGIN
    SELECT 
        COUNT(DISTINCT ls.patient_id) as total_patients_with_scores,
        COUNT(DISTINCT ls.cohort_key) as total_cohorts,
        ROUND(AVG(ls.score), 2) as avg_score,
        COUNT(CASE WHEN lv.opt_in = true THEN 1 END) as opted_in_patients
    INTO stats
    FROM longevity_scores ls
    LEFT JOIN leaderboard_visibility lv ON lv.patient_id = ls.patient_id
    JOIN patients p ON p.id = ls.patient_id
    WHERE p.deleted_at IS NULL;
    
    RAISE NOTICE 'LONGEVITY SCOREBOARD SEED COMPLETE:';
    RAISE NOTICE '- Patients with scores: %', stats.total_patients_with_scores;
    RAISE NOTICE '- Total cohorts: %', stats.total_cohorts;
    RAISE NOTICE '- Average score: %', stats.avg_score;
    RAISE NOTICE '- Opted-in patients: %', stats.opted_in_patients;
END $$;