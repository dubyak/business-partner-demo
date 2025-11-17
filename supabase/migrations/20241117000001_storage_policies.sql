-- =====================================================
-- Storage Bucket and Policies
-- =====================================================
-- Migration: 20241117000001_storage_policies
-- Description: Creates storage bucket and RLS policies for photo uploads
-- =====================================================

-- Create storage bucket for business photos
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'business-photos',
    'business-photos',
    false,
    5242880, -- 5MB
    ARRAY['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
) ON CONFLICT (id) DO NOTHING;

-- =====================================================
-- Storage Object Policies
-- =====================================================

-- Policy 1: Users can upload their own photos
CREATE POLICY "Users can upload own photos"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (
    bucket_id = 'business-photos' AND
    (storage.foldername(name))[1] = auth.uid()::text
);

-- Policy 2: Users can view their own photos
CREATE POLICY "Users can view own photos"
ON storage.objects FOR SELECT
TO authenticated
USING (
    bucket_id = 'business-photos' AND
    (storage.foldername(name))[1] = auth.uid()::text
);

-- Policy 3: Users can update their own photos
CREATE POLICY "Users can update own photos"
ON storage.objects FOR UPDATE
TO authenticated
USING (
    bucket_id = 'business-photos' AND
    (storage.foldername(name))[1] = auth.uid()::text
)
WITH CHECK (
    bucket_id = 'business-photos' AND
    (storage.foldername(name))[1] = auth.uid()::text
);

-- Policy 4: Users can delete their own photos
CREATE POLICY "Users can delete own photos"
ON storage.objects FOR DELETE
TO authenticated
USING (
    bucket_id = 'business-photos' AND
    (storage.foldername(name))[1] = auth.uid()::text
);

-- =====================================================
-- Storage path structure: {user_id}/{filename}
-- Example: 123e4567-e89b-12d3-a456-426614174000/store-photo.jpg
-- =====================================================

