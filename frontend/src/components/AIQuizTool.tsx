import { useState } from 'react';
import api from '../services/api';

interface Question {
    question: string;
    options: string[];
    answer: string;
}

export function AIQuizTool() {
    const [notes, setNotes] = useState('');
    const [questions, setQuestions] = useState<Question[]>([]);
    const [loading, setLoading] = useState(false);
    
    // Estado para controlar respostas do usuário (índice da pergunta -> resposta escolhida)
    const [userAnswers, setUserAnswers] = useState<{[key: number]: string}>({});
    const [showResults, setShowResults] = useState(false);

    const handleGenerate = async () => {
        if (!notes) return;
        setLoading(true);
        setQuestions([]);
        setShowResults(false);
        setUserAnswers({});

        try {
            const response = await api.post('/ai/generate_quiz', { text: notes });
            setQuestions(response.data);
        } catch (error) {
            alert("Erro ao gerar quiz. Verifique se o texto é longo o suficiente.");
        } finally {
            setLoading(false);
        }
    };

    const handleOptionSelect = (qIndex: number, option: string) => {
        if (showResults) return; // Trava mudanças após ver resultado
        setUserAnswers(prev => ({...prev, [qIndex]: option}));
    };

    return (
        <div style={{ textAlign: 'left', maxWidth: '600px', margin: '0 auto' }}>
            
            {/* Área de Input */}
            {!questions.length && (
                <div className="card">
                    <h3>🧠 Gerador de Quiz com IA</h3>
                    <p style={{ fontSize: '0.9rem', color: '#666' }}>
                        Cole suas anotações ou um texto sobre a matéria, e a IA criará um teste para você.
                    </p>
                    <textarea 
                        rows={6}
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                        placeholder="Cole seu texto de estudo aqui... (Mínimo 50 caracteres)"
                        style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #ddd', marginBottom: '10px' }}
                    />
                    <button onClick={handleGenerate} disabled={loading || notes.length < 50}>
                        {loading ? '🤖 A IA está pensando...' : '✨ Gerar Quiz Automático'}
                    </button>
                </div>
            )}

            {/* Área do Quiz Gerado */}
            {questions.length > 0 && (
                <div className="quiz-container">
                    <h3>📝 Quiz Gerado</h3>
                    
                    {questions.map((q, qIndex) => (
                        <div key={qIndex} className="card" style={{ marginBottom: '15px' }}>
                            <p style={{ fontWeight: 'bold', marginBottom: '10px' }}>{qIndex + 1}. {q.question}</p>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                {q.options.map((opt, optIndex) => {
                                    const isSelected = userAnswers[qIndex] === opt;
                                    const isCorrect = opt === q.answer;
                                    
                                    let bgColor = '#f9f9f9';
                                    if (showResults) {
                                        if (isCorrect) bgColor = '#d4edda'; // Verde
                                        else if (isSelected && !isCorrect) bgColor = '#f8d7da'; // Vermelho
                                    } else if (isSelected) {
                                        bgColor = '#e3f2fd'; // Azul claro seleção
                                    }

                                    return (
                                        <div 
                                            key={optIndex}
                                            onClick={() => handleOptionSelect(qIndex, opt)}
                                            style={{
                                                padding: '10px',
                                                border: '1px solid #eee',
                                                borderRadius: '6px',
                                                cursor: showResults ? 'default' : 'pointer',
                                                backgroundColor: bgColor,
                                                transition: 'background 0.3s'
                                            }}
                                        >
                                            {opt}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    ))}

                    {!showResults ? (
                        <button onClick={() => setShowResults(true)} style={{ backgroundColor: '#2ecc71', marginBottom: '10px' }}>
                            Verificar Respostas
                        </button>
                    ) : (
                        <button onClick={() => setQuestions([])} style={{ backgroundColor: '#666' }}>
                            Criar Novo Quiz
                        </button>
                    )}
                </div>
            )}
        </div>
    );
}