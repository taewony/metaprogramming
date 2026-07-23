"use client";

import { Button } from "@/components/ui/button";
import { Link2, Twitter, Facebook } from "lucide-react";
import { toast } from "sonner"; // Using sonner as requested

interface ShareButtonsProps {
    resultName: string;
    resultDescription: string;
}

export function ShareButtons({ resultName, resultDescription }: ShareButtonsProps) {
    const shareUrl = typeof window !== "undefined" ? window.location.href : "";
    const shareText = `나의 개발자 성향은? [${resultName}] - ${resultDescription}`;

    const handleCopyLink = () => {
        navigator.clipboard.writeText(shareUrl).then(() => {
            toast.success("링크가 복사되었습니다!");
        });
    };

    const handleTwitterShare = () => {
        const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(
            shareText
        )}&url=${encodeURIComponent(shareUrl)}`;
        window.open(twitterUrl, "_blank");
    };

    const handleFacebookShare = () => {
        const facebookUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(
            shareUrl
        )}`;
        window.open(facebookUrl, "_blank");
    };

    const handleKakaoShare = () => {
        // Placeholder for Kakao Logic
        toast.info("카카오톡 공유 기능은 API 키 설정이 필요합니다.");
    }

    return (
        <div className="flex flex-wrap gap-2 justify-center">
            <Button variant="outline" size="icon" onClick={handleCopyLink} title="링크 복사">
                <Link2 size={20} />
            </Button>
            <Button variant="outline" size="icon" onClick={handleTwitterShare} title="트위터 공유" className="text-blue-400 hover:text-blue-500">
                <Twitter size={20} />
            </Button>
            <Button variant="outline" size="icon" onClick={handleFacebookShare} title="페이스북 공유" className="text-blue-600 hover:text-blue-700">
                <Facebook size={20} />
            </Button>
            <Button variant="outline" size="icon" onClick={handleKakaoShare} title="카카오톡 공유" className="text-yellow-900 bg-yellow-400 hover:bg-yellow-500 hover:text-yellow-950 border-none">
                <span className="font-bold text-xs">TALK</span>
            </Button>
        </div>
    );
}
