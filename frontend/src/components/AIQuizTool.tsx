import { useState, useEffect } from 'react';
import api from '../services/api';
import { QuizQuestion, QuizAttempt } from '../types';

interface Props {
    subjectId: number;
    subjectName: string;
    onDataChanged?: () => void;
}

export function AIQuizTool({ subjectId, subjectName, onDataChanged }: Props) {
    const [notes, setNotes] = useState('');
    const [numQuestions, setNumQuestions] = useState(4);
    const [difficulty, setDifficulty] = useState('Intermediário');
    const [questions, setQuestions] = useState<QuizQuestion[]>([]);
    const [loading, setLoading] = useState(false);

    const [userAnswers, setUserAnswers] = useState<Record<number, string>>({});
    const [showResults, setShowResults] = useState(false);
    const [attempts, setAttempts] = useState<QuizAttempt[]>([]);
    const [savedCardIndexes, setSavedCardIndexes] = useState<Record<number, boolean>>({});

    const fetchAttempts = async () => {
        try {
            const res = await api.get<QuizAttempt[]>(`/subjects/${subjectId}/quizzes`);
            setAttempts(res.data);
        } catch (error) {
            console.error('Erro ao buscar histórico de quizzes', error);
        }
    };

    useEffect(() => {
        fetchAttempts();
    }, [subjectId]);

    const handleLoadSampleText = () => {
        setNotes(
            'Na arquitetura de microsserviços distribuídos, o padrão Circuit Breaker impede que falhas em um serviço ' +
            'remoto se propaguem em cascata por toda a plataforma. Ele opera como uma máquina de estados com três fases: ' +
            'Closed (fluxo normal monitorando taxa de erro), Open (rejeição rápida com fallback local) e Half-Open ' +
            '(envio controlado de requisições de sonda para verificar recuperação). Em conjunto com filas assíncronas ' +
            'e consumidores idempotentes, garante alta resiliência e tolerância a partições.'
        );
    };

    const handleGenerate = async () => {
        if (notes.trim().length < 50) return;
        setLoading(true);
        setQuestions([]);
        setShowResults(false);
        setUserAnswers({});
        setSavedCardIndexes({});

        try {
            const response = await api.post<QuizQuestion[]>('/ai/generate_quiz', {
                text: notes,
                num_questions: numQuestions,
                difficulty,
            });
            setQuestions(response.data);
        } catch (error) {
            console.error('Erro ao gerar quiz:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleOptionSelect = (qIndex: number, option: string) => {
        if (showResults) return;
        setUserAnswers((prev) => ({ ...prev, [qIndex]: option }));
    };

    const handleVerifyResults = async () => {
        setShowResults(true);
        const correctCount = questions.reduce(
            (acc, q, idx) => acc + (userAnswers[idx] === q.answer ? 1 : 0),
            0
        );
        try {
            await api.post('/quizzes/attempts', {
                subject_id: subjectId,
                topic_summary: `${subjectName} (${difficulty})`,
                total_questions: questions.length,
                correct_answers: correctCount,
            });
            fetchAttempts();
            onDataChanged?.();
        } catch (error) {
            console.error('Erro ao registrar tentativa de quiz', error);
        }
    };

    const handleConvertQuestionToFlashcard = async (q: QuizQuestion, idx: number) => {
        try {
            await api.post('/flashcards/', {
                subject_id: subjectId,
                front: q.question,
                back: `${q.answer}${q.explanation ? ` — ${q.explanation}` : ''}`,
                difficulty_tag: 'Difícil',
            });
            setSavedCardIndexes((prev) => ({ ...prev, [idx]: true }));
            onDataChanged?.();
        } catch (error) {
            console.error('Erro ao converter questão em flashcard', error);
        }
    };

    const correctCount = questions.reduce(
        (acc, q, idx) => acc + (userAnswers[idx] === q.answer ? 1 : 0),
        0
    );

    return (
        <div className="module-section">
            <div className="module-toolbar">
                <div>
                    <h3>🧠 Simulador de Quiz Ativo com IA & Conversão de Erros</h3>
                    <p className="module-subtitle">
                        Transforme qualquer resumo ou artigo em um simulado com explicação pedagógica e converta dúvidas diretamente em Flashcards SRS.
                    </p>
                </div>
                {!questions.length && (
                    <button className="btn-secondary-action" onClick={handleLoadSampleText}>
                        📄 Carregar Texto Técnico de Exemplo
                    </button>
                )}
            </div>

            {!questions.length ? (
                <div className="quiz-generator-box">
                    <div className="quiz-controls-row">
                        <div className="form-field">
                            <label>Nível de Profundidade Cognitiva</label>
                            <select
                                className="select-input"
                                value={difficulty}
                                onChange={(e) => setDifficulty(e.target.value)}
                            >
                                <option value="Iniciante">Iniciante (Conceitos Fundamentais)</option>
                                <option value="Intermediário">Intermediário (Aplicação & Relações)</option>
                                <option value="Avançado">Avançado (Arquitetura & Casos Críticos)</option>
                            </select>
                        </div>
                        <div className="form-field">
                            <label>Quantidade de Questões</label>
                            <select
                                className="select-input"
                                value={numQuestions}
                                onChange={(e) => setNumQuestions(Number(e.target.value))}
                            >
                                <option value={3}>3 Questões Rápidas</option>
                                <option value={4}>4 Questões Padrão</option>
                                <option value={6}>6 Questões Aprofundadas</option>
                            </select>
                        </div>
                    </div>

                    <textarea
                        rows={5}
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                        placeholder="Cole suas anotações, resumo de artigo ou transcrição de aula aqui (mínimo 50 caracteres)..."
                    />

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '12px' }}>
                        <span className="char-counter">{notes.length} caracteres digitados (mínimo 50)</span>
                        <button
                            className="btn-primary-action"
                            onClick={handleGenerate}
                            disabled={loading || notes.trim().length < 50}
                        >
                            {loading ? '🤖 Gerando Questões Contextualizadas...' : '✨ Gerar Simulado com Explicações'}
                        </button>
                    </div>
                </div>
            ) : (
                <div className="quiz-active-container">
                    {showResults && (
                        <div className="quiz-score-banner">
                            <div>
                                <h4>
                                    Resultado do Simulado: {correctCount} de {questions.length} acertos (
                                    {Math.round((correctCount / questions.length) * 100)}%)
                                </h4>
                                <p>Revise as explicações abaixo e envie questões desafiadoras para seu deck de Repetição Espaçada SRS.</p>
                            </div>
                            <button className="btn-secondary-action" onClick={() => setQuestions([])}>
                                ↻ Gerar Novo Simulado
                            </button>
                        </div>
                    )}

                    {questions.map((q, qIndex) => (
                        <div key={qIndex} className="quiz-question-card">
                            <div className="quiz-question-header">
                                <span className="badge-pill" style={{ background: '#eef2ff', color: '#4338ca' }}>
                                    Questão {qIndex + 1} {q.topic_tag ? `• ${q.topic_tag}` : ''}
                                </span>
                                <button
                                    className="btn-outline-sm"
                                    disabled={!!savedCardIndexes[qIndex]}
                                    onClick={() => handleConvertQuestionToFlashcard(q, qIndex)}
                                >
                                    {savedCardIndexes[qIndex] ? '✓ Adicionado ao Deck SRS' : '🃏 Converter em Flashcard SRS'}
                                </button>
                            </div>

                            <p className="quiz-question-title">{q.question}</p>

                            <div className="quiz-options-list">
                                {q.options.map((opt, optIndex) => {
                                    const isSelected = userAnswers[qIndex] === opt;
                                    const isCorrect = opt === q.answer;

                                    let statusClass = '';
                                    if (showResults) {
                                        if (isCorrect) statusClass = 'opt-correct';
                                        else if (isSelected && !isCorrect) statusClass = 'opt-wrong';
                                    } else if (isSelected) {
                                        statusClass = 'opt-selected';
                                    }

                                    return (
                                        <div
                                            key={optIndex}
                                            onClick={() => handleOptionSelect(qIndex, opt)}
                                            className={`quiz-option-row ${statusClass}`}
                                        >
                                            <span className="opt-letter">{String.fromCharCode(65 + optIndex)}</span>
                                            <span>{opt}</span>
                                        </div>
                                    );
                                })}
                            </div>

                            {showResults && q.explanation && (
                                <div className="quiz-explanation-box">
                                    <strong>💡 Explicação Pedagógica:</strong> {q.explanation}
                                </div>
                            )}
                        </div>
                    ))}

                    {!showResults && (
                        <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                            <button className="btn-secondary-action" onClick={() => setQuestions([])}>
                                Cancelar
                            </button>
                            <button className="btn-primary-action" onClick={handleVerifyResults}>
                                ✅ Corrigir Simulado e Registrar Retenção
                            </button>
                        </div>
                    )}
                </div>
            )}

            {attempts.length > 0 && (
                <div className="quiz-history-panel">
                    <h4>📊 Histórico de Desempenho em Quizzes ({attempts.length})</h4>
                    <div className="quiz-attempts-grid">
                        {attempts.slice(0, 6).map((att) => (
                            <div key={att.id} className="quiz-attempt-badge">
                                <div>
                                    <strong>{att.topic_summary}</strong>
                                    <span>{att.correct_answers}/{att.total_questions} questões corretas</span>
                                </div>
                                <span
                                    className="score-tag"
                                    style={{
                                        background: att.score_percent >= 80 ? '#ecfdf5' : '#fffbeb',
                                        color: att.score_percent >= 80 ? '#059669' : '#d97706',
                                    }}
                                >
                                    {att.score_percent}%
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
