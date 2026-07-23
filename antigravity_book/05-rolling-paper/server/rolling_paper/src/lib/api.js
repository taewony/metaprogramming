
import { supabase } from './supabaseClient'

export const fetchBoard = async (boardId) => {
  const { data, error } = await supabase
    .from('boards')
    .select('*')
    .eq('id', boardId)
    .single()
  
  if (error) throw error
  return data
}

export const fetchBoardBySlug = async (slug) => {
  const { data, error } = await supabase
    .from('boards')
    .select('*')
    .eq('slug', slug)
    .single()
  
  if (error) throw error
  return data
}

export const createPostIt = async (postItData) => {
  const { data, error } = await supabase
    .from('messages')
    .insert([postItData])
    .select()
    .single()

  if (error) throw error
  return data
}

export const fetchMessages = async (boardId) => {
  const { data, error } = await supabase
    .from('messages')
    .select('*')
    .eq('board_id', boardId)
  
  if (error) throw error
  return data
}

export const updateMessagePosition = async (id, newConfig) => {
  // Fetch current data first to merge config
  const { data: current, error: fetchError } = await supabase
    .from('messages')
    .select('design_config')
    .eq('id', id)
    .single()

  if (fetchError) throw fetchError
  if (!current) throw new Error('Message not found')

  const updatedConfig = { ...current.design_config, ...newConfig }

  const { data, error } = await supabase
    .from('messages')
    .update({ design_config: updatedConfig })
    .eq('id', id)
    .select()
    .single()

  if (error) throw error
  return data
}

export const updateMessageContent = async (id, { content, sender_name, color }) => {
  // We need to update content, sender_name, and also the color in design_config
  // First, fetch current design_config to preserve x, y, rotation
  const { data: current, error: fetchError } = await supabase
    .from('messages')
    .select('design_config')
    .eq('id', id)
    .single()

  if (fetchError) throw fetchError

  const updatedConfig = { 
    ...current.design_config, 
    color: color // Update color
  }

  const { data, error } = await supabase
    .from('messages')
    .update({ 
      content, 
      sender_name,
      design_config: updatedConfig
    })
    .eq('id', id)
    .select()
    .single()

  if (error) throw error
  return data
}
