# 개발자 MBTI 테스트 웹 애플리케이션 디자인 문서 (mbti_design.md)

## 1. 프로젝트 개요
개발자들의 코딩 스타일과 성향을 분석하여 MBTI 유형처럼 결과를 보여주는 웹 애플리케이션입니다. 사용자 몰입도를 높이기 위해 모던한 UI와 풍부한 인터랙션을 제공하며, 다크모드를 기본으로 라이트모드를 지원합니다.

## 2. 기술 스택 (Tech Stack)
- **Framework**: Next.js 14+ (App Router)
- **Styling**: Tailwind CSS
- **UI Component Library**: shadcn/ui (Radix UI 기반)
- **Animation**: Framer Motion
- **Icons**: Lucide React

## 3. 디자인 시스템 (Design System)

### 3.1 컬러 팔레트 (Color Palette)
`shadcn/ui`의 기본 테마를 활용하되, 개발자 감성에 맞는 컬러 포인트를 추가합니다.

#### Light Mode
- **Background**: `#ffffff` (Clean White)
- **Foreground**: `#09090b` (Rich Black)
- **Primary**: `#3b82f6` (Bright Blue - 신뢰감, 기술적임)
- **Secondary**: `#f1f5f9` (Light Slate - 부드러운 배경 요소)
- **Accent**: `#8b5cf6` (Violet - 창의성, 포인트)

#### Dark Mode (Default)
- **Background**: `#09090b` (Deep Zinc - 눈이 편안한 짙은 회색)
- **Foreground**: `#fafafa` (Off White)
- **Primary**: `#60a5fa` (Soft Blue)
- **Secondary**: `#1e293b` (Slate 800)
- **Accent**: `#a78bfa` (Soft Violet)

### 3.2 타이포그래피 (Typography)
- **한글 폰트**: 'Pretendard' (가독성 최우선, 모던한 고딕)
- **코드 폰트**: 'Fira Code' 또는 'JetBrains Mono' (개발자 컨셉 강조)

## 4. UI 컴포넌트 전략 (shadcn/ui)

### 사용될 주요 컴포넌트
- **Card**: 질문 카드 및 결과 카드 컨테이너.
- **Button**: 메인 CTA(Call to Action), 선택지 버튼. `ghost` 및 `outline` 변형 적극 활용.
- **Progress**: 진행 상황 표시줄.
- **Badge**: 결과 태그, 키워드 표시.
- **Toggle/Switch**: 다크/라이트 모드 전환.
- **Toast**: 결과 공유 시 피드백.

## 5. 애니메이션 및 인터랙션 (Framer Motion)

### 5.1 페이지 전환
- 페이지 이동 시 부드러운 Fade In/Out 및 Slide 효과 적용.

### 5.2 마이크로 인터랙션
- **버튼 호버**: 약간의 Scale Up (1.05x) 및 그림자 강화.
- **선택지 클릭**: 클릭 시 테두리 색상 변경 및 Ripple 효과.

### 5.3 진행 바
- 단계가 넘어갈 때 끊기지 않고 부드럽게 차오르는 애니메이션 (`layout` prop 활용).

## 6. 페이지별 상세 디자인 (Page Structure)

### 6.1 랜딩 페이지 (Landing Page)
- **Hero Section**:
    - 큰 타이틀: "나의 개발자 MBTI는?" (타이핑 애니메이션 효과 적용)
    - 서브텍스트: "코딩 스타일로 알아보는 나의 성향 테스트"
    - **메인 CTA 버튼**: "테스트 시작하기" (버튼 주위에 은은한 Glow 효과)
    - 배경: 추상적인 코드 조각이나 노드들이 떠다니는 애니메이션 배경.

### 6.2 테스트 페이지 (Question Page)
- **상단**:
    - 뒤로가기 아이콘 (ChevronLeft).
    - 현재 진행률 표시바 (Progress Bar).
- **중단 (질문 카드)**:
    - 카드 형태의 질문 영역.
    - 질문 텍스트는 크고 명확하게.
    - **답변 영역**: 2개의 커다란 버튼으로 구성. 마우스 호버 시 명확한 피드백.
    - 애니메이션: 답변 선택 시 현재 카드가 왼쪽으로 사라지고(Slide Left), 다음 카드가 오른쪽에서 등장(Slide In).

### 6.3 로딩/분석 페이지 (Loading Page)
- **컨셉**: 코드가 컴파일되거나 배포되는 듯한 터미널 UI.
- 텍스트: "Github 커밋 기록 분석 중...", "Stack Overflow 검색 중..." 등의 위트 있는 문구 롤링.
- 로딩 스피너 대신 타이핑되는 터미널 로그 텍스트 애니메이션.

### 6.4 결과 페이지 (Result Page)
- **상단**: "당신의 개발자 유형은?"
- **메인 결과**:
    - 유형 이름 (예: "완벽주의자 아키텍트") - 큰 폰트 강조.
    - 대표 일러스트 또는 3D 아이콘.
    - 성향 요약 설명 (Card 컴포넌트 활용).
- **잘 맞는/안 맞는 동료**:
    - 다른 유형의 아이콘과 이름 표시 (Grid 레이아웃).
- **하단 액션**:
    - "결과 공유하기" (클립보드 복사).
    - "다시 테스트하기".
- **추가 요소**: 다크모드 토글은 항상 접근 가능한 위치(우측 상단)에 고정.

## 7. 다크모드/라이트모드 전략
- `next-themes` 라이브러리를 사용하여 상태 관리.
- CSS Variables를 활용하여 색상 토큰값을 변경하므로, 컴포넌트 레벨에서의 코드 수정 최소화.
- 토글 버튼은 재미있는 아이콘 전환 애니메이션(해/달) 포함.
