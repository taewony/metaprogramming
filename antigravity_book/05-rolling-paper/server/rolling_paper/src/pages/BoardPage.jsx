import { useState, useEffect, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { fetchBoardBySlug, fetchMessages, createPostIt, updateMessagePosition, updateMessageContent } from '../lib/api'
import { ThemeToggle } from '../components/ThemeToggle'
import PostItModal from '../components/PostItModal'
import { Plus } from 'lucide-react'
import { motion } from 'framer-motion'
import { supabase } from '../lib/supabaseClient'

export default function BoardPage({ session }) {
  const { slug } = useParams()
  const [board, setBoard] = useState(null)
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(true)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [createLoading, setCreateLoading] = useState(false)
  const [editingMessage, setEditingMessage] = useState(null) // State for editing
  const constraintsRef = useRef(null)

  useEffect(() => {
    loadData()
  }, [slug])

  useEffect(() => {
    if (!board?.id) return

    const channel = supabase
      .channel('board-realtime')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'messages',
          filter: `board_id=eq.${board.id}`,
        },
        (payload) => {
          if (payload.eventType === 'INSERT') {
            setMessages((prev) => [...prev, payload.new])
          } else if (payload.eventType === 'UPDATE') {
            setMessages((prev) =>
              prev.map((msg) => (msg.id === payload.new.id ? payload.new : msg))
            )
          } else if (payload.eventType === 'DELETE') {
            setMessages((prev) =>
              prev.filter((msg) => msg.id !== payload.old.id)
            )
          }
        }
      )
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'boards',
          filter: `id=eq.${board.id}`,
        },
        (payload) => {
          setBoard((prev) => ({ ...prev, ...payload.new }))
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [board?.id])

  const loadData = async () => {
    try {
      setLoading(true)
      const boardData = await fetchBoardBySlug(slug)
      if (boardData) {
        const messagesData = await fetchMessages(boardData.id)
        setBoard(boardData)
        setMessages(messagesData)
      }
    } catch (error) {
      console.error('Failed to load board:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateOrUpdatePostIt = async (data) => {
    try {
      setCreateLoading(true)
      
      if (editingMessage) {
        // Update existing
        await updateMessageContent(editingMessage.id, data)
        setEditingMessage(null)
      } else {
        // Create new
        const x = 400 + (Math.random() * 300 - 150)
        const y = 300 + (Math.random() * 300 - 150)
        const rotation = Math.random() * 10 - 5 
  
        const newPostIt = {
          board_id: board.id,
          sender_name: data.sender_name,
          content: data.content,
          design_config: {
            color: data.color,
            x,
            y,
            rotation
          },
          author_id: session?.user?.id,
          is_anonymous: false
        }
  
        await createPostIt(newPostIt)
      }
      setIsModalOpen(false)
    } catch (error) {
      console.error('Failed to save post-it:', error)
      alert('저장 실패: ' + error.message)
    } finally {
      setCreateLoading(false)
    }
  }

  const handleDragEnd = async (result, info, msg) => {
    const currentConfig = msg.design_config || {}
    const oldX = currentConfig.x || 0
    const oldY = currentConfig.y || 0
    
    const newX = oldX + info.offset.x
    const newY = oldY + info.offset.y
    
    const updatedMsg = {
      ...msg,
      design_config: {
        ...currentConfig,
        x: newX,
        y: newY
      }
    }
    
    setMessages(prev => prev.map(m => m.id === msg.id ? updatedMsg : m))

    try {
       await updateMessagePosition(msg.id, { x: newX, y: newY })
    } catch (error) {
      console.error('Failed to update position:', error)
    }
  }

  const handleDoubleClick = (msg) => {
    if (session?.user?.id === msg.author_id) {
      setEditingMessage(msg)
      setIsModalOpen(true)
    }
  }

  const handleModalClose = () => {
    setIsModalOpen(false)
    setEditingMessage(null)
  }

  if (loading) return <div className="text-gray-900 dark:text-white text-center mt-20">Loading board...</div>
  if (!board) return <div className="text-gray-900 dark:text-white text-center mt-20">Board not found</div>

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 overflow-hidden relative selection:bg-indigo-500/30 transition-colors duration-300">
      
      {/* Background Grid Pattern */}
      <div className="absolute inset-0 opacity-10 pointer-events-none"
           style={{ backgroundImage: 'radial-gradient(circle, currentColor 1px, transparent 1px)', backgroundSize: '20px 20px' }} 
      />

      {/* Header */}
      <nav className="relative z-10 flex justify-between p-6 items-center bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-gray-200 dark:border-white/10 transition-colors duration-300">
        <div className="flex items-center gap-4">
          <Link to="/" className="text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors">
            ← Back
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white max-w-lg truncate">{board.title}</h1>
        </div>
        <div className="flex items-center gap-4">
          <ThemeToggle />
          {session ? (
            <button 
              onClick={() => {
                setEditingMessage(null)
                setIsModalOpen(true)
              }}
              className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-2.5 rounded-full shadow-lg hover:shadow-indigo-500/30 transition-all font-medium"
            >
              <Plus size={20} />
              <span>메시지 남기기</span>
            </button>
          ) : (
            <Link to="/" className="text-indigo-400 hover:text-indigo-300 text-sm font-medium">
              로그인하고 메시지 남기기
            </Link>
          )}
        </div>
      </nav>

      {/* Canvas Area */}
      <main className="relative w-full h-[calc(100vh-80px)] overflow-auto scrollbar-hide" ref={constraintsRef}>
        <div className="relative min-w-[2000px] min-h-[2000px]">
           {/* Render Post-its */}
           {messages.map(msg => {
             const config = msg.design_config || {}
             const { color = 'bg-yellow-100', x = 0, y = 0, rotation = 0 } = config
             const isOwner = session?.user?.id === msg.author_id
             
             return (
               <motion.div
                 key={msg.id}
                 drag={isOwner} // Only owner can drag
                 dragMomentum={false}
                 dragConstraints={constraintsRef}
                 onDragEnd={(e, info) => handleDragEnd(null, info, msg)}
                 onDoubleClick={() => handleDoubleClick(msg)}
                 initial={{ x: 0, y: 0 }} 
                 className={`${color} absolute p-6 shadow-lg rounded-sm cursor-pointer flex flex-col justify-between ${isOwner ? 'hover:scale-105 active:scale-110 active:z-50' : ''}`}
                 style={{
                   left: x,
                   top: y,
                   width: '240px',
                   height: '240px',
                   rotate: rotation, 
                   zIndex: isOwner ? 10 : 1, 
                 }}
                 whileTap={{ scale: 1.1, cursor: 'grabbing' }}
                 whileHover={{ scale: 1.05 }}
               >
                 <p className="text-gray-800 font-handwriting text-lg leading-relaxed break-words font-medium select-none">
                   {msg.content}
                 </p>
                 <div className="mt-4 text-right text-sm text-gray-600 font-bold opacity-80 select-none">
                   - {msg.sender_name}
                 </div>
               </motion.div>
             )
           })}
        </div>
      </main>

      <PostItModal 
        isOpen={isModalOpen}
        onClose={handleModalClose}
        onSubmit={handleCreateOrUpdatePostIt}
        loading={createLoading}
        initialData={editingMessage}
      />
    </div>
  )
}
