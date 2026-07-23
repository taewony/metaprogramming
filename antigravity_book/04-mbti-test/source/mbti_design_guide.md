# 개발자 성향 MBTI - 디자인 가이드 (Design Guide)

본 문서는 `docs/mbti_content.md`의 기획 내용과 `shadcn_guide.md`의 기술 스택을 기반으로 작성된 디자인 가이드라인입니다.

## 1. 디자인 컨셉 (Design Concept)

- **테마명**: "Midnight Dev Studio" (어둠 속의 코딩)
- **핵심 키워드**:
  - **Dark Mode First**: 개발자에게 익숙한 다크 모드를 기본으로 채택합니다.
  - **Code Aesthetic**: 터미널, IDE(통합 개발 환경) 느낌의 UI 요소를 차용합니다.
  - **Glassmorphism**: 최신 트렌드를 반영하여 카드 및 컨테이너에 반투명 유리 효과를 적용합니다.

---

## 2. 컬러 시스템 (Color System)

Tailwind CSS의 기본 팔레트를 활용하며, 커스텀 설정을 통해 브랜드 아이덴티티를 강화합니다.

### 2.1 메인 컬러 (Primary Colors)

- **Primary (Brand Color)**: `Violet-600` (#7c3aed)
  - 용도: 메인 CTA(Call to Action) 버튼, 프로그레스 바 핵심 컬러, 강조 텍스트.
  - 의미: 창의성과 지성을 상징하는 보라색 계열.
- **Secondary**: `Slate-800` (#1e293b)
  - 용도: 보조 버튼, 덜 중요한 카드 배경.
- **Accent**: `Cyan-400` (#22d3ee)
  - 용도: 포인트 아이콘, 중요 키워드 하이라이트, 링크.

### 2.2 배경 및 텍스트 (Background & Typography)

- **Background**: `Slate-950` (#020617) - 완전한 검정보다는 깊은 남색 계열의 다크 배경.
- **Surface (Card)**: `Slate-900` (#0f172a) with opacity (e.g., `bg-slate-900/50`).
- **Text Main**: `Slate-50` (#f8fafc) - 가독성 높은 흰색.
- **Text Muted**: `Slate-400` (#94a3b8) - 설명 텍스트, 비활성 요소.

---

## 3. 타이포그래피 (Typography)

- **기본 폰트 (Sans)**: `Inter` (Next.js/Shadcn 기본 폰트)
  - 용도: 일반적인 텍스트, 설명, 버튼 텍스트.
- **코드 폰트 (Mono)**: `JetBrains Mono` 또는 `Fira Code`
  - 용도: 질문 속의 코드 예시, 결과 화면의 "개발자 유형" 타이틀 등 개발자 감성 요소.

### 폰트 사이즈 가이드

- **Title (H1)**: `text-3xl lg:text-4xl` / `font-bold` / `tracking-tight`
- **Subtitle (H2)**: `text-xl lg:text-2xl` / `font-semibold` / `text-slate-200`
- **Body**: `text-base` / `leading-relaxed`
- **Small**: `text-sm` / `text-slate-400`

---

## 4. UI 컴포넌트 세부 가이드 (Shadcn/ui Extension)

Shadcn/ui 컴포넌트를 커스터마이징하여 사용합니다.

### 4.1 버튼 (Button)

- **크기**: 모바일 터치를 고려하여 기본 높이를 넉넉하게 잡습니다.
  - Class: `h-12 px-6 text-lg`
- **모양**: `rounded-full` (부드러운 느낌) 또는 `rounded-md` (단 단한 느낌). 본 프로젝트는 **`rounded-xl`**을 권장합니다.
- **인터랙션**: Hover 시 명도 증가 (`hover:bg-primary/90`), Active 시 살짝 축소 (`active:scale-95` via Framer Motion).

### 4.2 질문 카드 (Question Card)

- **스타일**: Glassmorphism 적용
  - Class: `bg-slate-900/50 backdrop-blur-md border border-slate-800 shadow-xl`
- **배치**: 화면 중앙 정렬, 최대 너비 `max-w-md` (모바일 최적화).

### 4.3 프로그레스 바 (Progress Bar)

- **스타일**: 네온 글로우 효과 추가.
- **Class**: `h-3 rounded-full bg-slate-800` (트랙), `bg-gradient-to-r from-violet-500 to-cyan-400` (게이지).

### 4.4 답변 선택지 (Radio Group Item)

- 일반적인 라디오 버튼 대신 **전체 영역을 클릭 가능한 카드 형태**로 제작합니다.
- **선택 전**: `border-slate-700 bg-slate-800/50`
- **선택 후**: `border-violet-500 bg-violet-500/10 text-violet-300 ring-2 ring-violet-500/20`

---

## 5. 애니메이션 & 인터랙션 (Animations)

`Framer Motion`을 활용하여 정적인 느낌을 탈피합니다.

1.  **페이지 전환**:
    - Fade In + Slide Up (투명도 0 -> 1, Y축 +20px -> 0px)
2.  **답변 선택 시**:
    - 선택한 카드는 강조(Scale 1.02), 선택하지 않은 카드는 흐려짐(Opacity 0.5).
3.  **로딩 화면**:
    - 터미널에 타이핑되는 듯한 "Typewriter Effect".
4.  **결과 카드 등장**:
    - 3D Flip 효과 또는 Pop-up 효과.

---

## 6. 레이아웃 구조 (Layout Structure)

```
[Mobile First View]
+-----------------------------------+
|  [Header] (Logo + Dark Toggle)    |
+-----------------------------------+
|                                   |
|   [Progress Bar] (Question Page)  |
|                                   |
|   +---------------------------+   |
|   |                           |   |
|   |        Question           |   |
|   |          Text             |   |
|   |                           |   |
|   +---------------------------+   |
|                                   |
|   +---------------------------+   |
|   |      Answer Option A      |   |
|   +---------------------------+   |
|                                   |
|   +---------------------------+   |
|   |      Answer Option B      |   |
|   +---------------------------+   |
|                                   |
|   [Prev]                 [Next]   |
|                                   |
+-----------------------------------+
|  [Footer] (Copyright)             |
+-----------------------------------+
```

---

## 7. 접근성 (Accessibility)

모든 사용자가 동등하게 서비스를 이용할 수 있도록 WCAG 2.1 AA 표준을 준수합니다.

### 7.1 색상 대비 (Color Contrast)

- **텍스트 대비**: 텍스트와 배경 간의 명도비는 최소 **4.5:1**을 유지해야 합니다.
  - Glassmorphism 카드의 배경 불투명도를 조절하여 텍스트 가독성을 확보합니다.
  - 특히 `Slate-400` 등의 회색 텍스트 사용 시 배경색과의 대비를 체크합니다.

### 7.2 키보드 접근성 (Keyboard Navigation)

- **포커스 표시**: 모든 상호작용 가능한 요소(버튼, 링크, 입력 폼)는 키보드 포커스 시 명확한 시각적 지표를 제공해야 합니다.
  - 구현: Tailwind의 `focus-visible:ring` 유틸리티 사용.
  - 스타일: `ring-2 ring-violet-500 ring-offset-2 ring-offset-slate-950`

### 7.3 스크린 리더 지원 (Screen Reader Support)

- **ARIA 레이블**: 텍스트가 없는 아이콘 버튼(예: 다크모드 토글)에는 반드시 `aria-label`을 제공합니다.
- **의미론적 마크업**: `<div>` 남발을 지양하고 `<main>`, `<section>`, `<article>`, `<button>` 등 의미에 맞는 태그를 사용합니다.

### 7.4 동작 줄이기 (Reduced Motion)

- 시스템 설정에서 '동작 줄이기(Reduce Motion)'를 켠 사용자에게는 과도한 애니메이션을 보여주지 않습니다.
  - 구현: Tailwind의 `motion-reduce` 모디파이어 활용.
  - 예: `motion-reduce:transition-none` 또는 `motion-reduce:animate-none`.

### 7.5 터치 타겟 (Touch Targets)

- 모바일 환경에서 오터치를 방지하기 위해 상호작용 요소의 크기는 최소 **44x44px** 이상이어야 합니다.

---

## 8. 다크 모드 및 테마 전략 (Dark Mode & Theming)

본 프로젝트는 "Midnight Dev Studio" 컨셉에 맞춰 **Dark Mode를 우선적으로 디자인**하되, Shadcn/ui의 테마 시스템을 활용하여 라이트 모드(Light Mode)에서도 일관된 사용자 경험을 제공합니다.

### 8.1 컬러 매핑 테이블 (Color Mapping)

| 요소                      | 다크 모드 (Default)   | 라이트 모드 (Alternative) | 비고                    |
| :------------------------ | :-------------------- | :------------------------ | :---------------------- |
| **배경 (Background)**     | `Slate-950` (#020617) | `Slate-50` (#f8fafc)      | 전체 배경색             |
| **카드/표면 (Surface)**   | `Slate-900/50`        | `White` (#ffffff)         | Glassmorphism 효과 조절 |
| **주요 텍스트 (Text)**    | `Slate-50`            | `Slate-900`               | 가독성 최우선           |
| **보조 텍스트 (Muted)**   | `Slate-400`           | `Slate-500`               | 설명 및 메타 정보       |
| **브랜드 컬러 (Primary)** | `Violet-600`          | `Violet-600`              | 브랜드 정체성 유지      |
| **테두리 (Border)**       | `Slate-800`           | `Slate-200`               | 구분선 및 카드 경계     |

### 8.2 테마 토글 (Theme Toggle)

- **위치**: 헤더(Header)의 우측 상단에 배치합니다.
- **UI 요소**: `Sun` 및 `Moon` 아이콘을 사용하는 Shadcn/ui의 `Dropdown Menu` 또는 `Button` 형태를 사용합니다.
- **애니메이션**: `Framer Motion`을 활용하여 아이콘 전환 시 부드러운 회전(Rotation) 및 스케일(Scale) 효과를 적용합니다.

### 8.3 시스템 설정 존중 (System Preference)

- `next-themes` 라이브러리를 사용하여 사용자의 운영체제 설정을 초기 테마로 반영합니다.
- 사용자가 수동으로 테마를 변경할 경우 이를 `localStorage`에 저장하여 재방문 시에도 유지합니다.
