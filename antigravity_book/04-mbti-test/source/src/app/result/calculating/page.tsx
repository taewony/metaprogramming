"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { useTestStore } from "@/store/useTestStore";
import { Card } from "@/components/ui/card";

export default function CalculatingPage() {
    const router = useRouter();
    const { scores } = useTestStore();
    const [currentPhraseIndex, setCurrentPhraseIndex] = useState(0);
    const [displayText, setDisplayText] = useState("");
    const [isTyping, setIsTyping] = useState(true);

    const phrases = [
        "Stack Overflow에서 복붙할 코드를 찾는 중...",
        "node_modules 폴더의 블랙홀을 탐사하는 중...",
        "원인 모를 에러와 협상하는 중...",
        "커피를 코드로 변환하는 중...",
        "가비지 컬렉터와 숨바꼭질 하는 중...",
        "레거시 코드의 늪에서 탈출구를 찾는 중...",
    ];

    useEffect(() => {
        // Typing effect logic
        let typingTimer: NodeJS.Timeout;
        const currentPhrase = phrases[currentPhraseIndex];
        
        if (isTyping) {
            if (displayText.length < currentPhrase.length) {
                typingTimer = setTimeout(() => {
                    setDisplayText(currentPhrase.slice(0, displayText.length + 1));
                }, 50);
            } else {
                typingTimer = setTimeout(() => {
                    setIsTyping(false);
                }, 1500);
            }
        } else {
            if (displayText.length > 0) {
                typingTimer = setTimeout(() => {
                    setDisplayText(displayText.slice(0, displayText.length - 1));
                }, 30);
            } else {
                setCurrentPhraseIndex((prev) => (prev + 1) % phrases.length);
                setIsTyping(true);
            }
        }

        return () => clearTimeout(typingTimer);
    }, [displayText, isTyping, currentPhraseIndex]);

    useEffect(() => {
        // Final calculation and redirect
        const redirectTimer = setTimeout(() => {
            let resultId = "fullstack_unicorn";
            const s = scores;

            // Mapping logic based on archetypes from mbti_content.md
            // 1. LOW high -> low_level_ghost
            // 2. DEVOPS/AUTO high -> script_villain
            // 3. CHAOS high -> chaos_magician
            // 4. FE > BE -> fe_god
            // 5. BE > FE -> be_ghost
            
            if ((s.DEVOPS || 0) >= 2 || (s.AUTO || 0) >= 2) resultId = "script_villain";
            else if ((s.LOW || 0) >= 3) resultId = "low_level_ghost";
            else if ((s.CHAOS || 0) >= 2) resultId = "chaos_magician";
            else if ((s.FE || 0) >= (s.BE || 0)) resultId = "fe_god";
            else resultId = "be_ghost";

            router.push(`/result/${resultId}`);
        }, 4000);

        return () => clearTimeout(redirectTimer);
    }, [router, scores]);

    return (
        <main className="flex min-h-screen flex-col items-center justify-center p-6 bg-background relative overflow-hidden">
            {/* 배경 장식 (모듈 가습 효과) */}
            <div className="absolute inset-0 pointer-events-none overflow-hidden opacity-10">
                <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-[100px] animate-pulse"></div>
                <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent/20 rounded-full blur-[100px] animate-pulse delay-700"></div>
            </div>

            <div className="w-full max-w-lg z-10 space-y-8 flex flex-col items-center">
                {/* 로딩 애니메이션 (컴파일 아이콘) */}
                <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                    className="w-16 h-16 border-4 border-primary/20 border-t-primary rounded-full relative shadow-[0_0_20px_var(--primary)]"
                >
                    <div className="absolute inset-0 border-4 border-transparent border-b-accent rounded-full opacity-50"></div>
                </motion.div>

                <div className="space-y-4 w-full text-center">
                    <motion.h2
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="text-2xl font-black tracking-tight text-foreground uppercase italic"
                    >
                        &gt; Initializing Build...
                    </motion.h2>

                    {/* 타이프라이터 텍스트 카드 */}
                    <Card className="p-8 bg-slate-900/50 backdrop-blur-xl border-slate-800 shadow-2xl rounded-2xl min-h-[140px] flex items-center justify-center border-l-4 border-l-primary">
                        <div className="font-mono text-lg md:text-xl text-primary/90 flex items-center justify-center break-keep">
                            <span>{displayText}</span>
                            <motion.span
                                animate={{ opacity: [0, 1, 0] }}
                                transition={{ repeat: Infinity, duration: 0.8 }}
                                className="inline-block w-2.5 h-6 ml-1 bg-primary"
                            />
                        </div>
                    </Card>

                    <p className="text-xs font-mono text-muted-foreground/60 uppercase tracking-[0.2em]">
                        personality_matrix.cpp is compiling
                    </p>
                </div>

                {/* 하단 진행 바 (디코딩 효과) */}
                <div className="w-64 space-y-1">
                    <div className="flex justify-between text-[10px] font-mono text-muted-foreground uppercase">
                        <span>Analysis</span>
                        <span>In Progress</span>
                    </div>
                    <div className="h-1 w-full bg-secondary/30 rounded-full overflow-hidden">
                        <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: "100%" }}
                            transition={{ duration: 4, ease: "easeInOut" }}
                            className="h-full bg-gradient-to-r from-primary to-accent"
                        />
                    </div>
                </div>
            </div>
            
            <footer className="absolute bottom-8 text-[10px] font-mono text-muted-foreground/30 uppercase tracking-widest">
                System: Processing scores into MBTI hex...
            </footer>
        </main>
    );
}
