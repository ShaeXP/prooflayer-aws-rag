-- Create tables for documents and chunks with pgvector support

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    trace_id TEXT NOT NULL,
    source_bucket TEXT NOT NULL,
    source_key TEXT NOT NULL,
    filename TEXT NOT NULL
);

-- Chunks table with vector embeddings
CREATE TABLE IF NOT EXISTS chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    trace_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536) NOT NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_documents_trace_id ON documents(trace_id);
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_trace_id ON chunks(trace_id);

-- Vector similarity index (IVFFlat for approximate nearest neighbor search)
-- Note: This index requires at least some data to be effective
-- You may want to create this after initial data load:
-- CREATE INDEX idx_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- For initial setup, we'll use a simpler index
-- Uncomment and run after you have some data:
-- CREATE INDEX idx_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

