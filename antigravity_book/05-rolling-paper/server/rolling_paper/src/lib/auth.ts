import { supabase } from "./supabaseClient";

/**
 * Kakao 소셜 로그인을 실행합니다.
 */
export const signInWithKakao = async () => {
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: "kakao",
    options: {
      redirectTo: window.location.origin,
    },
  });

  if (error) {
    console.error("Kakao login error:", error.message);
    throw error;
  }

  return data;
};

/**
 * 이메일/비밀번호 로그인을 실행합니다.
 */
export const signInWithEmail = async (email, password) => {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });

  if (error) {
    throw error;
  }

  return data;
};

/**
 * 이메일/비밀번호 회원가입을 실행합니다.
 */
export const signUpWithEmail = async (email, password) => {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      emailRedirectTo: window.location.origin,
    },
  });

  if (error) {
    throw error;
  }

  return data;
};

/**
 * 로그아웃을 실행합니다.
 */
export const signOut = async () => {
  const { error } = await supabase.auth.signOut();

  if (error) {
    console.error("Logout error:", error.message);
    throw error;
  }
};
