-- =====================================================
-- KinAura Questionnaire and Document Management System
-- Comprehensive Test Suite
-- =====================================================

-- This file contains comprehensive unit and integration tests for the
-- questionnaire and document management system to ensure data integrity,
-- business logic compliance, and system reliability.

BEGIN;

-- Test Configuration
-- ==================
DO $$
DECLARE
    test_count INTEGER := 0;
    passed_tests INTEGER := 0;
    failed_tests INTEGER := 0;
    test_name TEXT;
    test_result BOOLEAN;
BEGIN
    RAISE NOTICE '=====================================';
    RAISE NOTICE 'QUESTIONNAIRE SYSTEM TEST SUITE';
    RAISE NOTICE '=====================================';
    RAISE NOTICE 'Starting comprehensive test execution...';
    RAISE NOTICE '';

    -- Test 1: Questionnaire Creation and Validation
    -- ==============================================
    test_count := test_count + 1;
    test_name := 'Questionnaire Creation and Validation';
    BEGIN
        -- Test creating a questionnaire with all required fields
        INSERT INTO questionnaires (_id, title, description, category, is_active, is_required, instructions, questions, created_by, created_at, updated_at, metadata)
        VALUES (
            'test-quest-001',
            'Test Medical Questionnaire',
            'Test questionnaire for validation',
            'medical_history',
            true,
            false,
            'Test instructions',
            '[]',
            'test-admin',
            NOW(),
            NOW(),
            '{}'
        );
        
        -- Verify the questionnaire was created
        IF EXISTS (SELECT 1 FROM questionnaires WHERE _id = 'test-quest-001') THEN
            test_result := TRUE;
            RAISE NOTICE '[PASS] %: Questionnaire created successfully', test_name;
            passed_tests := passed_tests + 1;
        ELSE
            test_result := FALSE;
            RAISE NOTICE '[FAIL] %: Questionnaire creation failed', test_name;
            failed_tests := failed_tests + 1;
        END IF;
        
        DELETE FROM questionnaires WHERE _id = 'test-quest-001';
        
    EXCEPTION
        WHEN OTHERS THEN
            test_result := FALSE;
            RAISE NOTICE '[FAIL] %: Exception - %', test_name, SQLERRM;
            failed_tests := failed_tests + 1;
    END;

    -- Test 2: Question Data Structure Validation
    -- ===========================================
    test_count := test_count + 1;
    test_name := 'Question Data Structure Validation';
    BEGIN
        -- Test questionnaire with complex questions JSON
        INSERT INTO questionnaires (_id, title, description, category, is_active, is_required, instructions, questions, created_by, created_at, updated_at, metadata)
        VALUES (
            'test-quest-002',
            'Complex Questions Test',
            'Test complex question structures',
            'wellness_assessment',
            true,
            false,
            'Test instructions',
            '[
                {
                    "id": "q1",
                    "question_text": "Test multiple choice question",
                    "question_type": "multiple_choice",
                    "is_required": true,
                    "order_index": 1,
                    "options": {
                        "choices": ["Option A", "Option B", "Option C"],
                        "allow_multiple": true
                    },
                    "validation": {},
                    "help_text": "Select all that apply"
                },
                {
                    "id": "q2", 
                    "question_text": "Test rating scale",
                    "question_type": "rating_scale",
                    "is_required": true,
                    "order_index": 2,
                    "options": {
                        "min": 1,
                        "max": 10,
                        "labels": {"1": "Poor", "10": "Excellent"}
                    },
                    "validation": {},
                    "help_text": "Rate from 1 to 10"
                }
            ]',
            'test-admin',
            NOW(),
            NOW(),
            '{"estimated_minutes": 5}'
        );
        
        -- Verify JSON structure is valid and accessible
        DECLARE
            question_count INTEGER;
            first_question JSONB;
        BEGIN
            SELECT jsonb_array_length(questions), questions->0 
            INTO question_count, first_question
            FROM questionnaires WHERE _id = 'test-quest-002';
            
            IF question_count = 2 AND first_question->>'question_type' = 'multiple_choice' THEN
                test_result := TRUE;
                RAISE NOTICE '[PASS] %: Complex question JSON structure valid', test_name;
                passed_tests := passed_tests + 1;
            ELSE
                test_result := FALSE;
                RAISE NOTICE '[FAIL] %: Question JSON structure invalid', test_name;
                failed_tests := failed_tests + 1;
            END IF;
        END;
        
        DELETE FROM questionnaires WHERE _id = 'test-quest-002';
        
    EXCEPTION
        WHEN OTHERS THEN
            test_result := FALSE;
            RAISE NOTICE '[FAIL] %: Exception - %', test_name, SQLERRM;
            failed_tests := failed_tests + 1;
    END;

    -- Test 3: Patient Questionnaire Assignment
    -- =========================================
    test_count := test_count + 1;
    test_name := 'Patient Questionnaire Assignment';
    BEGIN
        -- Create test questionnaire
        INSERT INTO questionnaires (_id, title, description, category, is_active, is_required, instructions, questions, created_by, created_at, updated_at, metadata)
        VALUES ('test-quest-003', 'Assignment Test', 'Test assignment', 'pre_treatment', true, false, 'Instructions', '[]', 'test-admin', NOW(), NOW(), '{}');
        
        -- Create assignment
        INSERT INTO patient_questionnaires (_id, patient_id, questionnaire_id, assigned_by, assigned_at, due_date, status, context)
        VALUES (
            'test-assign-001',
            'test-patient-001',
            'test-quest-003',
            'test-admin',
            NOW(),
            NOW() + INTERVAL '7 days',
            'assigned',
            '{}'
        );
        
        -- Verify assignment
        IF EXISTS (SELECT 1 FROM patient_questionnaires WHERE _id = 'test-assign-001' AND status = 'assigned') THEN
            test_result := TRUE;
            RAISE NOTICE '[PASS] %: Patient questionnaire assignment successful', test_name;
            passed_tests := passed_tests + 1;
        ELSE
            test_result := FALSE;
            RAISE NOTICE '[FAIL] %: Patient questionnaire assignment failed', test_name;
            failed_tests := failed_tests + 1;
        END IF;
        
        -- Cleanup
        DELETE FROM patient_questionnaires WHERE _id = 'test-assign-001';
        DELETE FROM questionnaires WHERE _id = 'test-quest-003';
        
    EXCEPTION
        WHEN OTHERS THEN
            test_result := FALSE;
            RAISE NOTICE '[FAIL] %: Exception - %', test_name, SQLERRM;
            failed_tests := failed_tests + 1;
    END;

    -- Test 4: Assignment Status Transitions
    -- ====================================
    test_count := test_count + 1;
    test_name := 'Assignment Status Transitions';
    BEGIN
        -- Create test data
        INSERT INTO questionnaires (_id, title, description, category, is_active, is_required, instructions, questions, created_by, created_at, updated_at, metadata)
        VALUES ('test-quest-004', 'Status Test', 'Test status transitions', 'medical_history', true, false, 'Instructions', '[]', 'test-admin', NOW(), NOW(), '{}');
        
        INSERT INTO patient_questionnaires (_id, patient_id, questionnaire_id, assigned_by, assigned_at, status, context)
        VALUES ('test-assign-002', 'test-patient-002', 'test-quest-004', 'test-admin', NOW(), 'assigned', '{}');
        
        -- Test status transition: assigned -> in_progress
        UPDATE patient_questionnaires 
        SET status = 'in_progress', started_at = NOW()
        WHERE _id = 'test-assign-002';
        
        -- Test status transition: in_progress -> completed
        UPDATE patient_questionnaires 
        SET status = 'completed', completed_at = NOW()
        WHERE _id = 'test-assign-002';
        
        -- Verify final status
        DECLARE
            final_status TEXT;
            has_completed_at BOOLEAN;
        BEGIN
            SELECT status, completed_at IS NOT NULL
            INTO final_status, has_completed_at
            FROM patient_questionnaires WHERE _id = 'test-assign-002';
            
            IF final_status = 'completed' AND has_completed_at THEN
                test_result := TRUE;
                RAISE NOTICE '[PASS] %: Status transitions working correctly', test_name;
                passed_tests := passed_tests + 1;
            ELSE
                test_result := FALSE;
                RAISE NOTICE '[FAIL] %: Status transitions failed', test_name;
                failed_tests := failed_tests + 1;
            END IF;
        END;
        
        -- Cleanup
        DELETE FROM patient_questionnaires WHERE _id = 'test-assign-002';
        DELETE FROM questionnaires WHERE _id = 'test-quest-004';
        
    EXCEPTION
        WHEN OTHERS THEN
            test_result := FALSE;
            RAISE NOTICE '[FAIL] %: Exception - %', test_name, SQLERRM;
            failed_tests := failed_tests + 1;
    END;

    -- Test 5: Patient Answer Storage and Retrieval
    -- ============================================
    test_count := test_count + 1;
    test_name := 'Patient Answer Storage and Retrieval';
    BEGIN
        -- Create test data
        INSERT INTO questionnaires (_id, title, description, category, is_active, is_required, instructions, questions, created_by, created_at, updated_at, metadata)
        VALUES ('test-quest-005', 'Answer Test', 'Test answer storage', 'wellness_assessment', true, false, 'Instructions', 
        '[{"id": "q1", "question_text": "Test question", "question_type": "text", "is_required": true, "order_index": 1}]', 
        'test-admin', NOW(), NOW(), '{}');
        
        INSERT INTO patient_questionnaires (_id, patient_id, questionnaire_id, assigned_by, assigned_at, status, context)
        VALUES ('test-assign-003', 'test-patient-003', 'test-quest-005', 'test-admin', NOW(), 'in_progress', '{}');
        
        -- Test different answer types
        INSERT INTO patient_answers (_id, patient_questionnaire_id, question_id, answer_text, answered_at)
        VALUES ('test-answer-001', 'test-assign-003', 'q1', 'Text answer response', NOW());
        
        INSERT INTO patient_answers (_id, patient_questionnaire_id, question_id, answer_number, answered_at)
        VALUES ('test-answer-002', 'test-assign-003', 'q2', 8, NOW());
        
        INSERT INTO patient_answers (_id, patient_questionnaire_id, question_id, answer_choices, answered_at)
        VALUES ('test-answer-003', 'test-assign-003', 'q3', '["Choice A", "Choice C"]', NOW());
        
        INSERT INTO patient_answers (_id, patient_questionnaire_id, question_id, answer_date, answered_at)
        VALUES ('test-answer-004', 'test-assign-003', 'q4', '1990-05-15', NOW());
        
        -- Verify answers stored correctly
        DECLARE
            answer_count INTEGER;
            text_answer TEXT;
            number_answer NUMERIC;
            choice_answer JSONB;
            date_answer DATE;
        BEGIN
            SELECT COUNT(*) FROM patient_answers WHERE patient_questionnaire_id = 'test-assign-003' INTO answer_count;
            SELECT answer_text FROM patient_answers WHERE _id = 'test-answer-001' INTO text_answer;
            SELECT answer_number FROM patient_answers WHERE _id = 'test-answer-002' INTO number_answer;
            SELECT answer_choices FROM patient_answers WHERE _id = 'test-answer-003' INTO choice_answer;
            SELECT answer_date FROM patient_answers WHERE _id = 'test-answer-004' INTO date_answer;
            
            IF answer_count = 4 AND 
               text_answer = 'Text answer response' AND 
               number_answer = 8 AND 
               choice_answer = '["Choice A", "Choice C"]'::jsonb AND 
               date_answer = '1990-05-15'::date THEN
                test_result := TRUE;
                RAISE NOTICE '[PASS] %: All answer types stored and retrieved correctly', test_name;
                passed_tests := passed_tests + 1;
            ELSE
                test_result := FALSE;
                RAISE NOTICE '[FAIL] %: Answer storage/retrieval failed', test_name;
                failed_tests := failed_tests + 1;
            END IF;
        END;
        
        -- Cleanup
        DELETE FROM patient_answers WHERE patient_questionnaire_id = 'test-assign-003';
        DELETE FROM patient_questionnaires WHERE _id = 'test-assign-003';
        DELETE FROM questionnaires WHERE _id = 'test-quest-005';
        
    EXCEPTION
        WHEN OTHERS THEN
            test_result := FALSE;
            RAISE NOTICE '[FAIL] %: Exception - %', test_name, SQLERRM;
            failed_tests := failed_tests + 1;
    END;

    -- Test 6: Document Management System
    -- ==================================
    test_count := test_count + 1;
    test_name := 'Document Management System';
    BEGIN
        -- Create test document
        INSERT INTO documents (_id, title, document_type, content, version, is_active, requires_signature, settings, created_by, created_at, updated_at)
        VALUES (
            'test-doc-001',
            'Test Privacy Policy',
            'privacy_notice',
            '<h1>Test Privacy Policy</h1><p>This is a test document.</p>',
            '1.0',
            true,
            true,
            '{"signature_required": true}',
            'test-admin',
            NOW(),
            NOW()
        );
        
        -- Create document assignment
        INSERT INTO patient_documents (_id, patient_id, document_id, assigned_by, assigned_at, status, context)
        VALUES (
            'test-doc-assign-001',
            'test-patient-004',
            'test-doc-001',
            'test-admin',
            NOW(),
            'assigned',
            '{}'
        );
        
        -- Test document viewing
        UPDATE patient_documents 
        SET status = 'viewed', viewed_at = NOW()
        WHERE _id = 'test-doc-assign-001';
        
        -- Test document signing
        UPDATE patient_documents 
        SET status = 'signed', signed_at = NOW()
        WHERE _id = 'test-doc-assign-001';
        
        -- Create signature record
        INSERT INTO patient_signatures (_id, patient_document_id, patient_id, signature_data, signature_type, timestamp, verification_data)
        VALUES (
            'test-sig-001',
            'test-doc-assign-001',
            'test-patient-004',
            'John Doe Test Signature',
            'typed',
            NOW(),
            '{}'
        );
        
        -- Verify document workflow
        DECLARE
            doc_status TEXT;
            has_signature BOOLEAN;
        BEGIN
            SELECT pd.status, ps._id IS NOT NULL
            INTO doc_status, has_signature
            FROM patient_documents pd
            LEFT JOIN patient_signatures ps ON pd._id = ps.patient_document_id
            WHERE pd._id = 'test-doc-assign-001';
            
            IF doc_status = 'signed' AND has_signature THEN
                test_result := TRUE;
                RAISE NOTICE '[PASS] %: Document workflow completed successfully', test_name;
                passed_tests := passed_tests + 1;
            ELSE
                test_result := FALSE;
                RAISE NOTICE '[FAIL] %: Document workflow failed', test_name;
                failed_tests := failed_tests + 1;
            END IF;
        END;
        
        -- Cleanup
        DELETE FROM patient_signatures WHERE _id = 'test-sig-001';
        DELETE FROM patient_documents WHERE _id = 'test-doc-assign-001';
        DELETE FROM documents WHERE _id = 'test-doc-001';
        
    EXCEPTION
        WHEN OTHERS THEN
            test_result := FALSE;
            RAISE NOTICE '[FAIL] %: Exception - %', test_name, SQLERRM;
            failed_tests := failed_tests + 1;
    END;

    -- Test 7: Data Integrity and Constraints
    -- ======================================
    test_count := test_count + 1;
    test_name := 'Data Integrity and Constraints';
    BEGIN
        DECLARE
            constraint_violation BOOLEAN := FALSE;
        BEGIN
            -- Test invalid questionnaire category
            BEGIN
                INSERT INTO questionnaires (_id, title, description, category, is_active, is_required, instructions, questions, created_by, created_at, updated_at, metadata)
                VALUES ('test-quest-invalid', 'Invalid Category Test', 'Test', 'invalid_category', true, false, 'Instructions', '[]', 'test-admin', NOW(), NOW(), '{}');
            EXCEPTION
                WHEN check_violation THEN
                    constraint_violation := TRUE;
            END;
            
            -- Test invalid document type
            BEGIN
                INSERT INTO documents (_id, title, document_type, content, version, is_active, requires_signature, settings, created_by, created_at, updated_at)
                VALUES ('test-doc-invalid', 'Invalid Type Test', 'invalid_type', '<p>Test</p>', '1.0', true, false, '{}', 'test-admin', NOW(), NOW());
            EXCEPTION
                WHEN check_violation THEN
                    constraint_violation := TRUE;
            END;
            
            -- Test invalid assignment status
            BEGIN
                INSERT INTO questionnaires (_id, title, description, category, is_active, is_required, instructions, questions, created_by, created_at, updated_at, metadata)
                VALUES ('test-quest-006', 'Constraint Test', 'Test', 'medical_history', true, false, 'Instructions', '[]', 'test-admin', NOW(), NOW(), '{}');
                
                INSERT INTO patient_questionnaires (_id, patient_id, questionnaire_id, assigned_by, assigned_at, status, context)
                VALUES ('test-assign-004', 'test-patient-005', 'test-quest-006', 'test-admin', NOW(), 'invalid_status', '{}');
            EXCEPTION
                WHEN check_violation THEN
                    constraint_violation := TRUE;
                    DELETE FROM questionnaires WHERE _id = 'test-quest-006';
            END;
            
            IF constraint_violation THEN
                test_result := TRUE;
                RAISE NOTICE '[PASS] %: Data constraints working correctly', test_name;
                passed_tests := passed_tests + 1;
            ELSE
                test_result := FALSE;
                RAISE NOTICE '[FAIL] %: Data constraints not enforced', test_name;
                failed_tests := failed_tests + 1;
            END IF;
        END;
        
    EXCEPTION
        WHEN OTHERS THEN
            test_result := FALSE;
            RAISE NOTICE '[FAIL] %: Exception - %', test_name, SQLERRM;
            failed_tests := failed_tests + 1;
    END;

    -- Test 8: Assignment Deadline and Priority Logic
    -- ==============================================
    test_count := test_count + 1;
    test_name := 'Assignment Deadline and Priority Logic';
    BEGIN
        -- Create test questionnaire
        INSERT INTO questionnaires (_id, title, description, category, is_active, is_required, instructions, questions, created_by, created_at, updated_at, metadata)
        VALUES ('test-quest-007', 'Deadline Test', 'Test deadlines', 'treatment_consent', true, true, 'Instructions', '[]', 'test-admin', NOW(), NOW(), '{}');
        
        -- Create assignments with different deadlines
        INSERT INTO patient_questionnaires (_id, patient_id, questionnaire_id, assigned_by, assigned_at, due_date, status, context)
        VALUES 
            ('test-assign-005', 'test-patient-006', 'test-quest-007', 'test-admin', NOW(), NOW() + INTERVAL '1 day', 'assigned', '{"priority": "urgent"}'),
            ('test-assign-006', 'test-patient-007', 'test-quest-007', 'test-admin', NOW(), NOW() + INTERVAL '7 days', 'assigned', '{"priority": "normal"}'),
            ('test-assign-007', 'test-patient-008', 'test-quest-007', 'test-admin', NOW(), NOW() - INTERVAL '1 day', 'assigned', '{"priority": "overdue"}');
        
        -- Test priority calculation based on due dates and required status
        DECLARE
            urgent_count INTEGER;
            normal_count INTEGER;
            overdue_count INTEGER;
        BEGIN
            -- Count assignments by priority context
            SELECT 
                COUNT(CASE WHEN due_date <= NOW() + INTERVAL '1 day' AND due_date > NOW() THEN 1 END),
                COUNT(CASE WHEN due_date > NOW() + INTERVAL '1 day' THEN 1 END),
                COUNT(CASE WHEN due_date < NOW() THEN 1 END)
            INTO urgent_count, normal_count, overdue_count
            FROM patient_questionnaires 
            WHERE questionnaire_id = 'test-quest-007';
            
            IF urgent_count >= 1 AND normal_count >= 1 AND overdue_count >= 1 THEN
                test_result := TRUE;
                RAISE NOTICE '[PASS] %: Deadline and priority logic working', test_name;
                passed_tests := passed_tests + 1;
            ELSE
                test_result := FALSE;
                RAISE NOTICE '[FAIL] %: Deadline and priority logic failed', test_name;
                failed_tests := failed_tests + 1;
            END IF;
        END;
        
        -- Cleanup
        DELETE FROM patient_questionnaires WHERE questionnaire_id = 'test-quest-007';
        DELETE FROM questionnaires WHERE _id = 'test-quest-007';
        
    EXCEPTION
        WHEN OTHERS THEN
            test_result := FALSE;
            RAISE NOTICE '[FAIL] %: Exception - %', test_name, SQLERRM;
            failed_tests := failed_tests + 1;
    END;

    -- Test 9: JSON Query Performance and Functionality
    -- ================================================
    test_count := test_count + 1;
    test_name := 'JSON Query Performance and Functionality';
    BEGIN
        -- Create questionnaire with complex JSON structure
        INSERT INTO questionnaires (_id, title, description, category, is_active, is_required, instructions, questions, created_by, created_at, updated_at, metadata)
        VALUES (
            'test-quest-008',
            'JSON Performance Test',
            'Test JSON operations',
            'wellness_assessment',
            true,
            false,
            'Instructions',
            '[
                {"id": "q1", "question_text": "Multiple choice", "question_type": "multiple_choice", "options": {"choices": ["A", "B", "C"]}},
                {"id": "q2", "question_text": "Rating scale", "question_type": "rating_scale", "options": {"min": 1, "max": 10}},
                {"id": "q3", "question_text": "Text input", "question_type": "text", "validation": {"max_length": 100}}
            ]',
            'test-admin',
            NOW(),
            NOW(),
            '{"estimated_minutes": 15, "category_tags": ["wellness", "assessment"], "difficulty": "medium"}'
        );
        
        -- Test JSON queries
        DECLARE
            question_count INTEGER;
            multiple_choice_count INTEGER;
            has_rating_scale BOOLEAN;
            estimated_minutes INTEGER;
        BEGIN
            -- Test question counting
            SELECT jsonb_array_length(questions) 
            FROM questionnaires WHERE _id = 'test-quest-008'
            INTO question_count;
            
            -- Test filtering by question type
            SELECT COUNT(*)
            FROM questionnaires, jsonb_array_elements(questions) AS q
            WHERE _id = 'test-quest-008' AND q->>'question_type' = 'multiple_choice'
            INTO multiple_choice_count;
            
            -- Test checking for specific question type
            SELECT EXISTS(
                SELECT 1 FROM questionnaires, jsonb_array_elements(questions) AS q
                WHERE _id = 'test-quest-008' AND q->>'question_type' = 'rating_scale'
            ) INTO has_rating_scale;
            
            -- Test metadata extraction
            SELECT (metadata->>'estimated_minutes')::INTEGER
            FROM questionnaires WHERE _id = 'test-quest-008'
            INTO estimated_minutes;
            
            IF question_count = 3 AND multiple_choice_count = 1 AND has_rating_scale AND estimated_minutes = 15 THEN
                test_result := TRUE;
                RAISE NOTICE '[PASS] %: JSON queries working correctly', test_name;
                passed_tests := passed_tests + 1;
            ELSE
                test_result := FALSE;
                RAISE NOTICE '[FAIL] %: JSON query functionality failed', test_name;
                failed_tests := failed_tests + 1;
            END IF;
        END;
        
        DELETE FROM questionnaires WHERE _id = 'test-quest-008';
        
    EXCEPTION
        WHEN OTHERS THEN
            test_result := FALSE;
            RAISE NOTICE '[FAIL] %: Exception - %', test_name, SQLERRM;
            failed_tests := failed_tests + 1;
    END;

    -- Test 10: Cross-Table Relationships and Referential Integrity
    -- ============================================================
    test_count := test_count + 1;
    test_name := 'Cross-Table Relationships and Referential Integrity';
    BEGIN
        -- Create complete workflow test
        INSERT INTO questionnaires (_id, title, description, category, is_active, is_required, instructions, questions, created_by, created_at, updated_at, metadata)
        VALUES ('test-quest-009', 'Workflow Test', 'Complete workflow', 'pre_treatment', true, false, 'Instructions', 
        '[{"id": "wf1", "question_text": "Workflow question", "question_type": "text", "is_required": true}]', 
        'test-admin', NOW(), NOW(), '{}');
        
        INSERT INTO documents (_id, title, document_type, content, version, is_active, requires_signature, settings, created_by, created_at, updated_at)
        VALUES ('test-doc-002', 'Workflow Document', 'consent_form', '<p>Workflow test document</p>', '1.0', true, true, '{}', 'test-admin', NOW(), NOW());
        
        -- Create patient assignments
        INSERT INTO patient_questionnaires (_id, patient_id, questionnaire_id, assigned_by, assigned_at, status, context)
        VALUES ('test-assign-008', 'test-patient-009', 'test-quest-009', 'test-admin', NOW(), 'in_progress', '{}');
        
        INSERT INTO patient_documents (_id, patient_id, document_id, assigned_by, assigned_at, status, context)
        VALUES ('test-doc-assign-002', 'test-patient-009', 'test-doc-002', 'test-admin', NOW(), 'assigned', '{}');
        
        -- Add answers and signatures
        INSERT INTO patient_answers (_id, patient_questionnaire_id, question_id, answer_text, answered_at)
        VALUES ('test-answer-005', 'test-assign-008', 'wf1', 'Workflow answer', NOW());
        
        UPDATE patient_documents SET status = 'signed', signed_at = NOW() WHERE _id = 'test-doc-assign-002';
        
        INSERT INTO patient_signatures (_id, patient_document_id, patient_id, signature_data, signature_type, timestamp, verification_data)
        VALUES ('test-sig-002', 'test-doc-assign-002', 'test-patient-009', 'Workflow Signature', 'typed', NOW(), '{}');
        
        -- Test complete patient task summary
        DECLARE
            patient_tasks JSONB;
        BEGIN
            WITH patient_summary AS (
                SELECT 
                    'test-patient-009' as patient_id,
                    COUNT(pq._id) as questionnaire_count,
                    COUNT(pd._id) as document_count,
                    COUNT(pa._id) as answer_count,
                    COUNT(ps._id) as signature_count
                FROM patient_questionnaires pq
                FULL OUTER JOIN patient_documents pd ON pq.patient_id = pd.patient_id
                FULL OUTER JOIN patient_answers pa ON pq._id = pa.patient_questionnaire_id  
                FULL OUTER JOIN patient_signatures ps ON pd._id = ps.patient_document_id
                WHERE COALESCE(pq.patient_id, pd.patient_id) = 'test-patient-009'
                GROUP BY COALESCE(pq.patient_id, pd.patient_id)
            )
            SELECT jsonb_build_object(
                'questionnaires', questionnaire_count,
                'documents', document_count, 
                'answers', answer_count,
                'signatures', signature_count
            )
            FROM patient_summary
            INTO patient_tasks;
            
            IF (patient_tasks->>'questionnaires')::INTEGER >= 1 AND 
               (patient_tasks->>'documents')::INTEGER >= 1 AND
               (patient_tasks->>'answers')::INTEGER >= 1 AND
               (patient_tasks->>'signatures')::INTEGER >= 1 THEN
                test_result := TRUE;
                RAISE NOTICE '[PASS] %: Cross-table relationships working correctly', test_name;
                passed_tests := passed_tests + 1;
            ELSE
                test_result := FALSE;
                RAISE NOTICE '[FAIL] %: Cross-table relationships failed', test_name;
                failed_tests := failed_tests + 1;
            END IF;
        END;
        
        -- Cleanup
        DELETE FROM patient_signatures WHERE _id = 'test-sig-002';
        DELETE FROM patient_answers WHERE _id = 'test-answer-005';
        DELETE FROM patient_documents WHERE _id = 'test-doc-assign-002';
        DELETE FROM patient_questionnaires WHERE _id = 'test-assign-008';
        DELETE FROM documents WHERE _id = 'test-doc-002';
        DELETE FROM questionnaires WHERE _id = 'test-quest-009';
        
    EXCEPTION
        WHEN OTHERS THEN
            test_result := FALSE;
            RAISE NOTICE '[FAIL] %: Exception - %', test_name, SQLERRM;
            failed_tests := failed_tests + 1;
    END;

    -- Test Results Summary
    -- ====================
    RAISE NOTICE '';
    RAISE NOTICE '=====================================';
    RAISE NOTICE 'TEST SUITE RESULTS';
    RAISE NOTICE '=====================================';
    RAISE NOTICE 'Total Tests: %', test_count;
    RAISE NOTICE 'Passed: %', passed_tests;
    RAISE NOTICE 'Failed: %', failed_tests;
    RAISE NOTICE 'Success Rate: %%%', ROUND((passed_tests::DECIMAL / test_count::DECIMAL) * 100, 1);
    RAISE NOTICE '';
    
    IF failed_tests = 0 THEN
        RAISE NOTICE '🎉 ALL TESTS PASSED! Questionnaire system is ready for production.';
    ELSE
        RAISE NOTICE '⚠️  Some tests failed. Please review the failures above.';
    END IF;
    
    RAISE NOTICE '=====================================';

END $$;

-- Performance Test Queries
-- ========================

-- Test query performance for common operations
-- These can be run separately to analyze performance

/*
-- Query 1: Get all pending questionnaires for a patient with question details
EXPLAIN ANALYZE
SELECT 
    q.title,
    q.description,
    q.category,
    q.instructions,
    jsonb_array_length(q.questions) as question_count,
    pq.assigned_at,
    pq.due_date,
    pq.status
FROM patient_questionnaires pq
JOIN questionnaires q ON pq.questionnaire_id = q._id
WHERE pq.patient_id = 'test-patient-001' 
  AND pq.status IN ('assigned', 'in_progress')
ORDER BY pq.due_date ASC;

-- Query 2: Get questionnaire completion statistics
EXPLAIN ANALYZE
SELECT 
    q.title,
    q.category,
    COUNT(pq._id) as total_assignments,
    COUNT(CASE WHEN pq.status = 'completed' THEN 1 END) as completed,
    COUNT(CASE WHEN pq.status = 'in_progress' THEN 1 END) as in_progress,
    COUNT(CASE WHEN pq.status = 'assigned' THEN 1 END) as pending,
    ROUND(
        COUNT(CASE WHEN pq.status = 'completed' THEN 1 END)::DECIMAL / 
        NULLIF(COUNT(pq._id), 0) * 100, 1
    ) as completion_rate
FROM questionnaires q
LEFT JOIN patient_questionnaires pq ON q._id = pq.questionnaire_id
WHERE q.is_active = true
GROUP BY q._id, q.title, q.category
ORDER BY completion_rate DESC;

-- Query 3: Get patient answers with question details  
EXPLAIN ANALYZE
SELECT 
    q.title as questionnaire_title,
    jsonb_array_elements(q.questions)->>'question_text' as question_text,
    jsonb_array_elements(q.questions)->>'question_type' as question_type,
    pa.answer_text,
    pa.answer_number,
    pa.answer_choices,
    pa.answer_date,
    pa.answered_at
FROM patient_questionnaires pq
JOIN questionnaires q ON pq.questionnaire_id = q._id
JOIN patient_answers pa ON pq._id = pa.patient_questionnaire_id
WHERE pq.patient_id = 'test-patient-001'
  AND pq.status = 'completed'
ORDER BY pq.completed_at DESC, pa.answered_at ASC;

-- Query 4: Get pending tasks (combined questionnaires and documents)
EXPLAIN ANALYZE
WITH pending_questionnaires AS (
    SELECT 
        'questionnaire' as task_type,
        pq._id as task_id,
        q.title,
        q.description,
        pq.assigned_at,
        pq.due_date,
        CASE 
            WHEN q.is_required THEN 'high'
            WHEN pq.due_date <= NOW() + INTERVAL '24 hours' THEN 'urgent'
            ELSE 'normal'
        END as priority
    FROM patient_questionnaires pq
    JOIN questionnaires q ON pq.questionnaire_id = q._id
    WHERE pq.patient_id = 'test-patient-001'
      AND pq.status IN ('assigned', 'in_progress')
),
pending_documents AS (
    SELECT 
        'document' as task_type,
        pd._id as task_id,
        d.title,
        CASE d.document_type
            WHEN 'consent_form' THEN 'Please review and sign this consent form'
            WHEN 'privacy_notice' THEN 'Please review our privacy notice'
            ELSE 'Please review and sign this document'
        END as description,
        pd.assigned_at,
        pd.expires_at as due_date,
        CASE 
            WHEN d.requires_signature THEN 'high'
            WHEN pd.expires_at <= NOW() + INTERVAL '24 hours' THEN 'urgent'
            ELSE 'normal'
        END as priority
    FROM patient_documents pd
    JOIN documents d ON pd.document_id = d._id
    WHERE pd.patient_id = 'test-patient-001'
      AND pd.status IN ('assigned', 'viewed')
)
SELECT * FROM pending_questionnaires
UNION ALL
SELECT * FROM pending_documents
ORDER BY 
    CASE priority 
        WHEN 'urgent' THEN 1 
        WHEN 'high' THEN 2 
        ELSE 3 
    END,
    due_date ASC NULLS LAST;
*/

COMMIT;

-- End of Questionnaire System Test Suite
-- ======================================