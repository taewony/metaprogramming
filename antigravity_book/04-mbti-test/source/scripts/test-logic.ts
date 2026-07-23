
import { questions } from "@/data/questions";
import { results } from "@/data/results";

// Mock store logic
const scores: Record<string, number> = {};

function answer(questionId: number, optionIndex: number) {
    const q = questions.find(q => q.id === questionId);
    if (!q) return;
    const score = q.options[optionIndex].score;
    Object.entries(score).forEach(([k, v]) => {
        scores[k] = (scores[k] || 0) + v;
    });
}

function calculate() {
    let resultId = "fullstack_unicorn"; // Default
    const s = scores;

    if ((s.FE || 0) > (s.BE || 0)) {
        if ((s.SENSORY || 0) > (s.INTUITIVE || 0)) {
            resultId = "frontend_master";
        } else {
            resultId = "tech_hipster";
        }
    } else {
        if ((s.ORDER || 0) > (s.CHAOS || 0)) {
            resultId = "backend_architect";
        } else {
            resultId = "chaos_wizard";
        }
    }
    if ((s.AUTO || 0) > 0 && (s.THEORETICAL || 0) > 0) {
        resultId = "automation_king";
    }

    const exists = results.find(r => r.id === resultId);
    return exists ? exists.id : "error";
}

// Test Case 1: Frontend Master
// Q1: FE (Opt 0)
// Q2: PRACTICAL (Opt 0) - irrelevant?
// Q3: ORDER (Opt 1) - irrelevant?
// Q4: SENSORY (Opt 0) => FE > BE + SENSORY > INTUITIVE
console.log("Running Test Case 1: Frontend Master path");
scores['FE'] = 0; scores['BE'] = 0; // Reset
answer(1, 0); // FE
answer(4, 0); // SENSORY
const res1 = calculate();
console.log(`Expected: frontend_master, Got: ${res1}`);

// Test Case 2: Backend Architect
console.log("Running Test Case 2: Backend Architect path");
scores['FE'] = 0; scores['BE'] = 0; scores['ORDER'] = 0; scores['CHAOS'] = 0;
answer(1, 1); // BE
answer(3, 1); // ORDER
const res2 = calculate();
console.log(`Expected: backend_architect, Got: ${res2}`);

