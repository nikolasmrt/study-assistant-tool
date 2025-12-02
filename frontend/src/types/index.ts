export interface Subject {
    id: number;
    name: string;
    description?: string;
}

export interface SubjectCreate {
    name: string;
    description?: string;
}