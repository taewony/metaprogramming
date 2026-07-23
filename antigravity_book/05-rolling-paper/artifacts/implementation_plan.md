# 메시지 수정 및 비로그인 접근 기능 구현 계획

## 목표

1.  **메시지 수정**: 사용자가 자신이 작성한 메시지를 더블 클릭하여 내용을 수정할 수 있도록 합니다.
2.  **비로그인 접근**: 로그인이 되어 있지 않은 사용자도 보드를 조회할 수 있도록 접근 제한을 완화합니다. (단, 작성은 제한)

## 변경 사항

### Frontend Components

#### [MODIFY] [App.jsx](file:///c:/Users/ikiny/antigravity/rolling_paper/src/App.jsx)

- `/board/:slug` 경로의 `Navigate` 조건을 수정하여 비로그인 사용자도 접근할 수 있도록 변경합니다.
- `<BoardPage />` 컴포넌트에 `session` prop이 `null`일 수 있음을 감안하여 전달합니다.

#### [MODIFY] [BoardPage.jsx](file:///c:/Users/ikiny/antigravity/rolling_paper/src/pages/BoardPage.jsx)

- **비로그인 처리**:
  - `session`이 없을 경우 "메시지 남기기" 버튼을 숨기거나 로그인 유도 모달을 띄우도록 합니다.
  - Drag & Drop 핸들러에서 `session` 확인을 강화합니다.
- **수정 기능**:
  - `motion.div` (포스트잇)에 `onDoubleClick` 핸들러를 추가합니다.
  - 본인이 작성한 글(`isOwner`)인 경우에만 수정 모달을 엽니다.
  - `PostItModal`을 재사용하되, `editMode`와 `initialData`를 전달하여 수정 화면을 구성합니다.
  - 모달 `onSubmit` 시 `updateMessageContent` API를 호출하도록 처리합니다.

#### [MODIFY] [PostItModal.jsx](file:///c:/Users/ikiny/antigravity/rolling_paper/src/components/PostItModal.jsx)

- `initialData` prop을 받아 `content`, `senderName`, `color` 상태의 초기값을 설정할 수 있도록 수정합니다.
- 버튼 텍스트를 상황에 맞게 ('등록하기' / '수정하기') 변경합니다.

### API & Library

#### [MODIFY] [src/lib/api.js](file:///c:/Users/ikiny/antigravity/rolling_paper/src/lib/api.js)

- `updateMessageContent(id, { content, sender_name, color })` 함수를 추가합니다.
  - `messages` 테이블의 해당 컬럼들을 업데이트합니다.

## 검증 계획

### 수동 검증

1.  **비로그인 접근**:
    - 로그아웃 상태에서 `/board/{slug}` URL로 직접 접근하여 보드가 보이는지 확인합니다.
    - "메시지 남기기" 버튼이 보이지 않거나 동작하지 않는지 확인합니다.
2.  **메시지 수정**:
    - 로그인 후 자신이 쓴 포스트잇을 더블 클릭합니다.
    - 수정 모달이 뜨고 기존 내용이 채워져 있는지 확인합니다.
    - 내용을 변경하고 저장하면 화면에 즉시 반영되는지(Realtime 연동 확인) 테스트합니다.
