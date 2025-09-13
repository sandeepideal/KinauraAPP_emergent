-- KinAura Seed Data
-- This populates the database with sample data for development and testing

-- Insert KinAura Milan organization
INSERT INTO organizations (id, name, timezone, billing_email) VALUES
('018c5c37-b5a0-7000-8000-000000000001', 'KinAura Milan', 'Europe/Rome', 'billing@kinaura.it');

-- Create admin user profile (assuming auth.users already has this user)
-- You would create the auth user separately via Supabase Auth
INSERT INTO profiles (id, org_id, role, full_name, privacy_consent, marketing_consent) VALUES
('018c5c37-b5a0-7000-8000-000000000002', '018c5c37-b5a0-7000-8000-000000000001', 'admin', 'Dr. Marco Rossi', true, true),
('018c5c37-b5a0-7000-8000-000000000003', '018c5c37-b5a0-7000-8000-000000000001', 'practitioner', 'Dr. Sofia Bianchi', true, true);

-- Create clinicians
INSERT INTO clinicians (id, org_id, profile_id, name, specialization, license_number) VALUES
('018c5c37-b5a0-7000-8000-000000000004', '018c5c37-b5a0-7000-8000-000000000001', '018c5c37-b5a0-7000-8000-000000000002', 'Dr. Marco Rossi', 'Regenerative Medicine', 'RM-2024-001'),
('018c5c37-b5a0-7000-8000-000000000005', '018c5c37-b5a0-7000-8000-000000000001', '018c5c37-b5a0-7000-8000-000000000003', 'Dr. Sofia Bianchi', 'Aesthetic Medicine', 'AM-2024-002');

-- Create membership plans
INSERT INTO membership_plans (id, org_id, name, tier, price_cents, perks, billing_period) VALUES
('018c5c37-b5a0-7000-8000-000000000006', '018c5c37-b5a0-7000-8000-000000000001', 'Gold Membership', 'gold', 29900, '{"discount": 10, "priority_booking": true, "monthly_consultation": true}', 'monthly'),
('018c5c37-b5a0-7000-8000-000000000007', '018c5c37-b5a0-7000-8000-000000000001', 'Platinum Membership', 'platinum', 49900, '{"discount": 20, "priority_booking": true, "bi_weekly_consultation": true, "free_iv_therapy": true}', 'monthly'),
('018c5c37-b5a0-7000-8000-000000000008', '018c5c37-b5a0-7000-8000-000000000001', 'Elite Membership', 'elite', 99900, '{"discount": 30, "vip_access": true, "weekly_consultation": true, "premium_treatments": true, "concierge_24_7": true}', 'monthly');

-- Create sample patients
INSERT INTO patients (id, org_id, code, full_name, email, phone, dob, gender, country, tags, owner_user_id) VALUES
('018c5c37-b5a0-7000-8000-000000000009', '018c5c37-b5a0-7000-8000-000000000001', 'KA-001001', 'Elena Verdi', 'elena.verdi@example.com', '+39 347 123 4567', '1985-03-15', 'female', 'IT', '{"anti-aging", "wellness"}', '018c5c37-b5a0-7000-8000-000000000002'),
('018c5c37-b5a0-7000-8000-000000000010', '018c5c37-b5a0-7000-8000-000000000001', 'KA-001002', 'Francesco Neri', 'francesco.neri@example.com', '+39 348 987 6543', '1978-08-22', 'male', 'IT', '{"performance", "longevity"}', '018c5c37-b5a0-7000-8000-000000000002');

-- Create memberships for patients
INSERT INTO memberships (id, patient_id, org_id, plan_id, status, start_date, end_date, auto_renew) VALUES
('018c5c37-b5a0-7000-8000-000000000011', '018c5c37-b5a0-7000-8000-000000000009', '018c5c37-b5a0-7000-8000-000000000001', '018c5c37-b5a0-7000-8000-000000000007', 'active', '2024-01-01', '2024-12-31', true),
('018c5c37-b5a0-7000-8000-000000000012', '018c5c37-b5a0-7000-8000-000000000010', '018c5c37-b5a0-7000-8000-000000000001', '018c5c37-b5a0-7000-8000-000000000008', 'active', '2024-01-01', '2024-12-31', true);

-- Create services catalog
INSERT INTO services (id, org_id, category, name, description, duration_min, base_price_cents, is_active) VALUES
('018c5c37-b5a0-7000-8000-000000000013', '018c5c37-b5a0-7000-8000-000000000001', 'regenerative', 'Ozone Therapy', 'Advanced ozone treatment for cellular regeneration and immune system enhancement', 75, 22900, true),
('018c5c37-b5a0-7000-8000-000000000014', '018c5c37-b5a0-7000-8000-000000000001', 'iv_therapy', 'NAD+ IV Therapy', 'Revolutionary anti-aging therapy with nicotinamide adenine dinucleotide', 180, 44900, true),
('018c5c37-b5a0-7000-8000-000000000015', '018c5c37-b5a0-7000-8000-000000000001', 'regenerative', 'Hyperbaric Oxygen Therapy', 'Pure oxygen therapy in pressurized chamber for healing acceleration', 60, 19900, true),
('018c5c37-b5a0-7000-8000-000000000016', '018c5c37-b5a0-7000-8000-000000000001', 'iv_therapy', 'IV Vitamin Drips', 'Customized intravenous vitamin and mineral infusions', 45, 17900, true),
('018c5c37-b5a0-7000-8000-000000000017', '018c5c37-b5a0-7000-8000-000000000001', 'aesthetics', 'Red Light Therapy', 'Photobiomodulation therapy for skin rejuvenation and cellular energy', 30, 9900, true),
('018c5c37-b5a0-7000-8000-000000000018', '018c5c37-b5a0-7000-8000-000000000001', 'skincare', 'Personalized Skincare Consultation', 'AI-powered analysis and custom formula creation', 90, 15000, true);

-- Create sample protocols
INSERT INTO protocols (id, patient_id, name, goals, status, ai_version, last_ai_update_at) VALUES
('018c5c37-b5a0-7000-8000-000000000019', '018c5c37-b5a0-7000-8000-000000000009', 'Platinum Anti-Aging Protocol', '{"inflammation": "reduce", "skin_texture": "improve", "energy": "boost", "cellular_health": "optimize"}', 'active', 'v2024.1.15', '2024-01-15 10:00:00+00'),
('018c5c37-b5a0-7000-8000-000000000020', '018c5c37-b5a0-7000-8000-000000000010', 'Elite Performance Protocol', '{"performance": "enhance", "recovery": "accelerate", "longevity": "extend", "cognitive": "optimize"}', 'active', 'v2024.1.20', '2024-01-20 14:30:00+00');

-- Create protocol sessions
INSERT INTO protocol_sessions (id, protocol_id, idx, title, status, scheduled_at, completed_at, clinician_id, notes) VALUES
('018c5c37-b5a0-7000-8000-000000000021', '018c5c37-b5a0-7000-8000-000000000019', 1, 'Initial Assessment & Ozone Therapy', 'done', '2024-01-10 09:00:00+00', '2024-01-10 10:15:00+00', '018c5c37-b5a0-7000-8000-000000000004', 'Excellent initial response to treatment'),
('018c5c37-b5a0-7000-8000-000000000022', '018c5c37-b5a0-7000-8000-000000000019', 2, 'IV Vitamin Therapy', 'done', '2024-01-17 10:00:00+00', '2024-01-17 10:45:00+00', '018c5c37-b5a0-7000-8000-000000000005', 'Patient reports increased energy levels'),
('018c5c37-b5a0-7000-8000-000000000023', '018c5c37-b5a0-7000-8000-000000000019', 3, 'Red Light Therapy Session', 'scheduled', '2024-01-24 11:00:00+00', null, '018c5c37-b5a0-7000-8000-000000000005', null),
('018c5c37-b5a0-7000-8000-000000000024', '018c5c37-b5a0-7000-8000-000000000020', 1, 'Comprehensive Health Analysis', 'done', '2024-01-12 15:00:00+00', '2024-01-12 16:30:00+00', '018c5c37-b5a0-7000-8000-000000000004', 'Baseline metrics established'),
('018c5c37-b5a0-7000-8000-000000000025', '018c5c37-b5a0-7000-8000-000000000020', 2, 'NAD+ IV Therapy', 'scheduled', '2024-01-26 14:00:00+00', null, '018c5c37-b5a0-7000-8000-000000000004', null);

-- Create sample analyses
INSERT INTO analyses (id, patient_id, kind, metrics, source, document_ids, created_by) VALUES
('018c5c37-b5a0-7000-8000-000000000026', '018c5c37-b5a0-7000-8000-000000000009', 'blood', '{"hemoglobin": 13.5, "vitamin_d": 32, "inflammatory_markers": {"crp": 1.2, "esr": 15}, "lipid_profile": {"total_cholesterol": 190, "hdl": 58, "ldl": 120}}', 'clinic', '["blood_analysis_elena_20240110.pdf"]', '018c5c37-b5a0-7000-8000-000000000004'),
('018c5c37-b5a0-7000-8000-000000000027', '018c5c37-b5a0-7000-8000-000000000009', 'hormonal', '{"estradiol": 45, "progesterone": 8.2, "testosterone": 0.8, "cortisol": 280, "thyroid": {"tsh": 2.1, "t3": 3.8, "t4": 9.2}}', 'clinic', '["hormonal_panel_elena_20240115.pdf"]', '018c5c37-b5a0-7000-8000-000000000005'),
('018c5c37-b5a0-7000-8000-000000000028', '018c5c37-b5a0-7000-8000-000000000010', 'oligoscan', '{"minerals": {"magnesium": 85, "zinc": 78, "selenium": 92}, "heavy_metals": {"mercury": 15, "lead": 8, "cadmium": 12}, "oxidative_stress": 68}', 'clinic', '["oligoscan_francesco_20240112.pdf"]', '018c5c37-b5a0-7000-8000-000000000004');

-- Create sample pre/post treatment images
INSERT INTO prepost_sets (id, patient_id, treatment_context, before_image, after_image, diff_meta, notes) VALUES
('018c5c37-b5a0-7000-8000-000000000029', '018c5c37-b5a0-7000-8000-000000000009', 'Ozone Therapy - Skin Assessment', 'patient-images/018c5c37-b5a0-7000-8000-000000000009/before_20240110.jpg', 'patient-images/018c5c37-b5a0-7000-8000-000000000009/after_20240117.jpg', '{"skin_texture_improvement": 0.23, "hydration_increase": 0.18, "pore_size_reduction": 0.15, "overall_score": 0.78}', 'Significant improvement in skin texture and hydration after first treatment cycle');

-- Create longevity scores
INSERT INTO longevity_scores (id, patient_id, score_numeric, components, community_avg_snapshot, computed_at) VALUES
('018c5c37-b5a0-7000-8000-000000000030', '018c5c37-b5a0-7000-8000-000000000009', 78, '{"adherence": 85, "biomarkers": 72, "skin_improvements": 80, "inflammation_markers": 75, "energy_levels": 82}', 68.5, '2024-01-18 08:00:00+00'),
('018c5c37-b5a0-7000-8000-000000000031', '018c5c37-b5a0-7000-8000-000000000010', 84, '{"adherence": 92, "biomarkers": 85, "skin_improvements": 75, "inflammation_markers": 88, "energy_levels": 85, "cognitive_performance": 80}', 68.5, '2024-01-18 08:05:00+00');

-- Create sample formulas (minimum €150)
INSERT INTO formulas (id, patient_id, analysis_id, name, actives, concentration, fragrance, packaging, price_cents, status) VALUES
('018c5c37-b5a0-7000-8000-000000000032', '018c5c37-b5a0-7000-8000-000000000009', '018c5c37-b5a0-7000-8000-000000000027', 'Elena Custom Anti-Aging Serum', '{"retinoid_complex": true, "vitamin_c": true, "peptides": true, "hyaluronic_acid": true}', '{"retinoid": "0.5%", "vitamin_c": "15%", "peptides": "5%", "hyaluronic_acid": "2%"}', 'Rose & Neroli', 'serum_bottle', 18500, 'finalized'),
('018c5c37-b5a0-7000-8000-000000000033', '018c5c37-b5a0-7000-8000-000000000010', '018c5c37-b5a0-7000-8000-000000000028', 'Francesco Performance Recovery Cream', '{"growth_factors": true, "cbd": true, "ceramides": true, "antioxidants": true}', '{"growth_factors": "3%", "cbd": "2%", "ceramides": "4%", "vitamin_e": "1%"}', 'Unscented', 'jar', 22000, 'finalized');

-- Create sample orders
INSERT INTO orders (id, patient_id, formula_id, channel, status, total_cents, payment_ref) VALUES
('018c5c37-b5a0-7000-8000-000000000034', '018c5c37-b5a0-7000-8000-000000000009', '018c5c37-b5a0-7000-8000-000000000032', 'app', 'paid', 18500, 'pi_1234567890_elena'),
('018c5c37-b5a0-7000-8000-000000000035', '018c5c37-b5a0-7000-8000-000000000010', '018c5c37-b5a0-7000-8000-000000000033', 'in_clinic', 'paid', 22000, 'clinic_payment_francesco_001');

-- Create sample appointments
INSERT INTO appointments (id, patient_id, org_id, service_id, starts_at, ends_at, practitioner_id, status, notes) VALUES
('018c5c37-b5a0-7000-8000-000000000036', '018c5c37-b5a0-7000-8000-000000000009', '018c5c37-b5a0-7000-8000-000000000001', '018c5c37-b5a0-7000-8000-000000000013', '2024-01-10 09:00:00+00', '2024-01-10 10:15:00+00', '018c5c37-b5a0-7000-8000-000000000004', 'completed', 'First ozone therapy session - excellent response'),
('018c5c37-b5a0-7000-8000-000000000037', '018c5c37-b5a0-7000-8000-000000000009', '018c5c37-b5a0-7000-8000-000000000001', '018c5c37-b5a0-7000-8000-000000000016', '2024-01-17 10:00:00+00', '2024-01-17 10:45:00+00', '018c5c37-b5a0-7000-8000-000000000005', 'completed', 'IV vitamin therapy - patient reports increased energy'),
('018c5c37-b5a0-7000-8000-000000000038', '018c5c37-b5a0-7000-8000-000000000009', '018c5c37-b5a0-7000-8000-000000000001', '018c5c37-b5a0-7000-8000-000000000017', '2024-01-24 11:00:00+00', '2024-01-24 11:30:00+00', '018c5c37-b5a0-7000-8000-000000000005', 'scheduled', 'Red light therapy session'),
('018c5c37-b5a0-7000-8000-000000000039', '018c5c37-b5a0-7000-8000-000000000010', '018c5c37-b5a0-7000-8000-000000000001', '018c5c37-b5a0-7000-8000-000000000014', '2024-01-26 14:00:00+00', '2024-01-26 17:00:00+00', '018c5c37-b5a0-7000-8000-000000000004', 'confirmed', 'NAD+ therapy session for performance enhancement');

-- Create messaging threads and messages
INSERT INTO threads (id, patient_id, created_by, last_message_at) VALUES
('018c5c37-b5a0-7000-8000-000000000040', '018c5c37-b5a0-7000-8000-000000000009', '018c5c37-b5a0-7000-8000-000000000004', '2024-01-18 15:30:00+00'),
('018c5c37-b5a0-7000-8000-000000000041', '018c5c37-b5a0-7000-8000-000000000010', '018c5c37-b5a0-7000-8000-000000000004', '2024-01-19 10:15:00+00');

INSERT INTO messages (id, thread_id, sender_id, sender_role, body, read_at) VALUES
('018c5c37-b5a0-7000-8000-000000000042', '018c5c37-b5a0-7000-8000-000000000040', '018c5c37-b5a0-7000-8000-000000000004', 'admin', 'Ciao Elena! Come ti senti dopo le prime due sessioni del protocollo?', '2024-01-18 16:00:00+00'),
('018c5c37-b5a0-7000-8000-000000000043', '018c5c37-b5a0-7000-8000-000000000040', '018c5c37-b5a0-7000-8000-000000000009', 'patient', 'Molto bene Dr. Rossi! Ho più energia e la pelle sembra già più luminosa. Grazie!', null),
('018c5c37-b5a0-7000-8000-000000000044', '018c5c37-b5a0-7000-8000-000000000041', '018c5c37-b5a0-7000-8000-000000000004', 'admin', 'Francesco, tutto pronto per la tua sessione NAD+ di domani. Hai domande?', '2024-01-19 10:30:00+00'),
('018c5c37-b5a0-7000-8000-000000000045', '018c5c37-b5a0-7000-8000-000000000041', '018c5c37-b5a0-7000-8000-000000000010', 'patient', 'Perfetto, sono molto curioso di provare questa terapia. A domani!', null);

-- Create sample segments for marketing
INSERT INTO segments (id, org_id, name, definition) VALUES
('018c5c37-b5a0-7000-8000-000000000046', '018c5c37-b5a0-7000-8000-000000000001', 'Premium Members', '{"membership_tier": "platinum", "membership_status": "active"}'),
('018c5c37-b5a0-7000-8000-000000000047', '018c5c37-b5a0-7000-8000-000000000001', 'Anti-Aging Focus', '{"tags": ["anti-aging"], "membership_status": "active"}');

-- Create sample campaigns
INSERT INTO campaigns (id, org_id, name, channel, segment_id, status, sent_count, metadata) VALUES
('018c5c37-b5a0-7000-8000-000000000048', '018c5c37-b5a0-7000-8000-000000000001', 'New NAD+ Treatment Launch', 'push', '018c5c37-b5a0-7000-8000-000000000046', 'sent', 2, '{"title": "Scopri la nuova terapia NAD+", "body": "La rivoluzionaria terapia anti-aging è ora disponibile da KinAura"}'),
('018c5c37-b5a0-7000-8000-000000000049', '018c5c37-b5a0-7000-8000-000000000001', 'Winter Wellness Check', 'email', '018c5c37-b5a0-7000-8000-000000000047', 'draft', 0, '{"title": "Check-up invernale gratuito", "body": "Prenota la tua consulenza wellness gratuita per l\'inverno"}');

-- Create sample notifications
INSERT INTO notifications (id, patient_id, channel, title, body, data, status, sent_at) VALUES
('018c5c37-b5a0-7000-8000-000000000050', '018c5c37-b5a0-7000-8000-000000000009', 'push', 'Promemoria Appuntamento', 'Il tuo appuntamento per Red Light Therapy è domani alle 11:00', '{"appointment_id": "018c5c37-b5a0-7000-8000-000000000038", "type": "reminder"}', 'sent', '2024-01-23 18:00:00+00'),
('018c5c37-b5a0-7000-8000-000000000051', '018c5c37-b5a0-7000-8000-000000000010', 'push', 'Scopri la nuova terapia NAD+', 'La rivoluzionaria terapia anti-aging è ora disponibile da KinAura', '{"campaign_id": "018c5c37-b5a0-7000-8000-000000000048", "type": "campaign"}', 'sent', '2024-01-20 10:00:00+00');

-- Create consent records
INSERT INTO consents (id, patient_id, kind, granted, granted_at, method) VALUES
('018c5c37-b5a0-7000-8000-000000000052', '018c5c37-b5a0-7000-8000-000000000009', 'privacy', true, '2024-01-01 10:00:00+00', 'registration_form'),
('018c5c37-b5a0-7000-8000-000000000053', '018c5c37-b5a0-7000-8000-000000000009', 'marketing', true, '2024-01-01 10:00:00+00', 'registration_form'),
('018c5c37-b5a0-7000-8000-000000000054', '018c5c37-b5a0-7000-8000-000000000009', 'data_use', true, '2024-01-01 10:00:00+00', 'registration_form'),
('018c5c37-b5a0-7000-8000-000000000055', '018c5c37-b5a0-7000-8000-000000000010', 'privacy', true, '2024-01-02 15:30:00+00', 'registration_form'),
('018c5c37-b5a0-7000-8000-000000000056', '018c5c37-b5a0-7000-8000-000000000010', 'marketing', false, null, 'registration_form'),
('018c5c37-b5a0-7000-8000-000000000057', '018c5c37-b5a0-7000-8000-000000000010', 'data_use', true, '2024-01-02 15:30:00+00', 'registration_form');

-- Create sample patient notes
INSERT INTO patient_notes (id, patient_id, author_id, visibility, content) VALUES
('018c5c37-b5a0-7000-8000-000000000058', '018c5c37-b5a0-7000-8000-000000000009', '018c5c37-b5a0-7000-8000-000000000004', 'practitioner_only', 'Paziente molto motivata, ottima aderenza al protocollo. Risultati eccellenti dopo le prime sessioni. Considera upgrade a Elite membership.'),
('018c5c37-b5a0-7000-8000-000000000059', '018c5c37-b5a0-7000-8000-000000000010', '018c5c37-b5a0-7000-8000-000000000004', 'practitioner_only', 'Atleta professionista, focus su performance e recovery. Interessato alle ultime innovazioni. Candidato ideale per protocolli avanzati.');

-- Create sample audit logs
INSERT INTO audit_logs (id, actor_id, org_id, action, entity_table, entity_id, diff) VALUES
('018c5c37-b5a0-7000-8000-000000000060', '018c5c37-b5a0-7000-8000-000000000004', '018c5c37-b5a0-7000-8000-000000000001', 'create_patient', 'patients', '018c5c37-b5a0-7000-8000-000000000009', '{"name": "Elena Verdi", "email": "elena.verdi@example.com"}'),
('018c5c37-b5a0-7000-8000-000000000061', '018c5c37-b5a0-7000-8000-000000000004', '018c5c37-b5a0-7000-8000-000000000001', 'refresh_protocol', 'protocols', '018c5c37-b5a0-7000-8000-000000000019', '{"ai_version": "v2024.1.15", "sessions_updated": 3}'),
('018c5c37-b5a0-7000-8000-000000000062', '018c5c37-b5a0-7000-8000-000000000004', '018c5c37-b5a0-7000-8000-000000000001', 'finalize_formula', 'formulas', '018c5c37-b5a0-7000-8000-000000000032', '{"price_cents": 18500, "status": "finalized"}');

-- Seed complete message
INSERT INTO audit_logs (actor_id, org_id, action, entity_table, entity_id, diff) VALUES
('018c5c37-b5a0-7000-8000-000000000002', '018c5c37-b5a0-7000-8000-000000000001', 'seed_complete', 'system', '018c5c37-b5a0-7000-8000-000000000001', '{"message": "KinAura seed data successfully loaded", "timestamp": "2024-01-20T12:00:00Z"}');