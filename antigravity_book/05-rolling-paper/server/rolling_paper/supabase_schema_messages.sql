-- Create messages table for Post-its
CREATE TABLE IF NOT EXISTS messages (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  board_id UUID NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
  user_id UUID REFERENCES auth.users(id), -- Nullable for anonymous, but we'll use auth for now
  content TEXT NOT NULL CHECK (char_length(content) <= 200),
  nickname TEXT NOT NULL CHECK (char_length(nickname) <= 10),
  color TEXT NOT NULL,
  x FLOAT NOT NULL,
  y FLOAT NOT NULL,
  rotation FLOAT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
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
WITH CHECK (true); -- You might want to stricter checks later, e.g., checking board existence or user link

-- Policy: Authors can update their own messages (for moving)
CREATE POLICY "authors_can_update_messages"
ON messages FOR UPDATE
TO authenticated
USING (auth.uid() = user_id);

-- Realtime
ALTER PUBLICATION supabase_realtime ADD TABLE messages;
