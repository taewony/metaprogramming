
export interface Score {
    [key: string]: number;
}

export interface Option {
    text: string;
    score: Score;
}

export interface Question {
    id: number;
    question: string;
    options: Option[];
}

export interface MBTIResult {
    id: string;
    name: string;
    image: string;
    description: string;
    traits: string[];
    match: {
        best: string;
        worst: string;
    };
}
