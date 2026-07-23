import { create } from 'zustand';
import { Score } from '@/types';

interface TestState {
    currentQuestionIndex: number;
    scores: Score;
    answers: number[]; // Index of selected option for each question
    nickname: string;
    setNickname: (name: string) => void;
    setAnswer: (questionId: number, selectedOptionIndex: number, score: Score) => void;
    nextQuestion: () => void;
    resetTest: () => void;
}

export const useTestStore = create<TestState>((set) => ({
    currentQuestionIndex: 0,
    scores: {},
    answers: [],
    nickname: "",
    setNickname: (name) => set({ nickname: name }),
    setAnswer: (questionId, selectedOptionIndex, score) =>
        set((state) => {
            const newScores = { ...state.scores };
            Object.entries(score).forEach(([key, value]) => {
                newScores[key] = (newScores[key] || 0) + value;
            });
            const newAnswers = [...state.answers];
            newAnswers[state.currentQuestionIndex] = selectedOptionIndex; // Store answer for current question

            return {
                scores: newScores,
                answers: newAnswers,
            };
        }),
    nextQuestion: () =>
        set((state) => ({ currentQuestionIndex: state.currentQuestionIndex + 1 })),
    resetTest: () =>
        set({
            currentQuestionIndex: 0,
            scores: {},
            answers: [],
            nickname: "",
        }),
}));
