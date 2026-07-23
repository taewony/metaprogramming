import React, { useState } from 'react';
import { RiKakaoTalkFill } from 'react-icons/ri';
import { signInWithKakao, signInWithEmail, signUpWithEmail } from '../lib/auth';

const LoginModal = ({ isOpen, onClose, canClose = true }) => {
  if (!isOpen) return null;

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
        // Sign Up
        await signUpWithEmail(email, password);
        alert("회원가입 확인 메일을 전송했습니다. 이메일을 확인해 주세요!");
        setIsSignUp(false);
      } else {
        // Sign In
        await signInWithEmail(email, password);
        // Successful login usually redirects or updates global state, 
        // but for now let's just close modal
        if (canClose && onClose) onClose(); 
      }
    } catch (error) {
      setErrorMsg(error.message || "오류가 발생했습니다.");
    } finally {
      setIsLoading(false);
    }
  };

  // Close modal when clicking outside
  const handleBackdropClick = (e) => {
    if (canClose && e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-in fade-in duration-200"
      onClick={handleBackdropClick}
    >
      <div className="w-full max-w-[350px] bg-white rounded-2xl shadow-2xl p-6 mx-4 animate-in zoom-in-95 duration-200 relative">
        
        {/* Close Button */}
        {canClose && (
          <button 
            onClick={onClose}
            className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 !w-auto !p-1 !bg-transparent"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        )}

        <div className="flex flex-col items-center mb-6 mt-2">
          <h2 className="text-xl font-bold text-gray-900 text-center leading-tight">
            {isSignUp ? "회원가입" : "로그인하고"}<br/>
            {isSignUp ? "새로운 계정을 만들어보세요" : "마음을 남겨보세요"}
          </h2>
          <p className="text-sm text-gray-500 mt-2">
            3초 만에 시작할 수 있어요
          </p>
        </div>

        <div className="flex flex-col gap-3">
          {/* Kakao Button */}
          <button
            onClick={handleKakaoLogin}
            className="flex items-center justify-center w-full py-4 px-4 rounded-xl bg-[#FEE500] hover:bg-[#FDD835] text-black font-bold transition-all active:scale-[0.98] border-none shadow-sm text-base"
          >
            <RiKakaoTalkFill className="w-6 h-6 mr-2 opacity-90" />
            카카오로 3초 만에 시작하기
          </button>

          <div className="relative my-2">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-gray-200" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-white px-2 text-gray-500">
                또는 이메일로 {isSignUp ? "가입" : "로그인"}
              </span>
            </div>
          </div>

          {/* Email Form */}
          <form onSubmit={handleEmailAuth} className="flex flex-col gap-3">
            <input 
              type="email" 
              placeholder="이메일" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-4 rounded-xl border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 outline-none transition-all text-sm bg-gray-50/50"
              required
            />
            <input 
              type="password" 
              placeholder="비밀번호" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-4 rounded-xl border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 outline-none transition-all text-sm bg-gray-50/50"
              required
              minLength={6}
            />
            
            {errorMsg && (
              <p className="text-xs text-red-500 text-center">{errorMsg}</p>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-4 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-indigo-600/20 mt-2 text-base"
            >
              {isLoading ? "처리 중..." : (isSignUp ? "회원가입" : "이메일로 로그인")}
            </button>
          </form>

          <div className="text-center mt-2">
             <button
              type="button"
              onClick={() => {
                setIsSignUp(!isSignUp);
                setErrorMsg('');
              }}
              className="text-sm font-semibold text-indigo-600 hover:text-indigo-700 transition-colors bg-transparent border-none p-0 w-auto inline-flex items-center"
            >
              {isSignUp ? "이미 계정이 있으신가요? 로그인" : "계정이 없으신가요? 회원가입"}
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="ml-1"><path d="M5 12h14"></path><path d="m12 5 7 7-7 7"></path></svg>
            </button>
          </div>

        </div>

        <div className="mt-6 text-center">
          <p className="text-[10px] text-gray-400">
            로그인 시 이용약관 및 개인정보처리방침에 동의하게 됩니다.
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginModal;
