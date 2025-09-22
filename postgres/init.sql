DROP TABLE IF EXISTS embeddings;

CREATE TABLE embeddings (
  id SERIAL PRIMARY KEY,
  file_name TEXT NOT NULL,
  chunk_index INTEGER NOT NULL,
  original_text TEXT NOT NULL,
  embedding VECTOR(384),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);