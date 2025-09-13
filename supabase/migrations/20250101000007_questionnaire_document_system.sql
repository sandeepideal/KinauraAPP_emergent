-- Questionnaire and Document Management System Schema
-- This creates comprehensive questionnaire, document, and signature management

-- Create questionnaires table for managing different questionnaire templates
CREATE TABLE questionnaires (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL CHECK (category IN (
        'medical_history', 'privacy_disclosure', 'treatment_consent', 
        'pre_treatment', 'post_treatment', 'wellness_assessment', 
        'lifestyle', 'symptoms', 'preferences', 'other'
    )),
    is_active BOOLEAN DEFAULT TRUE,
    is_required BOOLEAN DEFAULT FALSE,
    instructions TEXT, -- Instructions for the patient
    created_by UUID REFERENCES profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Metadata for questionnaire behavior
    metadata JSONB DEFAULT '{}' -- Settings like: auto_assign_new_patients, frequency, etc.
);

-- Create questions table for individual questions
CREATE TABLE questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    questionnaire_id UUID NOT NULL REFERENCES questionnaires(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_type VARCHAR(50) NOT NULL CHECK (question_type IN (
        'multiple_choice', 'single_choice', 'text', 'long_text', 
        'number', 'date', 'yes_no', 'rating_scale', 'file_upload'
    )),
    is_required BOOLEAN DEFAULT FALSE,
    order_index INTEGER NOT NULL DEFAULT 0,
    
    -- Configuration for different question types
    options JSONB, -- For multiple choice: ["Option 1", "Option 2"], for rating: {"min": 1, "max": 10, "labels": {...}}
    validation JSONB, -- Validation rules: {"min_length": 10, "max_length": 500, "pattern": "regex"}
    help_text TEXT, -- Additional help text for the question
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create patient_questionnaires table to track assigned questionnaires
CREATE TABLE patient_questionnaires (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    questionnaire_id UUID NOT NULL REFERENCES questionnaires(id) ON DELETE CASCADE,
    assigned_by UUID REFERENCES profiles(id) ON DELETE SET NULL,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    due_date TIMESTAMPTZ, -- Optional due date
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    status VARCHAR(50) DEFAULT 'assigned' CHECK (status IN (
        'assigned', 'in_progress', 'completed', 'expired', 'cancelled'
    )),
    
    -- Optional context for assignment
    context JSONB, -- {"treatment_id": "...", "appointment_id": "...", "reason": "pre_treatment"}
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Ensure patient doesn't get the same questionnaire assigned multiple times simultaneously
    UNIQUE(patient_id, questionnaire_id, status) 
    DEFERRABLE INITIALLY DEFERRED -- Allow temporary duplicates during status transitions
);

-- Create patient_answers table to store individual answers
CREATE TABLE patient_answers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_questionnaire_id UUID NOT NULL REFERENCES patient_questionnaires(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    
    -- Different answer types
    answer_text TEXT, -- For text, long_text answers
    answer_number NUMERIC, -- For number, rating_scale answers
    answer_date DATE, -- For date answers
    answer_choices JSONB, -- For multiple_choice answers: ["choice1", "choice2"]
    answer_files JSONB, -- For file_upload answers: [{"filename": "...", "url": "...", "size": ...}]
    
    answered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Ensure one answer per question per patient questionnaire
    UNIQUE(patient_questionnaire_id, question_id)
);

-- Create documents table for consent forms and information documents
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    document_type VARCHAR(100) NOT NULL CHECK (document_type IN (
        'consent_form', 'privacy_notice', 'treatment_info', 'waiver', 
        'terms_conditions', 'medical_disclosure', 'financial_agreement', 'other'
    )),
    content TEXT NOT NULL, -- HTML content of the document
    version VARCHAR(50) DEFAULT '1.0',
    is_active BOOLEAN DEFAULT TRUE,
    requires_signature BOOLEAN DEFAULT TRUE,
    
    -- Document settings
    settings JSONB DEFAULT '{}', -- {"auto_assign": true, "treatments": ["treatment_id"], "expiry_days": 365}
    
    created_by UUID REFERENCES profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create patient_documents table to track assigned documents
CREATE TABLE patient_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    assigned_by UUID REFERENCES profiles(id) ON DELETE SET NULL,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    status VARCHAR(50) DEFAULT 'assigned' CHECK (status IN (
        'assigned', 'viewed', 'signed', 'expired', 'cancelled'
    )),
    
    viewed_at TIMESTAMPTZ,
    signed_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ, -- When the signature expires (if applicable)
    
    -- Context for why document was assigned
    context JSONB, -- {"treatment_id": "...", "appointment_id": "...", "service_id": "..."}
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create patient_signatures table for digital signatures
CREATE TABLE patient_signatures (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_document_id UUID NOT NULL REFERENCES patient_documents(id) ON DELETE CASCADE,
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    
    -- Signature data
    signature_data TEXT NOT NULL, -- Base64 encoded signature image or signature metadata
    signature_type VARCHAR(50) DEFAULT 'canvas' CHECK (signature_type IN (
        'canvas', 'typed', 'uploaded', 'electronic'
    )),
    
    -- Legal and audit information
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Additional verification data
    verification_data JSONB, -- {"browser": "...", "device": "...", "location": "..."}
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- One signature per document assignment
    UNIQUE(patient_document_id)
);

-- Create indexes for better performance
CREATE INDEX idx_questionnaires_org_category ON questionnaires(org_id, category, is_active);
CREATE INDEX idx_questions_questionnaire_order ON questions(questionnaire_id, order_index);
CREATE INDEX idx_patient_questionnaires_patient_status ON patient_questionnaires(patient_id, status);
CREATE INDEX idx_patient_questionnaires_due_date ON patient_questionnaires(due_date) WHERE due_date IS NOT NULL;
CREATE INDEX idx_patient_answers_questionnaire ON patient_answers(patient_questionnaire_id);
CREATE INDEX idx_documents_org_type ON documents(org_id, document_type, is_active);
CREATE INDEX idx_patient_documents_patient_status ON patient_documents(patient_id, status);
CREATE INDEX idx_patient_documents_assigned_at ON patient_documents(assigned_at DESC);
CREATE INDEX idx_patient_signatures_patient ON patient_signatures(patient_id);

-- Create updated_at triggers
CREATE TRIGGER update_questionnaires_updated_at BEFORE UPDATE ON questionnaires FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_questions_updated_at BEFORE UPDATE ON questions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_patient_questionnaires_updated_at BEFORE UPDATE ON patient_questionnaires FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_patient_answers_updated_at BEFORE UPDATE ON patient_answers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_patient_documents_updated_at BEFORE UPDATE ON patient_documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create helper functions

-- Function to assign questionnaire to patient
CREATE OR REPLACE FUNCTION assign_questionnaire_to_patient(
    questionnaire_id_param UUID,
    patient_id_param UUID,
    assigned_by_param UUID DEFAULT NULL,
    due_date_param TIMESTAMPTZ DEFAULT NULL,
    context_param JSONB DEFAULT '{}'
)
RETURNS UUID AS $$
DECLARE
    assignment_id UUID;
    questionnaire_record RECORD;
BEGIN
    -- Get questionnaire details
    SELECT * INTO questionnaire_record FROM questionnaires WHERE id = questionnaire_id_param AND is_active = TRUE;
    
    IF questionnaire_record IS NULL THEN
        RAISE EXCEPTION 'Questionnaire not found or inactive';
    END IF;
    
    -- Check if patient already has this questionnaire assigned and not completed
    IF EXISTS (
        SELECT 1 FROM patient_questionnaires 
        WHERE patient_id = patient_id_param 
        AND questionnaire_id = questionnaire_id_param 
        AND status IN ('assigned', 'in_progress')
    ) THEN
        RAISE EXCEPTION 'Patient already has this questionnaire assigned';
    END IF;
    
    -- Create assignment
    INSERT INTO patient_questionnaires (
        patient_id, questionnaire_id, assigned_by, due_date, context
    ) VALUES (
        patient_id_param, questionnaire_id_param, assigned_by_param, due_date_param, context_param
    ) RETURNING id INTO assignment_id;
    
    -- Log assignment
    INSERT INTO audit_logs (
        actor_id, action, entity_table, entity_id, diff
    ) VALUES (
        assigned_by_param, 'questionnaire_assigned', 'patient_questionnaires', assignment_id,
        jsonb_build_object('patient_id', patient_id_param, 'questionnaire_id', questionnaire_id_param)
    );
    
    RETURN assignment_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to assign document to patient
CREATE OR REPLACE FUNCTION assign_document_to_patient(
    document_id_param UUID,
    patient_id_param UUID,
    assigned_by_param UUID DEFAULT NULL,
    expires_in_days INTEGER DEFAULT NULL,
    context_param JSONB DEFAULT '{}'
)
RETURNS UUID AS $$
DECLARE
    assignment_id UUID;
    document_record RECORD;
    expiry_date TIMESTAMPTZ;
BEGIN
    -- Get document details
    SELECT * INTO document_record FROM documents WHERE id = document_id_param AND is_active = TRUE;
    
    IF document_record IS NULL THEN
        RAISE EXCEPTION 'Document not found or inactive';
    END IF;
    
    -- Calculate expiry date if specified
    IF expires_in_days IS NOT NULL THEN
        expiry_date := NOW() + (expires_in_days || ' days')::INTERVAL;
    ELSIF (document_record.settings->>'expiry_days') IS NOT NULL THEN
        expiry_date := NOW() + ((document_record.settings->>'expiry_days')::INTEGER || ' days')::INTERVAL;
    END IF;
    
    -- Create assignment
    INSERT INTO patient_documents (
        patient_id, document_id, assigned_by, expires_at, context
    ) VALUES (
        patient_id_param, document_id_param, assigned_by_param, expiry_date, context_param
    ) RETURNING id INTO assignment_id;
    
    -- Log assignment
    INSERT INTO audit_logs (
        actor_id, action, entity_table, entity_id, diff
    ) VALUES (
        assigned_by_param, 'document_assigned', 'patient_documents', assignment_id,
        jsonb_build_object('patient_id', patient_id_param, 'document_id', document_id_param)
    );
    
    RETURN assignment_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get patient's pending tasks (questionnaires + documents)
CREATE OR REPLACE FUNCTION get_patient_pending_tasks(patient_id_param UUID)
RETURNS TABLE(
    task_type TEXT,
    task_id UUID,
    title TEXT,
    description TEXT,
    assigned_at TIMESTAMPTZ,
    due_date TIMESTAMPTZ,
    priority TEXT,
    estimated_duration INTEGER -- in minutes
) AS $$
BEGIN
    RETURN QUERY
    -- Pending questionnaires
    SELECT 
        'questionnaire'::TEXT as task_type,
        pq.id as task_id,
        q.title,
        q.description,
        pq.assigned_at,
        pq.due_date,
        CASE 
            WHEN q.is_required THEN 'high'
            WHEN pq.due_date < NOW() + INTERVAL '24 hours' THEN 'urgent'
            ELSE 'normal'
        END as priority,
        COALESCE((q.metadata->>'estimated_minutes')::INTEGER, 10) as estimated_duration
    FROM patient_questionnaires pq
    JOIN questionnaires q ON q.id = pq.questionnaire_id
    WHERE pq.patient_id = patient_id_param
    AND pq.status IN ('assigned', 'in_progress')
    AND q.is_active = TRUE
    
    UNION ALL
    
    -- Pending documents  
    SELECT 
        'document'::TEXT as task_type,
        pd.id as task_id,
        d.title,
        CASE d.document_type
            WHEN 'consent_form' THEN 'Please review and sign this consent form'
            WHEN 'privacy_notice' THEN 'Please review our privacy notice'
            WHEN 'treatment_info' THEN 'Important information about your treatment'
            ELSE 'Please review and sign this document'
        END as description,
        pd.assigned_at,
        pd.expires_at as due_date,
        CASE 
            WHEN d.requires_signature THEN 'high'
            WHEN pd.expires_at < NOW() + INTERVAL '24 hours' THEN 'urgent'
            ELSE 'normal'
        END as priority,
        COALESCE((d.settings->>'estimated_minutes')::INTEGER, 5) as estimated_duration
    FROM patient_documents pd
    JOIN documents d ON d.id = pd.document_id
    WHERE pd.patient_id = patient_id_param
    AND pd.status IN ('assigned', 'viewed')
    AND d.is_active = TRUE
    
    ORDER BY 
        CASE priority 
            WHEN 'urgent' THEN 1
            WHEN 'high' THEN 2
            WHEN 'normal' THEN 3
        END,
        assigned_at ASC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get questionnaire completion statistics
CREATE OR REPLACE FUNCTION get_questionnaire_stats(questionnaire_id_param UUID)
RETURNS TABLE(
    total_assigned BIGINT,
    completed BIGINT,
    in_progress BIGINT,
    pending BIGINT,
    completion_rate NUMERIC,
    avg_completion_time INTERVAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_assigned,
        COUNT(CASE WHEN pq.status = 'completed' THEN 1 END)::BIGINT as completed,
        COUNT(CASE WHEN pq.status = 'in_progress' THEN 1 END)::BIGINT as in_progress,
        COUNT(CASE WHEN pq.status = 'assigned' THEN 1 END)::BIGINT as pending,
        ROUND(
            (COUNT(CASE WHEN pq.status = 'completed' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0)), 2
        ) as completion_rate,
        AVG(CASE 
            WHEN pq.status = 'completed' AND pq.started_at IS NOT NULL 
            THEN pq.completed_at - pq.started_at 
        END) as avg_completion_time
    FROM patient_questionnaires pq
    WHERE pq.questionnaire_id = questionnaire_id_param;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Comments for documentation
COMMENT ON TABLE questionnaires IS 'Templates for patient questionnaires (medical history, consent, etc.)';
COMMENT ON TABLE questions IS 'Individual questions within questionnaires with various answer types';
COMMENT ON TABLE patient_questionnaires IS 'Tracking of questionnaires assigned to patients';
COMMENT ON TABLE patient_answers IS 'Patient responses to questionnaire questions';
COMMENT ON TABLE documents IS 'Document templates for consent forms, information sheets, etc.';
COMMENT ON TABLE patient_documents IS 'Documents assigned to patients for review/signature';
COMMENT ON TABLE patient_signatures IS 'Digital signatures on patient documents';
COMMENT ON FUNCTION assign_questionnaire_to_patient IS 'Assigns a questionnaire to a patient with proper validation';
COMMENT ON FUNCTION assign_document_to_patient IS 'Assigns a document to a patient for review/signature';
COMMENT ON FUNCTION get_patient_pending_tasks IS 'Gets all pending questionnaires and documents for a patient';
COMMENT ON FUNCTION get_questionnaire_stats IS 'Provides completion statistics for a questionnaire';