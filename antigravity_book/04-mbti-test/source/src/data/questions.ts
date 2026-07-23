import { Question } from "@/types";

export const questions: Question[] = [
    {
        id: 1,
        question: "프로젝트 시작! 폴더 구조를 어떻게 잡을까?",
        options: [
            {
                text: "폴더링은 예술이다. src/components/atoms... 아토믹 디자인 패턴으로 완벽하게 설계한다.",
                score: { FE: 2, ORDER: 1 },
            },
            {
                text: "일단 main.js 하나 만들고 코드를 때려 박는다. 나중에 나누면 됨.",
                score: { CHAOS: 2, PRACTICAL: 1 },
            },
            {
                text: "DB 스키마부터 짠다. 데이터가 곧 법이다.",
                score: { BE: 2, THEORETICAL: 1 },
            },
        ],
    },
    {
        id: 2,
        question: "치명적인 버그 발생! 로그를 확인해보니 'undefined'가 떴다.",
        options: [
            {
                text: "침착하게 크롬 개발자 도구(F12)를 켜고 네트워크 탭과 콘솔을 분석한다.",
                score: { FE: 2, PRACTICAL: 1 },
            },
            {
                text: "console.log('aaaa'), console.log('1111') 도배해서 어디까지 실행됐는지 본다.",
                score: { CHAOS: 2, PRACTICAL: 1 },
            },
            {
                text: "GDB나 디버거를 연결해서 어셈블리 단까지 까본다. undefined의 근원을 찾길 원한다.",
                score: { LOW: 2, THEORETICAL: 1 },
            },
        ],
    },
    {
        id: 3,
        question: "동료가 코드 리뷰 요청(PR)을 보냈다. 나는?",
        options: [
            {
                text: "변수명이 마음에 안 든다. 띄어쓰기, 줄바꿈, 컨벤션 하나하나 지적한다.",
                score: { ORDER: 2, STRICT: 1 },
            },
            {
                text: "\"LGTM! (Looks Good To Me)\" 일단 승인하고 칼퇴한다.",
                score: { CHAOS: 2, FLEXIBLE: 1 },
            },
            {
                text: "로직의 허점을 발견했다. '이 부분 동시성 이슈 발생할 것 같은데요?'",
                score: { BE: 2, THEORETICAL: 1 },
            },
        ],
    },
    {
        id: 4,
        question: "키보드를 산다면?",
        options: [
            {
                text: "알록달록 RGB LED가 번쩍이는 게이밍 키보드. 코딩은 기세다.",
                score: { FE: 1, SENSORY: 2 },
            },
            {
                text: "해피해킹(HHKB) 무각. 키캡에 글자가 없어야 진정한 고수.",
                score: { LOW: 2, INTUITIVE: 1 },
            },
            {
                text: "회사에서 주는 기본 멤브레인 키보드. 장비 탓 하지 않는다.",
                score: { BE: 1, PRACTICAL: 2 },
            },
        ],
    },
    {
        id: 5,
        question: "새로운 기술 스택 도입을 고민할 때?",
        options: [
            {
                text: "Github Star 수 1위, 트렌디한 기술! 일단 써보자! (Beta 버전도 환영)",
                score: { HIPSTER: 2, NEW: 1 },
            },
            {
                text: "10년 전부터 쓰던 거 씁시다. 안정성이 최고.",
                score: { STABLE: 2, OLD: 1 },
            },
            {
                text: "내가 라이브러리를 직접 만든다. 남의 코드는 믿을 수 없다.",
                score: { LOW: 2, DEVOPS: 3 },
            },
        ],
    },
    {
        id: 6,
        question: "단순 반복 작업이 생겼다. (엑셀 1000줄 수정 등)",
        options: [
            {
                text: "노동요(BGM) 틀고 무지성으로 빠르게 ctrl+c, ctrl+v 한다.",
                score: { MANUAL: 2 },
            },
            {
                text: "파이썬이나 쉘 스크립트를 짠다. 스크립트 짜는데 1시간 걸려도 손으로 하기 싫다.",
                score: { DEVOPS: 5, AUTO: 5 },
            },
            {
                text: "인턴이나 후배를 부른다. \"이거 좋은 경험이 될 거야.\"",
                score: { BE: 1, BOSS: 2 },
            },
        ],
    },
    {
        id: 7,
        question: "커밋 메시지를 작성할 때 나의 스타일은?",
        options: [
            {
                text: "feat(auth): add google oauth2 integration (상세하고 규격화됨)",
                score: { ORDER: 2, COMM: 1 },
            },
            {
                text: "fix: t",
                score: { CHAOS: 2, PRACTICAL: 1 },
            },
            {
                text: "Working on it... (나만 아는 진행 상황)",
                score: { SOLO: 2 },
            },
        ],
    },
    {
        id: 8,
        question: "배포 당일, 예상치 못한 서버 다운! 나의 심리 상태는?",
        options: [
            {
                text: "이미 예상했다. 롤백 플랜 가동! (침착하게 커맨드 입력)",
                score: { BE: 2, STABLE: 1, DEVOPS: 2 },
            },
            {
                text: "식은땀이 나지만 일단 구글링부터 한다. 'server dead what to do'",
                score: { PRACTICAL: 2 },
            },
            {
                text: "이럴 줄 알고 미리 사직서를 써놨다.",
                score: { CHAOS: 1, HUMOR: 2 },
            },
        ],
    },
    {
        id: 9,
        question: "동료와의 의견 충돌! 나는 어떻게 설득하는가?",
        options: [
            {
                text: "벤치마크 결과와 공식 문서 팩트를 들이민다.",
                score: { THEORETICAL: 2, BE: 1 },
            },
            {
                text: "일단 내가 짜온 코드를 보여주며 '이게 더 편하지 않아요?'라며 시연한다.",
                score: { FE: 2, SENSORY: 1 },
            },
            {
                text: "소고기 회식을 제안하며 분위기로 승부한다.",
                score: { COMM: 2, BOSS: 1 },
            },
        ],
    },
    {
        id: 10,
        question: "코드의 가독성 vs 퍼포먼스?",
        options: [
            {
                text: "협업이 먼저다. 주석 없어도 이해 가능한 클린 코드가 최고.",
                score: { ORDER: 2, COMM: 1 },
            },
            {
                text: "퍼포먼스가 깡패다. 비트 연산을 써서라도 1ms를 줄인다.",
                score: { LOW: 2, THEORETICAL: 1 },
            },
            {
                text: "둘 다 포기하고 기능을 빨리 완성하는 데 집중한다.",
                score: { PRACTICAL: 2, CHAOS: 1 },
            },
        ],
    },
    {
        id: 11,
        question: "나의 깃허브 잔디 상태는?",
        options: [
            {
                text: "축구장 급. 1일 1커밋 안 하면 잠이 안 온다.",
                score: { COMM: 2, ORDER: 1 },
            },
            {
                text: "드문드문... 폭우가 쏟아진 뒤 가뭄이 찾아온 듯한 들쭉날쭉함.",
                score: { CHAOS: 1, PRACTICAL: 1 },
            },
            {
                text: "황무지. 커밋보다는 코드 완성 그 자체가 중요하다.",
                score: { SOLO: 2, BE: 1 },
            },
        ],
    },
    {
        id: 12,
        question: "꿈꾸는 나의 노년 생활은?",
        options: [
            {
                text: "직접 만든 서비스로 대박 나서 실리콘밸리에서 은퇴.",
                score: { FE: 1, HIPSTER: 1 },
            },
            {
                text: "조용한 시골에서 농사 지으며, 직접 짠 자동화 센서로 물을 준다.",
                score: { DEVOPS: 5, LOW: 1, AUTO: 3 },
            },
            {
                text: "전설의 시니어 개발자로 남아 고대 유물을 유지보수한다.",
                score: { STABLE: 2, BE: 1 },
            },
        ],
    },
];
