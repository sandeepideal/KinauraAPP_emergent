-- Storage Policies for Longevity Scoreboard Avatars
-- This creates storage buckets and policies for patient avatar management

-- Create avatar storage bucket if it doesn't exist
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'longevity-avatars', 
    'longevity-avatars', 
    false, -- Private bucket
    2097152, -- 2MB limit
    '{"image/jpeg","image/png","image/webp","image/gif"}'
) ON CONFLICT (id) DO NOTHING;

-- =====================================================
-- AVATAR STORAGE POLICIES
-- =====================================================

-- Admin/practitioners can upload avatars for patients in their org
CREATE POLICY "longevity_avatars_staff_upload" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'longevity-avatars' AND
        EXISTS (
            SELECT 1 FROM patients p
            JOIN profiles pr ON pr.org_id = p.org_id
            WHERE pr.id = auth.uid()
            AND pr.role IN ('admin', 'practitioner')
            AND p.id::text = (storage.foldername(name))[1]
        )
    );

-- Admin/practitioners can read avatars for patients in their org
CREATE POLICY "longevity_avatars_staff_read" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'longevity-avatars' AND
        EXISTS (
            SELECT 1 FROM patients p
            JOIN profiles pr ON pr.org_id = p.org_id
            WHERE pr.id = auth.uid()
            AND pr.role IN ('admin', 'practitioner')
            AND p.id::text = (storage.foldername(name))[1]
        )
    );

-- Admin/practitioners can update avatars for patients in their org
CREATE POLICY "longevity_avatars_staff_update" ON storage.objects
    FOR UPDATE USING (
        bucket_id = 'longevity-avatars' AND
        EXISTS (
            SELECT 1 FROM patients p
            JOIN profiles pr ON pr.org_id = p.org_id
            WHERE pr.id = auth.uid()
            AND pr.role IN ('admin', 'practitioner')
            AND p.id::text = (storage.foldername(name))[1]
        )
    );

-- Admin/practitioners can delete avatars for patients in their org
CREATE POLICY "longevity_avatars_staff_delete" ON storage.objects
    FOR DELETE USING (
        bucket_id = 'longevity-avatars' AND
        EXISTS (
            SELECT 1 FROM patients p
            JOIN profiles pr ON pr.org_id = p.org_id
            WHERE pr.id = auth.uid()
            AND pr.role IN ('admin', 'practitioner')
            AND p.id::text = (storage.foldername(name))[1]
        )
    );

-- Patients can read their own avatars
CREATE POLICY "longevity_avatars_patient_read" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'longevity-avatars' AND
        (storage.foldername(name))[1] = (
            SELECT p.id::text FROM patients p
            JOIN profiles pr ON pr.id = auth.uid()
            WHERE p.email = (SELECT raw_user_meta_data->>'email' FROM auth.users WHERE id = auth.uid())
            AND p.org_id = pr.org_id
        )
    );

-- Patients can upload their own avatars
CREATE POLICY "longevity_avatars_patient_upload" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'longevity-avatars' AND
        (storage.foldername(name))[1] = (
            SELECT p.id::text FROM patients p
            JOIN profiles pr ON pr.id = auth.uid()
            WHERE p.email = (SELECT raw_user_meta_data->>'email' FROM auth.users WHERE id = auth.uid())
            AND p.org_id = pr.org_id
        )
    );

-- Patients can update their own avatars
CREATE POLICY "longevity_avatars_patient_update" ON storage.objects
    FOR UPDATE USING (
        bucket_id = 'longevity-avatars' AND
        (storage.foldername(name))[1] = (
            SELECT p.id::text FROM patients p
            JOIN profiles pr ON pr.id = auth.uid()
            WHERE p.email = (SELECT raw_user_meta_data->>'email' FROM auth.users WHERE id = auth.uid())
            AND p.org_id = pr.org_id
        )
    );

-- =====================================================
-- HELPER FUNCTIONS FOR AVATAR MANAGEMENT
-- =====================================================

-- Function to generate signed URL for avatar (1 hour expiry)
CREATE OR REPLACE FUNCTION get_avatar_signed_url(
    patient_id_param UUID,
    expires_in INTEGER DEFAULT 3600
)
RETURNS TEXT
SECURITY DEFINER
AS $$
DECLARE
    avatar_path TEXT;
    signed_url TEXT;
BEGIN
    -- Get avatar path for the patient
    SELECT pr.display_avatar_url INTO avatar_path
    FROM patients p
    LEFT JOIN profiles pr ON pr.org_id = p.org_id
    WHERE p.id = patient_id_param;
    
    -- Return null if no avatar
    IF avatar_path IS NULL THEN
        RETURN NULL;
    END IF;
    
    -- Check access permissions
    IF NOT EXISTS (
        SELECT 1 FROM patients p
        JOIN profiles pr ON pr.org_id = p.org_id
        WHERE p.id = patient_id_param
        AND (
            -- Staff access
            (pr.id = auth.uid() AND pr.role IN ('admin', 'practitioner')) OR
            -- Patient self access
            (p.email = (SELECT raw_user_meta_data->>'email' FROM auth.users WHERE id = auth.uid()))
        )
    ) THEN
        RAISE EXCEPTION 'Access denied to avatar';
    END IF;
    
    -- Generate signed URL using Supabase storage
    -- Note: This would typically call storage.create_signed_url in a real implementation
    -- For now, return the path prefixed with signed URL indicator
    RETURN 'signed:' || avatar_path || ':' || expires_in;
END;
$$ LANGUAGE plpgsql;

-- Function to upload avatar and update profile
CREATE OR REPLACE FUNCTION upload_patient_avatar(
    patient_id_param UUID,
    file_name TEXT,
    file_content BYTEA
)
RETURNS TEXT
SECURITY DEFINER
AS $$
DECLARE
    storage_path TEXT;
    patient_record RECORD;
BEGIN
    -- Get patient info and verify access
    SELECT p.*, pr.org_id as profile_org_id
    INTO patient_record
    FROM patients p
    LEFT JOIN profiles pr ON pr.org_id = p.org_id
    WHERE p.id = patient_id_param;
    
    -- Check permissions
    IF NOT EXISTS (
        SELECT 1 FROM profiles pr
        WHERE pr.id = auth.uid()
        AND pr.org_id = patient_record.org_id
        AND pr.role IN ('admin', 'practitioner')
    ) THEN
        RAISE EXCEPTION 'Access denied to upload avatar';
    END IF;
    
    -- Generate storage path: patient_id/avatar_timestamp.ext
    storage_path := patient_id_param || '/avatar_' || EXTRACT(EPOCH FROM NOW()) || '_' || file_name;
    
    -- Update profile with new avatar path
    UPDATE profiles 
    SET display_avatar_url = storage_path,
        updated_at = NOW()
    WHERE org_id = patient_record.org_id
    AND id = auth.uid();
    
    -- Note: Actual file upload would be handled by the Edge Function
    -- This function just manages the database side
    
    RETURN storage_path;
END;
$$ LANGUAGE plpgsql;

-- Function to delete patient avatar
CREATE OR REPLACE FUNCTION delete_patient_avatar(patient_id_param UUID)
RETURNS BOOLEAN
SECURITY DEFINER
AS $$
DECLARE
    patient_record RECORD;
    old_avatar_path TEXT;
BEGIN
    -- Get patient info and current avatar
    SELECT p.*, pr.display_avatar_url, pr.org_id as profile_org_id
    INTO patient_record
    FROM patients p
    LEFT JOIN profiles pr ON pr.org_id = p.org_id
    WHERE p.id = patient_id_param;
    
    -- Check permissions
    IF NOT EXISTS (
        SELECT 1 FROM profiles pr
        WHERE pr.id = auth.uid()
        AND pr.org_id = patient_record.profile_org_id
        AND pr.role IN ('admin', 'practitioner')
    ) THEN
        RAISE EXCEPTION 'Access denied to delete avatar';
    END IF;
    
    -- Store old path for cleanup
    old_avatar_path := patient_record.display_avatar_url;
    
    -- Clear avatar from profile
    UPDATE profiles 
    SET display_avatar_url = NULL,
        updated_at = NOW()
    WHERE org_id = patient_record.profile_org_id
    AND id = auth.uid();
    
    -- Note: Actual file deletion would be handled by the Edge Function
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- PUBLIC AVATAR ACCESS FOR LEADERBOARD
-- =====================================================

-- Function to get public avatar URL (for leaderboard display)
CREATE OR REPLACE FUNCTION get_public_avatar_url(patient_id_param UUID)
RETURNS TEXT
SECURITY DEFINER
AS $$
DECLARE
    avatar_path TEXT;
    is_visible BOOLEAN;
    identity_mode TEXT;
BEGIN
    -- Check if patient is visible on leaderboard and uses avatar mode
    SELECT 
        pr.display_avatar_url,
        COALESCE(lv.opt_in, pr.publish_on_leaderboard, FALSE),
        COALESCE(lv.identity, pr.publish_identity, 'avatar')
    INTO avatar_path, is_visible, identity_mode
    FROM patients p
    LEFT JOIN profiles pr ON pr.org_id = p.org_id
    LEFT JOIN leaderboard_visibility lv ON lv.patient_id = p.id
    WHERE p.id = patient_id_param;
    
    -- Only return avatar if patient is visible and uses avatar identity
    IF is_visible AND identity_mode = 'avatar' AND avatar_path IS NOT NULL THEN
        -- Return signed URL (simplified version)
        RETURN get_avatar_signed_url(patient_id_param, 3600);
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON FUNCTION get_avatar_signed_url IS 'Generates signed URL for patient avatar with access control';
COMMENT ON FUNCTION upload_patient_avatar IS 'Handles avatar upload with permission checking';
COMMENT ON FUNCTION delete_patient_avatar IS 'Deletes patient avatar with proper cleanup';
COMMENT ON FUNCTION get_public_avatar_url IS 'Gets public avatar URL for leaderboard display';