import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";
import KakaoScript from "@/components/layout/KakaoScript";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
    title: "Developer MBTI Test",
    description: "Find out your developer personality type!",
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="ko" suppressHydrationWarning>
            <body className={inter.className} suppressHydrationWarning>
                <ThemeProvider
                    attribute="class"
                    defaultTheme="system"
                    enableSystem
                    disableTransitionOnChange
                >
                    {children}
                </ThemeProvider>
                <KakaoScript />
            </body>
        </html>
    );
}
