-- Storage configuration for KinAura
-- This sets up storage buckets and policies for patient files

-- Create storage buckets
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES 
    ('patient-images', 'patient-images', false, 52428800, '{"image/jpeg","image/png","image/webp"}'),
    ('patient-docs', 'patient-docs', false, 52428800, '{"application/pdf","image/jpeg","image/png"}'),
    ('chat-attachments', 'chat-attachments', false, 52428800, '{"image/jpeg","image/png","application/pdf","text/plain"}');

-- Storage policies for patient-images bucket
CREATE POLICY "Patient images: patients can read own files" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'patient-images' AND
        (storage.foldername(name))[1] = (
            SELECT p.id::text FROM patients p 
            JOIN profiles pr ON pr.id = auth.uid() 
            WHERE p.email = (SELECT raw_user_meta_data->>'email' FROM auth.users WHERE id = auth.uid())
            AND p.org_id = (SELECT org_id FROM profiles WHERE id = auth.uid())
        )
    );

CREATE POLICY "Patient images: staff can read org files" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'patient-images' AND
        EXISTS (
            SELECT 1 FROM patients p 
            JOIN profiles pr ON pr.org_id = p.org_id
            WHERE pr.id = auth.uid() 
            AND pr.role IN ('admin', 'practitioner')
            AND p.id::text = (storage.foldername(name))[1]
        )
    );

CREATE POLICY "Patient images: staff can upload org files" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'patient-images' AND
        EXISTS (
            SELECT 1 FROM patients p 
            JOIN profiles pr ON pr.org_id = p.org_id
            WHERE pr.id = auth.uid() 
            AND pr.role IN ('admin', 'practitioner')
            AND p.id::text = (storage.foldername(name))[1]
        )
    );

CREATE POLICY "Patient images: staff can delete org files" ON storage.objects
    FOR DELETE USING (
        bucket_id = 'patient-images' AND
        EXISTS (
            SELECT 1 FROM patients p 
            JOIN profiles pr ON pr.org_id = p.org_id
            WHERE pr.id = auth.uid() 
            AND pr.role IN ('admin', 'practitioner')
            AND p.id::text = (storage.foldername(name))[1]
        )
    );

-- Storage policies for patient-docs bucket (similar pattern)
CREATE POLICY "Patient docs: patients can read own files" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'patient-docs' AND
        (storage.foldername(name))[1] = (
            SELECT p.id::text FROM patients p 
            JOIN profiles pr ON pr.id = auth.uid() 
            WHERE p.email = (SELECT raw_user_meta_data->>'email' FROM auth.users WHERE id = auth.uid())
            AND p.org_id = (SELECT org_id FROM profiles WHERE id = auth.uid())
        )
    );

CREATE POLICY "Patient docs: staff can read org files" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'patient-docs' AND
        EXISTS (
            SELECT 1 FROM patients p 
            JOIN profiles pr ON pr.org_id = p.org_id
            WHERE pr.id = auth.uid() 
            AND pr.role IN ('admin', 'practitioner')
            AND p.id::text = (storage.foldername(name))[1]
        )
    );

CREATE POLICY "Patient docs: staff can upload org files" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'patient-docs' AND
        EXISTS (
            SELECT 1 FROM patients p 
            JOIN profiles pr ON pr.org_id = p.org_id
            WHERE pr.id = auth.uid() 
            AND pr.role IN ('admin', 'practitioner')
            AND p.id::text = (storage.foldername(name))[1]
        )
    );

CREATE POLICY "Patient docs: patients can upload own files" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'patient-docs' AND
        (storage.foldername(name))[1] = (
            SELECT p.id::text FROM patients p 
            JOIN profiles pr ON pr.id = auth.uid() 
            WHERE p.email = (SELECT raw_user_meta_data->>'email' FROM auth.users WHERE id = auth.uid())
            AND p.org_id = (SELECT org_id FROM profiles WHERE id = auth.uid())
        )
    );

-- Storage policies for chat-attachments bucket
CREATE POLICY "Chat attachments: thread participants can access" ON storage.objects
    FOR ALL USING (
        bucket_id = 'chat-attachments' AND
        EXISTS (
            SELECT 1 FROM messages m
            JOIN threads t ON t.id = m.thread_id
            WHERE m.id::text = (storage.foldername(name))[1]
            AND (
                t.patient_id = (
                    SELECT p.id FROM patients p 
                    JOIN profiles pr ON pr.id = auth.uid() 
                    WHERE p.email = (SELECT raw_user_meta_data->>'email' FROM auth.users WHERE id = auth.uid())
                    AND p.org_id = (SELECT org_id FROM profiles WHERE id = auth.uid())
                ) OR
                EXISTS (
                    SELECT 1 FROM patients p2 
                    JOIN profiles pr2 ON pr2.org_id = p2.org_id
                    WHERE pr2.id = auth.uid() 
                    AND pr2.role IN ('admin', 'practitioner')
                    AND p2.id = t.patient_id
                )
            )
        )
    );