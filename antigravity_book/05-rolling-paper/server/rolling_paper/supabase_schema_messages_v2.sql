-- Drop existing messages table if it exists to reset schema safely (CAUTION: Data loss)
-- DROP TABLE IF EXISTS messages; 
-- Or just create if not exists and note that user might need to migrate manually if they already created it.

CREATE TABLE IF NOT EXISTS messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMPTZ DEFAULT now(),
  board_id UUID NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
  sender_name TEXT NOT NULL,
  content TEXT NOT NULL,
  design_config JSONB DEFAULT '{}'::jsonb,
  author_id UUID REFERENCES auth.users(id),
  is_anonymous BOOLEAN DEFAULT false
);

-- Enable RLS
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Policy: Everyone can view messages
CREATE POLICY "everyone_can_view_messages"
ON messages FOR SELECT
USING (true);

-- Policy: Authenticated users can create messages
CREATE POLICY "authenticated_users_can_create_messages"
ON messages FOR INSERT
TO authenticated
WITH CHECK (true);

-- Policy: Authors can update their own messages (id check or author_id check)
CREATE POLICY "authors_can_update_messages"
ON messages FOR UPDATE
TO authenticated
USING (auth.uid() = author_id);
