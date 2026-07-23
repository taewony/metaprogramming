# Shadcn/ui 사용 가이드 (MBTI Test Project)

이 문서는 [Shadcn/ui 공식 문서](https://ui.shadcn.com/docs)를 참조하여, 우리 MBTI 심리 테스트 프로젝트(Next.js App Router)에 필요한 핵심 컴포넌트 사용법을 정리한 가이드입니다.

## 1. 초기 설치 (Installation)

Next.js 프로젝트 루트 경로에서 아래 명령어를 실행하여 Shadcn/ui를 초기화합니다.

```bash
npx shadcn@latest init
```

명령어 실행 후 나타나는 설정 질문에는 프로젝트 환경에 맞춰 답변합니다. (일반적인 추천 설정: TypeScript 사용, Tailwind CSS 사용)

---

## 2. 필수 컴포넌트 설치 및 사용법

### 2.1 Button (버튼)
사용자의 답변 제출, 다음/이전 단계 이동 등에 사용합니다.

**설치 명령어:**
```bash
npx shadcn@latest add button
```

**사용 예제:**
```tsx
import { Button } from "@/components/ui/button"

export function ButtonDemo() {
  return (
    <div className="flex gap-4">
      {/* 기본 버튼 */}
      <Button>다음 단계</Button>
      
      {/* 2차 액션 (Secondary) */}
      <Button variant="secondary">이전</Button>
      
      {/* 파괴적 액션 (Destructive) - 예: 다시 시작 */}
      <Button variant="destructive">다시 시작</Button>
      
      {/* 아이콘 스타일 (Outline) */}
      <Button variant="outline">설정</Button>
    </div>
  )
}
```

---

### 2.2 Card (카드)
질문 내용, 테스트 결과 등을 담는 컨테이너로 사용합니다.

**설치 명령어:**
```bash
npx shadcn@latest add card
```

**사용 예제:**
```tsx
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export function QuestionCard() {
  return (
    <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>질문 1</CardTitle>
        <CardDescription>새로운 프로젝트를 시작할 때 당신의 스타일은?</CardDescription>
      </CardHeader>
      <CardContent>
        <p>답변 선택지들이 여기에 위치합니다.</p>
      </CardContent>
      <CardFooter className="flex justify-between">
        <Button variant="outline">이전</Button>
        <Button>다음</Button>
      </CardFooter>
    </Card>
  )
}
```

---

### 2.3 Progress (진행률 표시)
테스트 진행 상황이나 결과 점수를 시각적으로 보여줄 때 사용합니다.

**설치 명령어:**
```bash
npx shadcn@latest add progress
```

**사용 예제:**
```tsx
"use client"

import * as React from "react"
import { Progress } from "@/components/ui/progress"

export function ProgressBar() {
  const [progress, setProgress] = React.useState(13)

  React.useEffect(() => {
    const timer = setTimeout(() => setProgress(66), 500)
    return () => clearTimeout(timer)
  }, [])

  return (
    <div className="w-full space-y-2">
      <div className="text-sm text-muted-foreground">진행률: {progress}%</div>
      <Progress value={progress} className="w-[60%]" />
    </div>
  )
}
```

---

### 2.4 Radio Group (라디오 그룹)
객관식 질문의 답변을 선택할 때 사용합니다.

**설치 명령어:**
```bash
npx shadcn@latest add radio-group
```

**사용 예제:**
```tsx
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"

export function AnswerSelection() {
  return (
    <RadioGroup defaultValue="option-1">
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="option-1" id="option-1" />
        <Label htmlFor="option-1">계획을 철저히 세우고 시작한다 (J형)</Label>
      </div>
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="option-2" id="option-2" />
        <Label htmlFor="option-2">일단 코드를 작성하며 생각한다 (P형)</Label>
      </div>
    </RadioGroup>
  )
}
```
