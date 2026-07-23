# 개발자 MBTI 테스트 구현 계획서

## 목표 설명
제공된 디자인 및 콘텐츠 사양을 바탕으로 "개발자 MBTI 테스트" 웹 애플리케이션을 구축합니다. 이 앱은 개발자의 코딩 스타일과 선택에 따라 다양한 성격 유형으로 분류합니다. 주요 기능으로는 동적 설문지, 결과 계산 로직, 소셜 공유 기능 등이 포함됩니다.

## 사용자 검토 필요 사항
- **프로젝트 구조**: 새로운 Next.js 프로젝트를 초기화합니다.
- **기술 스택**: Next.js (App Router), Tailwind CSS, Framer Motion, Zustand (상태 관리용).

## 제안된 변경 사항

### 프로젝트 초기화
#### [NEW] [프로젝트 루트]
- Next.js 앱 초기화: `npx create-next-app@latest . --typescript --tailwind --eslint`
- 종속성 설치: `npm install framer-motion zustand lucide-react clsx tailwind-merge`
- shadcn/ui 설치: `npx shadcn@latest init`

### 핵심 로직 및 데이터
#### [NEW] [types/index.ts]
- `Question`, `Option`, `Result`, `MBTIResult`에 대한 인터페이스 정의.

#### [NEW] [data/questions.ts]
- `mbti_content.md`의 내용을 구조화된 TypeScript 객체로 변환.

#### [NEW] [data/results.ts]
- `mbti_content.md`의 결과 내용을 구조화된 TypeScript 객체로 변환.

#### [NEW] [store/useTestStore.ts]
- 다음을 추적하기 위한 Zustand 스토어 구현:
    - 현재 질문 인덱스
    - 선택된 답변
    - 점수 계산 로직 (E/I, N/S, T/F, J/P)

### UI 컴포넌트
#### [NEW] [components/layout/ThemeToggle.tsx]
- `next-themes`를 사용한 라이트/다크 모드 토글.

#### [NEW] [app/page.tsx]
- "테스트 시작" 버튼이 있는 랜딩 페이지.

#### [NEW] [app/test/page.tsx]
- 질문 표시 컴포넌트.
- 진행 바 (Progress bar).
- 탐색 로직 (다음/이전).

#### [NEW] [app/result/[type]/page.tsx]
- 계산된 MBTI 유형에 따른 동적 결과 페이지.
- 설명, 잘 맞는 유형, 추천 직업 표시.

#### [NEW] [components/share/ShareButtons.tsx]
- 카카오톡 공유 로직 (카카오 일반 링크 사용 또는 API 키 요구 사항 확인 - *자체 메모: 키가 없는 경우 플레이스홀더 필요할 수 있음*).
- 링크 복사 기능.
- 트위터/페이스북 공유 링크.

## 검증 계획

### 자동 테스트
- **단위 테스트**:
    - 사용자가 질문에 답하는 것을 시뮬레이션하고 계산된 MBTI 결과가 예상 결과와 일치하는지 확인하는 `scripts/test-logic.ts` 스크립트 작성.
    - 실행: `npx tsx scripts/test-logic.ts`

### 수동 검증
- **사용자 흐름**:
    - 테스트 시작 -> 모든 질문 답변 -> 진행 바 업데이트 확인.
    - 테스트 완료 -> 올바른 결과 페이지로 리다이렉트되는지 확인.
- **공유**:
    - "링크 복사" 클릭 -> URL이 복사되는지 확인.
    - "트위터 공유" 클릭 -> 올바른 텍스트와 함께 새 창이 뜨는지 확인.
