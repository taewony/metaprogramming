"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { useTestStore } from "@/store/useTestStore";
import { questions } from "@/data/questions";
import { ThemeToggle } from "@/components/layout/ThemeToggle";

export default function TestPage() {
    const router = useRouter();
    const { currentQuestionIndex, nextQuestion, setAnswer, scores, resetTest, nickname } = useTestStore();
    const [progress, setProgress] = useState(0);

    const currentQuestion = questions[currentQuestionIndex];

    // Calculate progress
    useEffect(() => {
        const rawProgress = ((currentQuestionIndex) / questions.length) * 100;
        setProgress(rawProgress);
    }, [currentQuestionIndex]);

    const calculateAndRedirect = () => {
        router.push("/result/calculating");
    }

    const [selectedOption, setSelectedOption] = useState<number | null>(null);

    const handleOptionSelect = (optionIndex: number, score: any) => {
        setSelectedOption(optionIndex);
        
        // 버튼 클릭 후 잠시 대기하여 애니메이션을 보여준 뒤 다음 질문으로 이동
        setTimeout(() => {
            setAnswer(currentQuestion.id, optionIndex, score);
            setSelectedOption(null);

            if (currentQuestionIndex < questions.length - 1) {
                nextQuestion();
            } else {
                calculateAndRedirect();
            }
        }, 400);
    };

    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: {
                staggerChildren: 0.1
            }
        }
    };

    const itemVariants = {
        hidden: { opacity: 0, y: 20 },
        visible: { opacity: 1, y: 0 }
    };

    if (!currentQuestion) return <div>Loading...</div>;

    return (
        <main className="flex min-h-screen flex-col items-center justify-center p-4 bg-background overflow-hidden relative">
            {/* 상단 다크모드 토글 */}
            <div className="absolute top-4 right-4 z-50">
                <ThemeToggle />
            </div>

            {/* 배경 장식 요소 */}
            <div className="absolute inset-0 pointer-events-none opacity-[0.02] dark:opacity-[0.04] font-mono text-[10px] overflow-hidden select-none whitespace-pre">
                {"git push origin main --force --quiet \n".repeat(100)}
            </div>

            <div className="w-full max-w-md space-y-6 z-10">
                {/* 헤더 영역: 닉네임 표시 (Git Log style) */}
                <div className="flex flex-col gap-1 mb-2">
                    <div className="flex items-center gap-2 text-[10px] font-mono text-primary/70">
                        <span className="bg-primary/10 px-1.5 py-0.5 rounded text-primary border border-primary/20">USER</span>
                        <span className="opacity-80">$ git log --author=&quot;{nickname || "unknown"}&quot;</span>
                    </div>
                </div>

                {/* 프로그레스 바 영역: 컴파일 스타일 */}
                <div className="space-y-2">
                    <div className="flex justify-between items-end">
                        <span className="text-[11px] font-mono font-bold text-accent animate-pulse uppercase">
                            &gt; COMPILING... {Math.round(progress)}%
                        </span>
                        <span className="text-[10px] font-mono text-muted-foreground">
                            STDOUT: [ {currentQuestionIndex + 1} / {questions.length} ]
                        </span>
                    </div>
                    <Progress value={progress} className="h-2 bg-secondary/30" />
                </div>

                <AnimatePresence mode="wait">
                    <motion.div
                        key={currentQuestion.id}
                        initial={{ opacity: 0, y: 30 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -30 }}
                        transition={{ duration: 0.4, ease: "easeOut" }}
                    >
                        <Card className="p-8 shadow-2xl border-2 border-border/50 bg-card/40 backdrop-blur-xl relative overflow-hidden rounded-2xl">
                            {/* 장식용 아이콘 (Code Aesthetic) */}
                            <div className="absolute -top-6 -right-6 p-4 opacity-5 pointer-events-none rotate-12">
                                <code className="text-4xl font-mono italic">{"{...}"}</code>
                            </div>

                            <h2 className="text-xl md:text-2xl font-bold mb-10 leading-tight break-keep text-foreground/90 tracking-tight">
                                {currentQuestion.question}
                            </h2>

                            <motion.div 
                                className="space-y-3"
                                variants={containerVariants}
                                initial="hidden"
                                animate="visible"
                            >
                                {currentQuestion.options.map((option, index) => (
                                    <motion.div
                                        key={index}
                                        variants={itemVariants}
                                    >
                                        <motion.button
                                            whileHover={{ scale: 1.02, backgroundColor: "rgba(124, 58, 237, 0.05)", borderColor: "rgba(124, 58, 237, 0.5)" }}
                                            whileTap={{ scale: 0.98 }}
                                            animate={{
                                                opacity: selectedOption === null || selectedOption === index ? 1 : 0.4,
                                                scale: selectedOption === index ? 1.02 : 1,
                                                borderColor: selectedOption === index ? "var(--primary)" : "rgba(255,255,255,0.05)",
                                                borderWidth: "2px"
                                            }}
                                            onClick={() => handleOptionSelect(index, option.score)}
                                            className="w-full p-5 text-left rounded-xl bg-secondary/20 backdrop-blur-sm border-2 border-transparent transition-all shadow-sm flex items-center justify-between group relative overflow-hidden"
                                        >
                                            <span className="text-base md:text-lg font-medium group-hover:text-primary transition-colors pr-4 leading-normal">{option.text}</span>
                                            {selectedOption === index && (
                                                <motion.div
                                                    initial={{ scale: 0 }}
                                                    animate={{ scale: 1 }}
                                                    className="w-2.5 h-2.5 rounded-full bg-primary shrink-0 shadow-[0_0_10px_var(--primary)]"
                                                />
                                            )}
                                        </motion.button>
                                    </motion.div>
                                ))}
                            </motion.div>
                        </Card>
                    </motion.div>
                </AnimatePresence>

                {/* 하단 취소 버튼 */}
                <div className="flex justify-center pt-4">
                    <Button 
                        variant="ghost" 
                        size="sm" 
                        onClick={() => { if(confirm("빌드를 종료하시겠습니까?")) { resetTest(); router.push("/"); } }} 
                        className="text-[10px] font-mono uppercase tracking-widest opacity-40 hover:opacity-100 transition-opacity hover:bg-destructive/10 hover:text-destructive"
                    >
                        [ ESC ] Terminate Build
                    </Button>
                </div>
            </div>
        </main>
    );
}
