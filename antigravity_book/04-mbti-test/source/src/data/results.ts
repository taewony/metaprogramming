import { MBTIResult } from "@/types";

export const results: MBTIResult[] = [
    {
        id: "fe_god",
        name: "div 태그 조물주 (FE)",
        image: "/images/result_fe_meme.png",
        description: "사용자가 못 느껴도 나는 느낀다. 모니터에 자를 대고 다니는 픽셀 변태. UI가 1px이라도 어긋나면 호흡곤란이 오며, 디자이너와 영혼의 파트너(혹은 원수)가 됩니다.",
        traits: ["#1px의_집착", "#CSS는_예술", "#반응형_성애자"],
        match: {
            best: "be_ghost",
            worst: "chaos_magician",
        },
    },
    {
        id: "be_ghost",
        name: "JSON 깎는 노인 (BE)",
        image: "/images/result_be_meme.png",
        description: "화면은 장식일 뿐. 터미널의 검은 화면과 흰 글씨에서 마음의 안정을 찾음. API 명세서가 그들의 성경이며, 프론트엔드 개발자가 '데이터 이상한데요?'라고 하면 화가 납니다.",
        traits: ["#API명세서가_법", "#트래픽_방어", "#쿼리_최적화"],
        match: {
            best: "fe_god",
            worst: "chaos_magician",
        },
    },
    {
        id: "chaos_magician",
        name: "연금술사형 흑마법사 (CHAOS)",
        image: "/images/result_chaos_meme.png",
        description: "본인도 해석 불가능한 코드로 기적을 행함. 에러가 나면 try-catch로 감싸버리고, 버그를 기능(Feature)이라고 우깁니다. 유지보수 담당자에겐 재앙 그 자체.",
        traits: ["#스파게티_장인", "#배포가_곧_테스트", "#나만_아는_변수명"],
        match: {
            best: "fullstack_slave",
            worst: "be_ghost",
        },
    },
    {
        id: "script_villain",
        name: "스크립트 자동화 빌런 (DevOps)",
        image: "/images/result_devops_meme.png",
        description: "3번 이상 반복하면 죄악. 커피 타는 것도 쉘 스크립트로 짤 기세. 마우스 쓰는 걸 혐오하며, 5분 걸릴 일을 자동화하겠다고 5시간 동안 스크립트를 짭니다.",
        traits: ["#Bash_Master", "#모든걸_자동화", "#CI/CD_중독"],
        match: {
            best: "fullstack_slave",
            worst: "fe_god",
        },
    },
    {
        id: "low_level_ghost",
        name: "0과 1의 망령 (Low Level)",
        image: "/images/result_low_meme.png",
        description: "가비지 컬렉터? 나약한 소리. 메모 주소를 직접 따야 잠이 옴. 최적화되지 않은 코드를 보면 두드러기가 나며, 포인터와 썸 타는 중입니다.",
        traits: ["#C언어_네이티브", "#포인터_연산", "#메모리최적화"],
        match: {
            best: "be_ghost",
            worst: "fe_god",
        },
    },
    {
        id: "fullstack_slave",
        name: "천수관음 풀스택 예비군 (Full Stack)",
        image: "/images/result_fullstack.png",
        description: "다 할 줄 알아서 모든 똥을 치우게 되는 비운의 실력자. 프론트? 백엔드? 그냥 제가 다 할게요. 가끔 내가 무엇을 위해 코딩하는지 자아성찰이 필요함.",
        traits: ["#풀스택_노예", "#다재다능", "#정체성혼란"],
        match: {
            best: "script_villain",
            worst: "chaos_magician",
        },
    },
    {
        id: "community_hero",
        name: "잔디심기 조경사 (Community)",
        image: "/images/result_community.png",
        description: "1일 1커밋 안 하면 금단현상 옴. 코딩보다 깃허브 초록색 잔디 관리에 더 진심임. 오픈소스 기여를 통해 인류애를 느끼며, 깃허브 프로필이 곧 신분증.",
        traits: ["#잔디_매니아", "#오픈소스_전도사", "#소통왕"],
        match: {
            best: "tech_hipster",
            worst: "stable_scholar",
        },
    },
    {
        id: "tech_hipster",
        name: "찍먹 전문 힙스터 (Hipster)",
        image: "/images/result_hipster.png",
        description: "아직도 React 써요? 요즘은 OOO가 대세인데. 프로젝트 완성보다 기술 스택 정하는 게 더 즐거움. 유행하는 라이브러리 찍먹하다 끝나는 게 일상이지만 트렌드는 놓치지 않음.",
        traits: ["#얼리어답터", "#기술_찍먹", "#베타테스터"],
        match: {
            best: "community_hero",
            worst: "stable_scholar",
        },
    },
    {
        id: "stable_scholar",
        name: "돌다리 두드리는 선비 (Stable)",
        image: "/images/result_stable.png",
        description: "버전 올리지 마세요. 검증되지 않은 라이브러리는 절대 npm install 하지 않음. 안정성이 최고이며, 10년 뒤에도 돌아갈 코드를 짜는 것이 목표입니다.",
        traits: ["#안정성_신봉자", "#레거시_수호자", "#보수적_코딩"],
        match: {
            best: "be_ghost",
            worst: "tech_hipster",
        },
    },
];
