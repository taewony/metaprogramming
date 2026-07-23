/**
 * 타이머 애플리케이션의 핵심 로직을 담당하는 클래스입니다.
 * 시간 설정, 시작, 일시정지, 초기화 및 테마 변경 기능을 제공합니다.
 */
class Timer {
    /**
     * Timer 클래스의 생성자입니다.
     * DOM 요소를 초기화하고 이벤트 리스너를 설정합니다.
     */
    constructor() {
        // DOM 요소 가져오기
        this.hoursElement = document.getElementById('hours');
        this.minutesElement = document.getElementById('minutes');
        this.secondsElement = document.getElementById('seconds');

        this.inputHours = document.getElementById('input-hours');
        this.inputMinutes = document.getElementById('input-minutes');
        this.inputSeconds = document.getElementById('input-seconds');
        this.inputGroup = document.getElementById('input-group');

        this.startBtn = document.getElementById('start-btn');
        this.pauseBtn = document.getElementById('pause-btn');
        this.resetBtn = document.getElementById('reset-btn');
        this.pastaBtn = document.getElementById('pasta-btn');
        this.themeToggle = document.getElementById('theme-toggle');

        // 타이머 상태 변수 초기화
        this.totalSeconds = 0;
        this.intervalId = null;
        this.isRunning = false;

        // 이벤트 리스너 초기화
        this.initListeners();
    }

    /**
     * 버튼 및 입력 필드에 대한 이벤트 리스너를 등록합니다.
     */
    initListeners() {
        this.startBtn.addEventListener('click', () => this.start());
        this.pauseBtn.addEventListener('click', () => this.pause());
        this.resetBtn.addEventListener('click', () => this.reset());
        this.pastaBtn.addEventListener('click', () => this.startPasta());
        this.themeToggle.addEventListener('click', () => this.toggleTheme());

        // 입력 값 유효성 검사 (음수 방지 및 분/초 59 제한)
        [this.inputHours, this.inputMinutes, this.inputSeconds].forEach(input => {
            input.addEventListener('change', () => {
                if (input.value < 0) input.value = 0;
                // 시(Hours)는 59분을 넘을 수 있지만, 분/초는 59를 넘을 수 없음
                if (input !== this.inputHours && input.value > 59) input.value = 59;
            });
        });
    }

    /**
     * 현재 남은 시간을 화면에 업데이트합니다.
     * 시, 분, 초 단위로 변환하여 표시합니다.
     */
    updateDisplay() {
        // 총 초를 시, 분, 초로 변환
        const h = Math.floor(this.totalSeconds / 3600);
        const m = Math.floor((this.totalSeconds % 3600) / 60);
        const s = this.totalSeconds % 60;

        // 화면 업데이트 (2자리수로 패딩)
        this.hoursElement.textContent = h.toString().padStart(2, '0');
        this.minutesElement.textContent = m.toString().padStart(2, '0');
        this.secondsElement.textContent = s.toString().padStart(2, '0');

        // 브라우저 탭 타이틀 업데이트
        document.title = `${this.hoursElement.textContent}:${this.minutesElement.textContent}:${this.secondsElement.textContent} - Focus Timer`;
    }

    /**
     * 타이머를 시작합니다.
     * 입력된 시간을 바탕으로 카운트다운을 시작하거나, 일시정지된 타이머를 재개합니다.
     */
    start() {
        if (this.isRunning) return;

        // 새로운 타이머 시작 (일시정지 상태가 아닐 때)
        if (this.totalSeconds === 0) {
            // 입력 필드에서 값 가져오기
            const h = parseInt(this.inputHours.value) || 0;
            const m = parseInt(this.inputMinutes.value) || 0;
            const s = parseInt(this.inputSeconds.value) || 0;

            this.totalSeconds = h * 3600 + m * 60 + s;

            if (this.totalSeconds === 0) return; // 0초면 시작하지 않음
        }

        this.isRunning = true;
        this.inputGroup.classList.add('hidden'); // 입력 필드 숨김
        this.startBtn.disabled = true;
        this.pauseBtn.disabled = false;

        this.updateDisplay(); // 즉시 시간 표시 업데이트

        // 1초마다 타이머 감소
        this.intervalId = setInterval(() => {
            if (this.totalSeconds > 0) {
                this.totalSeconds--;
                this.updateDisplay();
            } else {
                this.finish();
            }
        }, 1000);
    }

    /**
     * 타이머를 일시정지합니다.
     */
    pause() {
        if (!this.isRunning) return;

        clearInterval(this.intervalId);
        this.isRunning = false;
        this.startBtn.disabled = false;
        this.pauseBtn.disabled = true;
        this.startBtn.textContent = "재개";
    }

    /**
     * 타이머를 초기화합니다.
     * 진행 중인 타이머를 멈추고 시간을 0으로 설정합니다.
     */
    reset() {
        this.pause();
        this.totalSeconds = 0;
        this.updateDisplay();

        this.inputGroup.classList.remove('hidden');
        this.startBtn.textContent = "시작";
        this.startBtn.disabled = false;
        this.pauseBtn.disabled = true;

        // 입력 필드 초기화
        this.inputHours.value = '';
        this.inputMinutes.value = '';
        this.inputSeconds.value = '';

        document.title = "Focus Timer";
    }

    /**
     * 타이머가 종료되었을 때 호출됩니다.
     * 알림을 표시하고 UI를 초기 상태로 되돌립니다.
     */
    finish() {
        this.pause();
        this.startBtn.textContent = "시작";
        this.inputGroup.classList.remove('hidden');

        // 종료 시 시각적 피드백 (배경색 변경)
        document.body.style.background = 'radial-gradient(circle at top right, #331e1e, #1a0f0f)';
        const originalColor = getComputedStyle(document.documentElement).getPropertyValue('--accent-color');
        document.documentElement.style.setProperty('--accent-color', '#ef4444');

        setTimeout(() => {
            alert("시간 종료!");
            // 스타일 초기화
            document.body.style.background = '';
            document.documentElement.style.setProperty('--accent-color', originalColor);
        }, 100);
    }

    /**
     * 파스타 삶기 프리셋 (8분)을 시작합니다.
     */
    startPasta() {
        this.reset();
        this.totalSeconds = 8 * 60; // 8분
        this.inputHours.value = 0;
        this.inputMinutes.value = 8;
        this.inputSeconds.value = 0;
        this.updateDisplay();
        this.start();
    }

    /**
     * 라이트 모드와 다크 모드를 전환합니다.
     */
    toggleTheme() {
        document.body.classList.toggle('light-mode');
        const isLight = document.body.classList.contains('light-mode');
        this.themeToggle.textContent = isLight ? '☀️' : '🌙';
        this.themeToggle.setAttribute('aria-label', isLight ? 'Switch to Dark Mode' : 'Switch to Light Mode');
    }
}

// 애플리케이션 초기화
const timer = new Timer();
