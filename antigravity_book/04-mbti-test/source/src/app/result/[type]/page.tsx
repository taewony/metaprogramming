"use client";

import { use, useRef, useEffect } from "react";
import { notFound } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import { results } from "@/data/results";
import { useTestStore } from "@/store/useTestStore";
import { motion } from "framer-motion";
import { RotateCcw, Home, Download, Share2, Bug, MessageCircle } from "lucide-react";
import { toPng } from "html-to-image";
import { toast } from "sonner";
import { ThemeToggle } from "@/components/layout/ThemeToggle";

// Types for Kakao SDK
interface KakaoShare {
    sendDefault: (options: any) => void;
}

interface Kakao {
    init: (key: string) => void;
    isInitialized: () => boolean;
    Share: KakaoShare;
}

declare global {
    interface Window {
        Kakao: Kakao;
    }
}

// Helper to get result by ID
function getResult(id: string) {
    return results.find((r) => r.id === id);
}

export default function ResultPage({ params }: { params: Promise<{ type: string }> }) {
    const { type } = use(params);
    const result = getResult(type);
    const { resetTest, nickname } = useTestStore();
    const resultCardRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const kakaoKey = process.env.NEXT_PUBLIC_KAKAO_JS_KEY;
        
        if (typeof window !== "undefined" && window.Kakao) {
            if (!window.Kakao.isInitialized()) {
                if (kakaoKey) {
                    try {
                        window.Kakao.init(kakaoKey);
                    } catch (e) {
                        console.error("Kakao Init Error:", e);
                    }
                }
            }
        }
    }, []);

    if (!result) {
        return notFound();
    }

    const bestMatch = getResult(result.match.best);
    const worstMatch = getResult(result.match.worst);

    const handleDownloadImage = async () => {
        if (!resultCardRef.current) return;

        try {
            const dataUrl = await toPng(resultCardRef.current, {
                backgroundColor: "#020617", // Slate-950
                cacheBust: true,
                style: {
                    borderRadius: '0px' // Capture without rounded corners for cleaner image
                }
            });
            const link = document.createElement("a");
            link.href = dataUrl;
            link.download = `dev_mbti_${nickname || 'coder'}_${result.id}.png`;
            link.click();
            toast.success("명예의 전당 이미지가 저장되었습니다!");
        } catch (error) {
            console.error(error);
            toast.error("이미지 저장에 실패했습니다.");
        }
    };

    const handleKakaoShare = () => {
        if (typeof window !== "undefined" && window.Kakao) {
            try {
                if (!window.Kakao.isInitialized()) {
                    const kakaoKey = process.env.NEXT_PUBLIC_KAKAO_JS_KEY;
                    if (kakaoKey) {
                        window.Kakao.init(kakaoKey);
                    } else {
                        toast.error("카카오 키가 설정되지 않았습니다.");
                        return;
                    }
                }

                window.Kakao.Share.sendDefault({
                    objectType: 'feed',
                    content: {
                        title: `나의 개발 정체성은 [${result.name}]!`,
                        description: `${result.traits.join(', ')}\n지금 당신의 개발 유형을 확인해보세요.`,
                        imageUrl: 'https://images.unsplash.com/photo-1614741118887-7a4ee193a5fa?q=80&w=1000&auto=format&fit=crop', // A nice coding-related image
                        link: {
                            mobileWebUrl: window.location.href,
                            webUrl: window.location.href,
                        },
                    },
                    buttons: [
                        {
                            title: '나도 테스트 하기',
                            link: {
                                mobileWebUrl: window.location.origin,
                                webUrl: window.location.origin,
                            },
                        },
                    ],
                });
            } catch (error) {
                console.error("Kakao Share Error:", error);
                toast.error("카카오톡 공유 중 오류가 발생했습니다.");
            }
        } else {
            toast.error("카카오 SDK가 아직 로드되지 않았습니다. 잠시 후 다시 시도해주세요.");
        }
    };

    const containerVariants = {
        hidden: { opacity: 0, y: 30 },
        visible: { 
            opacity: 1, 
            y: 0,
            transition: { duration: 0.6, staggerChildren: 0.15 } 
        }
    };

    const itemVariants = {
        hidden: { opacity: 0, y: 20 },
        visible: { opacity: 1, y: 0 }
    };

    return (
        <main className="min-h-screen py-10 px-4 md:px-8 flex flex-col items-center bg-background relative overflow-x-hidden">
            {/* 상단 다크모드 토글 */}
            <div className="absolute top-4 right-4 z-50">
                <ThemeToggle />
            </div>

            {/* 배경 장식 */}
            <div className="absolute inset-0 pointer-events-none opacity-[0.03] dark:opacity-[0.05] font-mono text-[10px] select-none whitespace-pre">
                {"01 ".repeat(1000)}
            </div>

            <motion.div
                variants={containerVariants}
                initial="hidden"
                animate="visible"
                className="max-w-2xl w-full space-y-10 z-10"
            >
                {/* Result Card for Capture */}
                <Card 
                    ref={resultCardRef} 
                    className="relative overflow-hidden border-2 border-border/50 bg-card p-6 md:p-10 shadow-[0_0_50px_rgba(0,0,0,0.1)] dark:shadow-[0_0_50px_rgba(0,0,0,0.5)] rounded-3xl"
                >
                    {/* IDE Header Style */}
                    <div className="absolute top-0 left-0 right-0 h-10 bg-muted/50 border-b border-border/20 flex items-center px-4 justify-between">
                        <div className="flex gap-1.5">
                            <div className="w-2.5 h-2.5 rounded-full bg-red-500/50" />
                            <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/50" />
                            <div className="w-2.5 h-2.5 rounded-full bg-green-500/50" />
                        </div>
                        <span className="text-[10px] font-mono text-muted-foreground italic capitalize">
                            {result.id}.log — {nickname || "guest"}@localhost
                        </span>
                    </div>

                    <div className="mt-8 space-y-8">
                        {/* Title Section */}
                        <div className="text-center space-y-3">
                            <motion.p variants={itemVariants} className="text-primary font-mono text-sm tracking-widest uppercase">
                                [ Analysis Complete ]
                            </motion.p>
                            <motion.h1 variants={itemVariants} className="text-3xl md:text-5xl font-black tracking-tighter text-foreground break-keep leading-tight">
                                당신은 <span className="text-primary underline decoration-primary/30 underline-offset-8">&quot;{result.name}&quot;</span> 입니다.
                            </motion.h1>
                        </div>

                        {/* Visual Center */}
                        <motion.div 
                            variants={itemVariants}
                            className="flex justify-center py-4"
                        >
                            <div className="relative group">
                                <div className="absolute -inset-4 bg-primary/20 rounded-full blur-3xl opacity-50 group-hover:opacity-100 transition-opacity duration-500" />
                                <div className="w-48 h-48 md:w-56 md:h-56 rounded-full bg-background border-4 border-primary/30 flex items-center justify-center text-7xl shadow-2xl relative z-10">
                                    <span className="drop-shadow-[0_0_15px_rgba(124,58,237,0.5)]">
                                        {result.id.includes('fe') ? '🎨' :
                                         result.id.includes('be') ? '⚙️' :
                                         result.id.includes('chaos') ? '🧙‍♂️' :
                                         result.id.includes('villain') ? '🤖' :
                                         result.id.includes('low') ? '💾' :
                                         result.id.includes('slave') ? '🦄' :
                                         result.id.includes('hero') ? '🌿' :
                                         result.id.includes('hipster') ? '🕶️' : '📜'}
                                    </span>
                                </div>
                            </div>
                        </motion.div>

                        {/* Traits Section */}
                        <motion.div variants={itemVariants} className="flex flex-wrap gap-2 justify-center">
                            {result.traits.map((trait, i) => (
                                <Badge key={i} variant="outline" className="text-sm px-4 py-1.5 rounded-full border-primary/20 bg-primary/5 text-primary hover:bg-primary/10 transition-colors">
                                    {trait}
                                </Badge>
                            ))}
                        </motion.div>

                        {/* Fact Violence Description */}
                        <motion.div variants={itemVariants} className="relative">
                            <div className="absolute -left-4 top-0 bottom-0 w-1 bg-primary/20 rounded-full" />
                            <div className="pl-6 space-y-4">
                                <h3 className="flex items-center gap-2 text-primary font-bold text-lg">
                                    <Bug size={18} /> TYPE_ANALYSIS_LOG:
                                </h3>
                                <p className="text-lg md:text-xl font-medium text-foreground/80 leading-relaxed break-keep">
                                    {result.description}
                                </p>
                            </div>
                        </motion.div>

                        {/* Compatibility */}
                        <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {bestMatch && (
                                <div className="p-5 rounded-2xl bg-primary/5 border border-primary/10 group hover:border-primary/30 transition-all">
                                    <h4 className="text-[10px] font-bold text-primary mb-2 flex items-center gap-1.5 uppercase tracking-tighter">
                                        <span className="w-1.5 h-1.5 rounded-full bg-primary" /> Merge 가능 (환상)
                                    </h4>
                                    <p className="font-bold text-foreground/90">{bestMatch.name}</p>
                                </div>
                            )}
                            {worstMatch && (
                                <div className="p-5 rounded-2xl bg-destructive/5 border border-destructive/10 group hover:border-destructive/30 transition-all">
                                    <h4 className="text-[10px] font-bold text-destructive mb-2 flex items-center gap-1.5 uppercase tracking-tighter">
                                        <span className="w-1.5 h-1.5 rounded-full bg-destructive" /> Conflict 발생 (환장)
                                    </h4>
                                    <p className="font-bold text-foreground/90">{worstMatch.name}</p>
                                </div>
                            )}
                        </motion.div>
                    </div>

                    {/* Footer for Image Capture */}
                    <div className="mt-12 flex justify-between items-end">
                        <div className="text-[10px] font-mono opacity-20 uppercase">
                            dev-mbti-test-v2.0 // viral edition
                        </div>
                        <div className="text-[10px] font-mono opacity-20">
                            WWW.ANTIGRAVITY.DEV
                        </div>
                    </div>
                </Card>

                {/* Actions */}
                <motion.div variants={itemVariants} className="flex flex-col items-center gap-8 w-full pt-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full">
                        <Button 
                            onClick={handleDownloadImage} 
                            variant="secondary" 
                            className="h-14 px-8 rounded-2xl text-lg font-bold gap-2 active:scale-95 transition-all shadow-xl"
                        >
                            <Download size={22} /> 명예의 전당 저장
                        </Button>
                        <Button 
                            onClick={handleKakaoShare}
                            className="h-14 px-8 rounded-2xl text-lg font-bold gap-2 active:scale-95 transition-all bg-[#FEE500] hover:bg-[#FEE500]/90 text-black border-none shadow-xl"
                        >
                            <MessageCircle size={22} fill="currentColor" /> 카카오톡 공유
                        </Button>
                        <Button 
                            variant="outline" 
                            className="h-14 px-8 rounded-2xl text-lg font-bold gap-2 active:scale-95 transition-all sm:col-span-2"
                            onClick={() => {
                                if (navigator.share) {
                                    navigator.share({
                                        title: '개발자 MBTI 테스트 결과',
                                        text: `나의 개발 정체성은 [${result.name}]! 지금 테스트 해보세요.`,
                                        url: window.location.href,
                                    });
                                } else {
                                    navigator.clipboard.writeText(window.location.href);
                                    toast.success("링크가 복사되었습니다!");
                                }
                            }}
                        >
                            <Share2 size={22} /> 링크 복사하기
                        </Button>
                    </div>

                    <div className="flex flex-col sm:flex-row gap-4 w-full justify-center">
                        <Link href="/test" onClick={resetTest} className="w-full sm:w-auto">
                            <Button variant="ghost" className="w-full h-12 rounded-xl text-muted-foreground hover:text-primary gap-2">
                                <RotateCcw size={18} /> 다시 빌드하기
                            </Button>
                        </Link>
                        <Link href="/" onClick={resetTest} className="w-full sm:w-auto">
                            <Button variant="ghost" className="w-full h-12 rounded-xl text-muted-foreground hover:text-accent gap-2">
                                <Home size={18} /> 터미널로 돌아가기
                            </Button>
                        </Link>
                    </div>
                </motion.div>
            </motion.div>

            {/* Bottom Credit */}
            <motion.footer 
                initial={{ opacity: 0 }}
                animate={{ opacity: 0.3 }}
                transition={{ delay: 1.5 }}
                className="mt-16 text-[10px] font-mono uppercase tracking-[0.5em]"
            >
                Made with passion by antgrav-dev-team
            </motion.footer>
        </main>
    );
}
