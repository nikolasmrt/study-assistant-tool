export interface Subject {
    id: number;
    name: string;
    description?: string;
    category?: string;
    target_retention?: number;
}

export interface SubjectCreate {
    name: string;
    description?: string;
    category?: string;
    target_retention?: number;
}

export interface Flashcard {
    id: number;
    subject_id: number;
    front: string;
    back: string;
    box_level: number;
    ease_factor: number;
    interval_days: number;
    review_count: number;
    difficulty_tag: string;
    last_reviewed_at?: string;
    next_review_at?: string;
}

export interface FeynmanEvaluation {
    id?: number;
    subject_id?: number;
    concept_title: string;
    target_audience: string;
    explanation_text: string;
    clarity_score: number;
    readability_level: string;
    strengths: string[];
    blind_spots: string[];
    socratic_questions: string[];
    suggested_analogy: string;
    created_at?: string;
}

export interface CornellNote {
    id: number;
    subject_id: number;
    title: string;
    cues: string;
    notes: string;
    summary: string;
    created_at: string;
}

export interface QuizQuestion {
    question: string;
    options: string[];
    answer: string;
    explanation?: string;
    topic_tag?: string;
}

export interface QuizAttempt {
    id: number;
    subject_id: number;
    topic_summary: string;
    total_questions: number;
    correct_answers: number;
    score_percent: number;
    created_at: string;
}

export interface SubjectCognitiveStats {
    subject_id: number;
    subject_name: string;
    category: string;
    total_cards: number;
    due_cards: number;
    mastered_cards: number;
    retention_index: number;
    box_distribution: Record<string, number>;
    feynman_count: number;
    avg_feynman_score: number;
    cornell_count: number;
    quiz_count: number;
    avg_quiz_score: number;
    total_study_minutes: number;
}

export interface GlobalAnalytics {
    total_subjects: number;
    total_flashcards: number;
    due_flashcards_today: number;
    mastered_flashcards: number;
    global_retention_index: number;
    box_distribution: Record<string, number>;
    total_feynman_evaluations: number;
    avg_feynman_clarity: number;
    total_cornell_notes: number;
    total_quizzes_taken: number;
    avg_quiz_accuracy: number;
    total_study_minutes: number;
    subjects_breakdown: SubjectCognitiveStats[];
}
