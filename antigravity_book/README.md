# Antigravity Book Project

이 프로젝트는 'Antigravity' 책의 실습 코드를 담고 있습니다. AI와 함께 효율적으로 코딩하는 방법을 배우며, 특히 **ROCK 법칙**을 기반으로 프롬프트를 작성하는 연습을 합니다.

## ROCK 법칙
프롬프트를 작성할 때 다음 네 가지 요소를 기억하세요:

1. **Role (역할)**: AI에게 구체적인 전문가 역할을 부여합니다. (예: "당신은 시니어 파이썬 개발자입니다.")
2. **Objective (목표)**: 달성하고자 하는 최종 결과를 명확히 정의합니다.
3. **Context (맥락)**: 필요한 배경 정보와 제약 사항을 제공합니다.
4. **Knowledge (지식/형식)**: 참고할 데이터나 출력 형식을 지정합니다.

## 프로젝트 구조

각 폴더는 독립적인 프로젝트를 담고 있으며, 'Antigravity' 책의 학습 단계에 따라 구성되어 있습니다.

### 🚀 [01-hello-antigravity](./01-hello-antigravity/)
- **주제**: AI 페어 프로그래밍 입문
- **내용**: AI와 소통하는 기초 방법과 환경 설정 실습.
- **주요 파일**: 기초 실습 스크립트 등.

### 🎮 [02-retro-game](./02-retro-game/)
- **주제**: Pygame을 활용한 레트로 게임 제작
- **내용**: 'Space Defender'라는 우주 슈팅 게임 개발. 게임 루프, 이미지/사운드 에셋 관리, 충돌 판정 구현.
- **기술 스택**: Python, Pygame.

### 📂 [03-folder-organizer](./03-folder-organizer/)
- **주제**: 파이썬 자동화 도구 제작
- **내용**: 난잡한 폴더 내 파일들을 확장자별로 자동 분류하여 정리해주는 실용적인 도구.
- **기술 스택**: Python (`os`, `shutil` 라이브러리).

### 🧪 [04-mbti-test](./04-mbti-test/)
- **주제**: 현대적인 웹 프론트엔드 개발
- **내용**: '개발자 성향 테스트(MBTI)' 웹 서비스. 애니메이션 효과와 반응형 레이아웃 적용.
- **기술 스택**: Next.js (App Router), Tailwind CSS, Framer Motion, Lucide React.

### 📝 [05-rolling-paper](./05-rolling-paper/)
- **주제**: 풀스택 모바일 앱 및 서버 개발
- **내용**: 실시간으로 메시지를 주고받는 롤링페이퍼 서비스.
- **기술 스택**: 
  - **Client**: Expo (React Native), React Navigation.
  - **Server/Web**: Vite, React, Tailwind CSS.
  - **Backend**: Supabase (Database, Auth, Real-time).

