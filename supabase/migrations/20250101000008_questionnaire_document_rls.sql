-- Row Level Security Policies for Questionnaire and Document Management System
-- This implements strict security for all questionnaire and document tables

-- Enable RLS on all new tables
ALTER TABLE questionnaires ENABLE ROW LEVEL SECURITY;
ALTER TABLE questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE patient_questionnaires ENABLE ROW LEVEL SECURITY;
ALTER TABLE patient_answers ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE patient_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE patient_signatures ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- QUESTIONNAIRES POLICIES
-- =====================================================

-- Admin/practitioners can manage questionnaires in their org
CREATE POLICY "questionnaires_staff_access" ON questionnaires
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM profiles pr
            WHERE pr.id = auth.uid()
            AND pr.org_id = org_id
            AND pr.role IN ('admin', 'practitioner')
        )
    );

-- Patients can read questionnaires assigned to them
CREATE POLICY "questionnaires_patient_read" ON questionnaires
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM patient_questionnaires pq
            JOIN patients p ON p.id = pq.patient_id
            WHERE pq.questionnaire_id = id
            AND p.email = (SELECT raw_user_meta_data->>'email' FROM auth.users WHERE id = auth.uid())
            AND pq.status IN ('assigned', 'in_progress')
        )
    );

-- =====================================================
-- QUESTIONS POLICIES
-- =====================================================

-- Admin/practitioners can manage questions in their org
CREATE POLICY "questions_staff_access" ON questions
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM questionnaires q
            JOIN profiles pr ON pr.org_id = q.org_id
            WHERE q.id = questionnaire_id
            AND pr.id = auth.uid()
            AND pr.role IN ('admin', 'practitioner')
        )
    );

-- Patients can read questions for their assigned questionnaires
CREATE POLICY "questions_patient_read" ON questions
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM patient_questionnaires pq
            JOIN patients p ON p.id = pq.patient_id
            WHERE pq.questionnaire_id = questionnaire_id
            AND p.email = (SELECT raw_user_meta_data->>'email' FROM auth.users WHERE id = auth.uid())
            AND pq.status IN ('assigned', 'in_progress')
        )
    );

-- =====================================================
-- PATIENT_QUESTIONNAIRES POLICIES
-- =====================================================

-- Admin/practitioners can manage patient questionnaires in their org
CREATE POLICY "patient_questionnaires_staff_access" ON patient_questionnaires
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM patients p
            JOIN profiles pr ON pr.org_id = p.org_id
            WHERE p.id = patient_id
            AND pr.id = auth.uid()
            AND pr.role IN ('admin', 'practitioner')
        )
    );

-- Patients can read their own questionnaire assignments
CREATE POLICY "patient_questionnaires_patient_read" ON patient_questionnaires
    FOR SELECT USING (
        patient_id = (
            SELECT p.id FROM patients p
            JOIN profiles pr ON pr.id = auth.uid()
            WHERE p.email = (SELECT raw_user_meta_data->>'email' FROM auth.users WHERE id = auth.uid())
            AND p.org_id = pr.org_id
        )
    );

-- Patients can update status of their own questionnaires (start, complete)
CREATE POLICY "patient_questionnaires_patient_update" ON patient_questionnaires
    FOR UPDATE USING (
        patient_id = (
            SELECT p.id FROM patients p
            JOIN profiles pr ON pr.id = auth.uid()
            WHERE p.email = (SELECT raw_user_meta_data->>'email' FROM auth.users WHERE id = auth.uid())
            AND p.org_id = pr.org_id
        )
    ) WITH CHECK (
        -- Patients can only update certain fields
        OLD.patient_id = NEW.patient_id
        AND OLD.questionnaire_id = NEW.questionnaire_id
        AND OLD.assigned_by = NEW.assigned_by
        AND OLD.assigned_at = NEW.assigned_at
        AND OLD.due_date = NEW.due_date
        AND OLD.context = NEW.context
    );

-- =====================================================
-- PATIENT_ANSWERS POLICIES
-- =====================================================

-- Admin/practitioners can read patient answers in their org
CREATE POLICY "patient_answers_staff_read" ON patient_answers
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM patient_questionnaires pq
            JOIN patients p ON p.id = pq.patient_id
            JOIN profiles pr ON pr.org_id = p.org_id
            WHERE pq.id = patient_questionnaire_id
            AND pr.id = auth.uid()
            AND pr.role IN ('admin', 'practitioner')
        )
    );

-- Patients can manage their own answers
CREATE POLICY "patient_answers_patient_access" ON patient_answers
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM patient_questionnaires pq
            JOIN patients p ON p.id = pq.patient_id
            WHERE pq.id = patient_questionnaire_id
            AND p.email = (SELECT raw_user_meta_data->>'email' FROM auth.users WHERE id = auth.uid())
        )
    );

-- =====================================================
-- DOCUMENTS POLICIES
-- =====================================================

-- Admin/practitioners can manage documents in their org
CREATE POLICY "documents_staff_access" ON documents
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM profiles pr
            WHERE pr.id = auth.uid()
            AND pr.org_id = org_id
            AND pr.role IN ('admin', 'practitioner')
        )
    );

-- Patients can read documents assigned to them
CREATE POLICY "documents_patient_read" ON documents
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM patient_documents pd
            JOIN patients p ON p.id = pd.patient_id
            WHERE pd.document_id = id
            AND p.email = (SELECT raw_user_meta_data->>'email' FROM auth.users WHERE id = auth.uid())
            AND pd.status IN ('assigned', 'viewed')
        )
    );

-- =====================================================
-- PATIENT_DOCUMENTS POLICIES
-- =====================================================

-- Admin/practitioners can manage patient documents in their org
CREATE POLICY "patient_documents_staff_access" ON patient_documents
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM patients p
            JOIN profiles pr ON pr.org_id = p.org_id
            WHERE p.id = patient_id
            AND pr.id = auth.uid()
            AND pr.role IN ('admin', 'practitioner')
        )
    );

-- Patients can read their own document assignments
CREATE POLICY "patient_documents_patient_read" ON patient_documents
    FOR SELECT USING (
        patient_id = (
            SELECT p.id FROM patients p
            JOIN profiles pr ON pr.id = auth.uid()
            WHERE p.email = (SELECT raw_user_meta_data->>'email' FROM auth.users WHERE id = auth.uid())
            AND p.org_id = pr.org_id
        )
    );

-- Patients can update their own document status (mark as viewed, signed)
CREATE POLICY "patient_documents_patient_update" ON patient_documents
    FOR UPDATE USING (
        patient_id = (
            SELECT p.id FROM patients p
            JOIN profiles pr ON pr.id = auth.uid()
            WHERE p.email = (SELECT raw_user_meta_data->>'email' FROM auth.users WHERE id = auth.uid())
            AND p.org_id = pr.org_id
        )
    ) WITH CHECK (
        -- Patients can only update certain fields
        OLD.patient_id = NEW.patient_id
        AND OLD.document_id = NEW.document_id
        AND OLD.assigned_by = NEW.assigned_by
        AND OLD.assigned_at = NEW.assigned_at
        AND OLD.expires_at = NEW.expires_at
        AND OLD.context = NEW.context
    );

-- =====================================================
-- PATIENT_SIGNATURES POLICIES
-- =====================================================

-- Admin/practitioners can read signatures in their org
CREATE POLICY "patient_signatures_staff_read" ON patient_signatures
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM patients p
            JOIN profiles pr ON pr.org_id = p.org_id
            WHERE p.id = patient_id
            AND pr.id = auth.uid()
            AND pr.role IN ('admin', 'practitioner')
        )
    );

-- Patients can create their own signatures
CREATE POLICY "patient_signatures_patient_insert" ON patient_signatures
    FOR INSERT WITH CHECK (
        patient_id = (
            SELECT p.id FROM patients p
            JOIN profiles pr ON pr.id = auth.uid()
            WHERE p.email = (SELECT raw_user_meta_data->>'email' FROM auth.users WHERE id = auth.uid())
            AND p.org_id = pr.org_id
        )
    );

-- Patients can read their own signatures
CREATE POLICY "patient_signatures_patient_read" ON patient_signatures
    FOR SELECT USING (
        patient_id = (
            SELECT p.id FROM patients p
            JOIN profiles pr ON pr.id = auth.uid()
            WHERE p.email = (SELECT raw_user_meta_data->>'email' FROM auth.users WHERE id = auth.uid())
            AND p.org_id = pr.org_id
        )
    );

-- =====================================================
-- HELPER FUNCTIONS FOR SECURITY
-- =====================================================

-- Function to check if user can access patient questionnaire data
CREATE OR REPLACE FUNCTION can_access_patient_questionnaire_data(target_patient_id UUID)
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

-- Function to safely get patient's questionnaire responses
CREATE OR REPLACE FUNCTION get_patient_questionnaire_responses(
    patient_id_param UUID,
    questionnaire_id_param UUID DEFAULT NULL
)
RETURNS TABLE(
    questionnaire_title TEXT,
    question_text TEXT,
    question_type TEXT,
    answer_text TEXT,
    answer_choices JSONB,
    answer_number NUMERIC,
    answer_date DATE,
    answered_at TIMESTAMPTZ,
    completion_status TEXT
)
SECURITY DEFINER
AS $$
BEGIN
    -- Check access permission
    IF NOT can_access_patient_questionnaire_data(patient_id_param) THEN
        RAISE EXCEPTION 'Access denied to patient questionnaire data';
    END IF;
    
    RETURN QUERY
    SELECT 
        q.title as questionnaire_title,
        qu.question_text,
        qu.question_type,
        pa.answer_text,
        pa.answer_choices,
        pa.answer_number,
        pa.answer_date,
        pa.answered_at,
        pq.status as completion_status
    FROM patient_questionnaires pq
    JOIN questionnaires q ON q.id = pq.questionnaire_id
    JOIN questions qu ON qu.questionnaire_id = q.id
    LEFT JOIN patient_answers pa ON pa.patient_questionnaire_id = pq.id AND pa.question_id = qu.id
    WHERE pq.patient_id = patient_id_param
    AND (questionnaire_id_param IS NULL OR pq.questionnaire_id = questionnaire_id_param)
    ORDER BY q.title, qu.order_index, pa.answered_at;
END;
$$ LANGUAGE plpgsql;

-- Function to safely get patient's document status
CREATE OR REPLACE FUNCTION get_patient_document_status(
    patient_id_param UUID,
    document_type_filter TEXT DEFAULT NULL
)
RETURNS TABLE(
    document_title TEXT,
    document_type TEXT,
    status TEXT,
    assigned_at TIMESTAMPTZ,
    viewed_at TIMESTAMPTZ,
    signed_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    is_expired BOOLEAN
)
SECURITY DEFINER
AS $$
BEGIN
    -- Check access permission
    IF NOT can_access_patient_questionnaire_data(patient_id_param) THEN
        RAISE EXCEPTION 'Access denied to patient document data';
    END IF;
    
    RETURN QUERY
    SELECT 
        d.title as document_title,
        d.document_type,
        pd.status,
        pd.assigned_at,
        pd.viewed_at,
        pd.signed_at,
        pd.expires_at,
        (pd.expires_at IS NOT NULL AND pd.expires_at < NOW()) as is_expired
    FROM patient_documents pd
    JOIN documents d ON d.id = pd.document_id
    WHERE pd.patient_id = patient_id_param
    AND (document_type_filter IS NULL OR d.document_type = document_type_filter)
    ORDER BY pd.assigned_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to safely get questionnaire for patient
CREATE OR REPLACE FUNCTION get_patient_questionnaire_data(
    patient_questionnaire_id_param UUID
)
RETURNS TABLE(
    questionnaire_title TEXT,
    questionnaire_description TEXT,
    questionnaire_instructions TEXT,
    question_id UUID,
    question_text TEXT,
    question_type TEXT,
    is_required BOOLEAN,
    order_index INTEGER,
    options JSONB,
    help_text TEXT,
    current_answer_text TEXT,
    current_answer_choices JSONB,
    current_answer_number NUMERIC,
    current_answer_date DATE,
    answered_at TIMESTAMPTZ
)
SECURITY DEFINER
AS $$
DECLARE
    pq_record RECORD;
BEGIN
    -- Get patient questionnaire record and check access
    SELECT pq.*, p.id as patient_id INTO pq_record
    FROM patient_questionnaires pq
    JOIN patients p ON p.id = pq.patient_id
    WHERE pq.id = patient_questionnaire_id_param;
    
    IF pq_record IS NULL THEN
        RAISE EXCEPTION 'Patient questionnaire not found';
    END IF;
    
    -- Check access permission
    IF NOT can_access_patient_questionnaire_data(pq_record.patient_id) THEN
        RAISE EXCEPTION 'Access denied to patient questionnaire data';
    END IF;
    
    RETURN QUERY
    SELECT 
        q.title as questionnaire_title,
        q.description as questionnaire_description,
        q.instructions as questionnaire_instructions,
        qu.id as question_id,
        qu.question_text,
        qu.question_type,
        qu.is_required,
        qu.order_index,
        qu.options,
        qu.help_text,
        pa.answer_text as current_answer_text,
        pa.answer_choices as current_answer_choices,
        pa.answer_number as current_answer_number,
        pa.answer_date as current_answer_date,
        pa.answered_at
    FROM questionnaires q
    JOIN questions qu ON qu.questionnaire_id = q.id
    LEFT JOIN patient_answers pa ON pa.question_id = qu.id AND pa.patient_questionnaire_id = patient_questionnaire_id_param
    WHERE q.id = pq_record.questionnaire_id
    ORDER BY qu.order_index;
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON FUNCTION can_access_patient_questionnaire_data IS 'Security function to check questionnaire/document data access permissions';
COMMENT ON FUNCTION get_patient_questionnaire_responses IS 'Safely retrieves patient questionnaire responses with access control';
COMMENT ON FUNCTION get_patient_document_status IS 'Safely retrieves patient document status with access control';
COMMENT ON FUNCTION get_patient_questionnaire_data IS 'Safely retrieves questionnaire data for patient completion';