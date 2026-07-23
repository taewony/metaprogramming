"use client";

import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { useState } from "react";
import { useTestStore } from "@/store/useTestStore";
import { useRouter } from "next/navigation";

export default function Home() {
    const [name, setName] = useState("");
    const { setNickname } = useTestStore();
    const router = useRouter();

    const handleStart = () => {
        if (name.trim()) {
            setNickname(name.trim());
            router.push("/test");
        } else {
            alert("닉네임을 입력해주세요!");
        }
    };

    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: {
                staggerChildren: 0.2,
                delayChildren: 0.3
            }
        }
    };

    const itemVariants = {
        hidden: { opacity: 0, y: 20 },
        visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } }
    };

    return (
        <main className="flex min-h-screen flex-col items-center justify-center p-6 relative overflow-hidden bg-background">
            {/* 상단 다크모드 토글 */}
            <div className="absolute top-4 right-4 z-50">
                <ThemeToggle />
            </div>

            {/* 배경 장식 요소 (코드 에스테틱) */}
            <div className="absolute inset-0 pointer-events-none opacity-[0.03] dark:opacity-[0.05] select-none font-mono text-xs leading-none overflow-hidden">
                {Array.from({ length: 20 }).map((_, i) => (
                    <div key={i} className="whitespace-nowrap">
                        {"import { build } from 'mbti'; console.log('searching for true developer...'); ".repeat(10)}
                    </div>
                ))}
            </div>

            <motion.div
                variants={containerVariants}
                initial="hidden"
                animate="visible"
                className="w-full max-w-2xl text-center z-10"
            >
                {/* 참여자 수 표시 (404 밈 활용) */}
                <motion.div variants={itemVariants} className="mb-6">
                    <span className="inline-block px-4 py-1.5 rounded-full bg-secondary text-primary text-xs font-mono font-bold border border-primary/20 shadow-sm shadow-primary/10">
                        STATUS: 404,111 CODERS DISCOVERED
                    </span>
                </motion.div>

                {/* 메인 카피 */}
                <motion.h1 
                    variants={itemVariants}
                    className="text-4xl md:text-6xl font-black tracking-tighter mb-4 break-keep leading-[1.1] text-foreground"
                >
                    너, <span className="text-primary italic font-mono font-black italic">코딩</span> 그렇게 하는거 아니야.
                </motion.h1>

                {/* 서브 카피 */}
                <motion.p 
                    variants={itemVariants}
                    className="text-lg md:text-xl text-muted-foreground mb-12 font-medium"
                >
                    100만 라인 스파게티 코드 속에서<br className="md:hidden" /> 나의 &apos;개발 본캐&apos; 찾기
                </motion.p>

                {/* 닉네임 입력 영역 (git config 스타일) */}
                <motion.div 
                    variants={itemVariants}
                    className="max-w-sm mx-auto mb-10 w-full"
                >
                    <div className="relative group">
                        <div className="absolute -inset-1 bg-gradient-to-r from-primary to-accent rounded-xl blur opacity-25 group-focus-within:opacity-50 transition duration-500"></div>
                        <div className="relative bg-card border-2 border-border rounded-xl p-2 transition-all group-focus-within:border-primary/50">
                            <div className="flex items-center px-4 py-1 text-xs font-mono text-muted-foreground border-b border-border mb-2">
                                <span className="flex-1 text-left">terminal — build</span>
                                <div className="flex gap-1.5">
                                    <div className="w-2.5 h-2.5 rounded-full bg-destructive/50"></div>
                                    <div className="w-2.5 h-2.5 rounded-full bg-amber-500/50"></div>
                                    <div className="w-2.5 h-2.5 rounded-full bg-green-500/50"></div>
                                </div>
                            </div>
                            <div className="flex items-center gap-2 px-4 py-2 font-mono text-lg">
                                <span className="text-primary font-bold shrink-0">$</span>
                                <span className="text-accent shrink-0">git config</span>
                                <input
                                    type="text"
                                    placeholder="user.name"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    className="w-full bg-transparent outline-none placeholder:text-muted-foreground/30 text-foreground"
                                    onKeyDown={(e) => e.key === 'Enter' && handleStart()}
                                    autoFocus
                                />
                            </div>
                        </div>
                    </div>
                </motion.div>

                {/* 시작 버튼 */}
                <motion.div variants={itemVariants}>
                    <Button 
                        size="lg" 
                        onClick={handleStart} 
                        className="group relative h-16 px-12 rounded-xl text-xl font-bold bg-primary hover:bg-primary/90 transition-all active:scale-95 shadow-xl shadow-primary/20 hover:shadow-primary/40 border-none"
                    >
                        <span className="relative z-10">빌드 시작하기 (START)</span>
                    </Button>
                </motion.div>
            </motion.div>

            {/* 푸터 */}
            <footer className="absolute bottom-8 left-0 right-0 text-center text-xs font-mono text-muted-foreground/40 tracking-tight">
                COMPILING SUCCESS... READY TO DEPLOY @ 2026 DEV_MBTI_LAB
            </footer>
        </main>
    );
}
