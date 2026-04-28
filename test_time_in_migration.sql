-- ============================================================================
-- TEST SCRIPT: time_in NULL Migration
-- ============================================================================
-- This script tests the migration logic for making attendances.time_in nullable
-- Run this AFTER the attendances table exists in your database
-- ============================================================================

-- Step 1: Check if attendances table exists
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_name = 'attendances'
) AS attendances_table_exists;

-- Step 2: Check current time_in column definition
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'attendances' 
  AND column_name = 'time_in';

-- Step 3: Test the migration SQL (ALTER COLUMN)
-- UNCOMMENT BELOW TO RUN THE ACTUAL MIGRATION:
-- ALTER TABLE attendances 
-- ALTER COLUMN time_in DROP NOT NULL,
-- ALTER COLUMN time_in DROP DEFAULT;

-- Step 4: Verify the change
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'attendances' 
  AND column_name = 'time_in';

-- Step 5: Test inserting a NULL value
-- UNCOMMENT TO TEST:
-- INSERT INTO attendances (student_id, event_id, time_in, method, status)
-- VALUES (1, 1, NULL, NULL, 'absent')
-- RETURNING id, student_id, event_id, time_in, method, status;

-- Step 6: Clean up test record
-- DELETE FROM attendances WHERE student_id = 1 AND event_id = 1;

-- ============================================================================
-- EXPECTED RESULTS:
-- ============================================================================
-- Before migration:
--   is_nullable: NO
--   column_default: (some default function)
--
-- After migration:
--   is_nullable: YES
--   column_default: NULL
--
-- Test insert should succeed with time_in = NULL and method = NULL
-- ============================================================================
