import { ThemeToggle } from '../components/ThemeToggle'

export default function Home({ session }) {
  // ... existing code ...

  return (
    <div className="container mx-auto min-h-screen flex flex-col dark:text-white">
      <nav className="flex justify-between p-6 items-center">
        <div className="flex items-center gap-2">
          {/* ... logo ... */}
        </div>
        <div className="flex items-center gap-4">
          <ThemeToggle />
          <span className="text-sm text-gray-500 dark:text-gray-400 font-medium">
            {session.user.email}
          </span>
          <button 
            onClick={handleLogout}
            className="!w-auto bg-gray-100 dark:bg-white/5 text-gray-600 dark:text-gray-300 px-4 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-white/10 transition-all border border-gray-200 dark:border-white/10 text-sm font-semibold"
          >
            로그아웃
          </button>
        </div>
      </nav>

      <main className="flex-1 flex items-center justify-center p-4">
        <div className="card w-full max-w-[500px] !m-0">
          <h1>Create New Board</h1>
          <p className="subtitle">누군가에게 당신의 따뜻한 마음을 전달해보세요.</p>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="form-group !mb-0">
              <label htmlFor="title">보드 제목</label>
              <input
                type="text"
                id="title"
                name="title"
                value={formData.title}
                onChange={handleChange}
                placeholder="예: 민수님 생일 축하해!"
                required
              />
            </div>

            <div className="form-group !mb-0">
              <label htmlFor="slug">고유 주소 (Slug)</label>
              <div className="relative flex items-center">
                <span className="absolute left-3 text-gray-500 text-sm font-medium">paper.io/</span>
                <input
                  type="text"
                  id="slug"
                  name="slug"
                  value={formData.slug}
                  onChange={handleChange}
                  className="!pl-20"
                  placeholder="happy-minsoo"
                  required
                />
              </div>
            </div>

            <div className="form-group !mb-0">
              <label htmlFor="description">보드 설명</label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleChange}
                placeholder="보드에 대한 간단한 설명을 적어주세요."
                rows="3"
                className="resize-none"
              />
            </div>

            <button 
              type="submit" 
              disabled={loading}
              className="bg-indigo-600 hover:bg-indigo-500 shadow-lg shadow-indigo-600/20 py-4"
            >
              {loading ? '생성 중...' : '보드 생성하기'}
            </button>
          </form>

          {status.message && (
            <div className={`status-msg mt-6 ${status.type}`}>
              {status.message}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
