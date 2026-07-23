import React, { useState } from 'react';
import { RiKakaoTalkFill } from 'react-icons/ri';
import { signInWithKakao, signInWithEmail, signUpWithEmail } from '../lib/auth';
import { ThemeToggle } from './ThemeToggle';

const LoginPage = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const handleKakaoLogin = async () => {
    try {
      await signInWithKakao();
    } catch (error) {
      alert("카카오 로그인 중 오류가 발생했습니다.");
    }
  };

  const handleEmailAuth = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setIsLoading(true);

    try {
      if (isSignUp) {
        await signUpWithEmail(email, password);
        alert("회원가입 확인 메일을 전송했습니다. 이메일을 확인해 주세요!");
        setIsSignUp(false);
      } else {
        await signInWithEmail(email, password);
      }
    } catch (error) {
      setErrorMsg(error.message || "오류가 발생했습니다.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-slate-50 dark:bg-[#0f172a] p-4 transition-colors duration-300 relative">
      <div className="absolute top-4 right-4">
        <ThemeToggle />
      </div>
      <div className="w-full max-w-[400px] bg-white dark:bg-slate-800 rounded-2xl shadow-2xl p-8 animate-in fade-in zoom-in duration-300 transition-colors">
        <div className="flex flex-col items-center mb-10">
          <div className="w-16 h-16 bg-indigo-600 rounded-2xl flex items-center justify-center mb-4 shadow-lg shadow-indigo-500/30">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white text-center">
            {isSignUp ? "회원가입" : "로그인하고 마음을 남겨보세요"}
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-2 text-center text-sm">
            {isSignUp ? "새로운 계정을 만들어보세요" : "디지털 롤링페이퍼 서비스에 오신 것을 환영합니다"}
          </p>
        </div>

        <div className="flex flex-col gap-4">
          <button
            onClick={handleKakaoLogin}
            className="flex items-center justify-center w-full py-4 px-4 rounded-xl bg-[#FEE500] hover:bg-[#FDD835] text-black font-bold transition-all active:scale-[0.98] border-none shadow-sm text-base"
          >
            <RiKakaoTalkFill className="w-6 h-6 mr-2 opacity-90" />
            카카오로 3초 만에 시작하기
          </button>

          <div className="relative my-4">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-gray-100" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-white dark:bg-slate-800 px-4 text-gray-400 font-medium transition-colors">
                OR EMAIL
              </span>
            </div>
          </div>

          <form onSubmit={handleEmailAuth} className="flex flex-col gap-4">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 ml-1">이메일 주소</label>
              <input 
                type="email" 
                placeholder="example@email.com" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-4 rounded-xl border border-gray-200 dark:border-gray-700 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 outline-none transition-all text-sm bg-gray-50/50 dark:bg-slate-900 dark:text-white"
                required
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 ml-1">비밀번호</label>
              <input 
                type="password" 
                placeholder="••••••••" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-4 rounded-xl border border-gray-200 dark:border-gray-700 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 outline-none transition-all text-sm bg-gray-50/50 dark:bg-slate-900 dark:text-white"
                required
                minLength={6}
              />
            </div>
            
            {errorMsg && (
              <div className="bg-red-50 p-3 rounded-lg border border-red-100">
                <p className="text-xs text-red-600 text-center font-medium">{errorMsg}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-4 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-indigo-600/20 mt-2"
            >
              {isLoading ? "처리 중..." : (isSignUp ? "회원가입하기" : "이메일로 로그인")}
            </button>
          </form>

          <div className="mt-4 text-center">
            <button
              type="button"
              onClick={() => {
                setIsSignUp(!isSignUp);
                setErrorMsg('');
              }}
              className="text-sm font-semibold text-indigo-600 hover:text-indigo-700 transition-colors bg-transparent border-none p-0 w-auto inline-flex items-center"
            >
              {isSignUp ? "이미 계정이 있으신가요? 로그인" : "아직 계정이 없으신가요? 회원가입"}
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="ml-1"><path d="M5 12h14"></path><path d="m12 5 7 7-7 7"></path></svg>
            </button>
          </div>
        </div>

        <div className="mt-10 text-center border-t border-gray-50 pt-6">
          <p className="text-[11px] text-gray-400 leading-relaxed uppercase tracking-wider font-medium">
            Copyright © 2026 Rolling Paper Studio.<br/>All rights reserved.
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
