"use client";

import Script from "next/script";

export default function KakaoScript() {
    return (
        <Script
            src="https://t1.kakaocdn.net/kakao_js_sdk/2.7.7/kakao.min.js"
            integrity="sha384-tJkjbtDbvoxO+diRuDtwRO9JXR7pjWnfjfRn5ePUpl7e7RJCxKCwwnfqUAdXh53p"
            crossOrigin="anonymous"
            strategy="afterInteractive"
            onLoad={() => {
                const kakaoKey = process.env.NEXT_PUBLIC_KAKAO_JS_KEY;
                if (window.Kakao && kakaoKey && !window.Kakao.isInitialized()) {
                    window.Kakao.init(kakaoKey);
                }
            }}
        />
    );
}
