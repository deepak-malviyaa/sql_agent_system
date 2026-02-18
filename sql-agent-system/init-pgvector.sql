-- Initialization script for PostgreSQL with pgvector
-- This file is automatically executed when the container starts for the first time
-- Place this in /docker-entrypoint-initdb.d/ directory

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_extension WHERE extname = 'vector'
    ) THEN
        RAISE EXCEPTION 'pgvector extension installation failed!';
    END IF;
    
    RAISE NOTICE '✅ pgvector extension successfully installed';
END $$;

-- Show pgvector version
SELECT extversion as pgvector_version 
FROM pg_extension 
WHERE extname = 'vector';

-- Optional: Create test table to verify vector type works
CREATE TABLE IF NOT EXISTS vector_test (
    id SERIAL PRIMARY KEY,
    embedding vector(3),
    description TEXT
);

-- Insert test data
INSERT INTO vector_test (embedding, description) VALUES
    ('[1, 2, 3]', 'Test vector 1'),
    ('[4, 5, 6]', 'Test vector 2');

-- Test vector operations
DO $$
DECLARE
    test_result NUMERIC;
BEGIN
    -- Test cosine distance
    SELECT embedding <=> '[1, 2, 3]'::vector INTO test_result
    FROM vector_test
    LIMIT 1;
    
    RAISE NOTICE '✅ Vector operations working! Test distance: %', test_result;
END $$;

-- Clean up test table (optional - comment out to keep)
-- DROP TABLE vector_test;

RAISE NOTICE '============================================';
RAISE NOTICE 'pgvector initialization complete!';
RAISE NOTICE 'Database: entegris_db';
RAISE NOTICE 'Extension: vector';
RAISE NOTICE '============================================';
