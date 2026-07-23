import { useState, useEffect } from 'react'
import { X } from 'lucide-react'

const COLORS = [
  { name: 'Warm Yellow', value: 'bg-amber-100' },
  { name: 'Soft Pink', value: 'bg-pink-100' },
  { name: 'Calm Blue', value: 'bg-blue-100' },
  { name: 'Mint Green', value: 'bg-emerald-100' },
  { name: 'Lavender', value: 'bg-violet-100' },
]

export default function PostItModal({ isOpen, onClose, onSubmit, loading, initialData = null }) {
  const [content, setContent] = useState('')
  const [senderName, setSenderName] = useState('')
  const [selectedColor, setSelectedColor] = useState(COLORS[0].value)

  useEffect(() => {
    if (isOpen) {
      if (initialData) {
        setContent(initialData.content || '')
        setSenderName(initialData.sender_name || '')
        setSelectedColor(initialData.design_config?.color || COLORS[0].value)
      } else {
        setContent('')
        setSenderName('')
        setSelectedColor(COLORS[0].value)
      }
    }
  }, [isOpen, initialData])

  if (!isOpen) return null

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit({
      content,
      sender_name: senderName,
      color: selectedColor
    })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="relative w-full max-w-md bg-white dark:bg-slate-800 rounded-2xl shadow-xl overflow-hidden animate-in fade-in zoom-in duration-200 transition-colors">
        
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b dark:border-white/10">
          <h2 className="text-lg font-bold text-gray-900 dark:text-white">
            {initialData ? '메시지 수정하기' : '포스트잇 작성하기'}
          </h2>
          <button 
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 rounded-full hover:bg-gray-100 dark:hover:bg-white/10 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          
          {/* Content */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              내용 ({content.length}/200)
            </label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value.slice(0, 200))}
              placeholder="따뜻한 마음을 전해주세요..."
              rows={4}
              required
              className={`w-full p-4 rounded-xl resize-none border-none focus:ring-2 focus:ring-indigo-500 transition-all ${selectedColor} text-gray-800 placeholder-gray-500`}
            />
          </div>

          {/* Nickname -> sender_name */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              닉네임 ({senderName.length}/10)
            </label>
            <input
              type="text"
              value={senderName}
              onChange={(e) => setSenderName(e.target.value.slice(0, 10))}
              placeholder="별명 입력"
              required
              className="w-full px-4 py-3 border rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all dark:bg-slate-900 dark:border-slate-700 dark:text-white"
            />
          </div>

          {/* Color Picker */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              배경색 선택
            </label>
            <div className="flex gap-3">
              {COLORS.map((color) => (
                <button
                  key={color.name}
                  type="button"
                  onClick={() => setSelectedColor(color.value)}
                  className={`w-8 h-8 rounded-full border-2 transition-all ${color.value} ${
                    selectedColor === color.value 
                      ? 'border-indigo-600 scale-110 shadow-md' 
                      : 'border-transparent hover:scale-105'
                  }`}
                  aria-label={color.name}
                />
              ))}
            </div>
          </div>

          {/* Footer */}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-4 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl shadow-lg shadow-indigo-600/20 hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (initialData ? '수정 중...' : '등록 중...') : (initialData ? '수정완료' : '등록하기')}
          </button>
        </form>

      </div>
    </div>
  )
}
