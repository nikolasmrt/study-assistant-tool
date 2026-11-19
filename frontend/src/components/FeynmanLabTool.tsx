import { useState, useEffect } from 'react';
import api from '../services/api';
import { FeynmanEvaluation } from '../types';

interface Props {
    subjectId: number;
    subjectName: string;
    onDataChanged?: () => void;
}

export function FeynmanLabTool({ subjectId, subjectName, onDataChanged }: Props) {
    const [conceptTitle, setConceptTitle] = useState('');
    const [targetAudience, setTargetAudience] = useState('Iniciante / Leigo');
    const [explanationText, setExplanationText] = useState('');
    const [loading, setLoading] = useState(false);
    const [activeEval, setActiveEval] = useState<FeynmanEvaluation | null>(null);
    const [history, setHistory] = useState<FeynmanEvaluation[]>([]);

    const fetchHistory = async () => {
        try {
            const res = await api.get<FeynmanEvaluation[]>(`/subjects/${subjectId}/feynman`);
            setHistory(res.data);
            if (res.data.length > 0 && !activeEval) {
                setActiveEval(res.data[0]);
            }
        } catch (error) {
            console.error('Erro ao buscar histórico Feynman', error);
        }
    };

    useEffect(() => {
        setActiveEval(null);
        fetchHistory();
    }, [subjectId]);

    const handleLoadSample = () => {
        setConceptTitle('Consistência Eventual e Replicação Assíncrona');
        setTargetAudience('Iniciante / Leigo');
        setExplanationText(
            'A Consistência Eventual funciona como atualizar um mural de avisos em várias filiais de uma empresa. ' +
            'Quando você publica uma alteração na matriz, ela é confirmada na hora porque não espera todas as filiais ' +
            'confirmarem ao mesmo tempo. Por exemplo, durante alguns milissegundos uma filial pode ver a versão anterior, ' +
            'mas logo as mensagens chegam e todas ficam sincronizadas, garantindo alta velocidade e disponibilidade.'
        );
    };

    const handleEvaluate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!conceptTitle.trim() || explanationText.trim().length < 20) return;
        setLoading(true);
        try {
            const res = await api.post<FeynmanEvaluation>('/ai/feynman_evaluate', {
                subject_id: subjectId,
                concept_title: conceptTitle,
                target_audience: targetAudience,
                explanation_text: explanationText,
            });
            setActiveEval(res.data);
            setConceptTitle('');
            setExplanationText('');
            await fetchHistory();
            onDataChanged?.();
        } catch (error) {
            console.error('Erro na avaliação Feynman', error);
        } finally {
            setLoading(false);
        }
    };

    const getScoreColor = (score: number) => {
        if (score >= 85) return '#059669';
        if (score >= 70) return '#2563eb';
        return '#d97706';
    };

    return (
        <div className="module-section">
            <div className="module-toolbar">
                <div>
                    <h3>🎙️ Laboratório Método Feynman — “Ensine para Aprender”</h3>
                    <p className="module-subtitle">
                        Explique um conceito de <strong>{subjectName}</strong> com suas próprias palavras e sem se esconder atrás de jargões. A IA diagnostica lacunas e propõe perguntas socráticas.
                    </p>
                </div>
                <button type="button" className="btn-secondary-action" onClick={handleLoadSample}>
                    💡 Preencher Exemplo Didático
                </button>
            </div>

            <div className="feynman-split-layout">
                {/* Coluna Esquerda: Editor Feynman */}
                <form className="feynman-form-card" onSubmit={handleEvaluate}>
                    <h4>1. Estruture sua Explicação Didática</h4>
                    <div className="form-field">
                        <label>Conceito que você está ensinando</label>
                        <input
                            type="text"
                            placeholder="Ex: Teorema CAP, Árvore B+, Self-Attention..."
                            value={conceptTitle}
                            onChange={(e) => setConceptTitle(e.target.value)}
                            required
                        />
                    </div>

                    <div className="form-field">
                        <label>Público-Alvo da Explicação</label>
                        <select
                            className="select-input"
                            value={targetAudience}
                            onChange={(e) => setTargetAudience(e.target.value)}
                        >
                            <option value="Iniciante / Leigo">Iniciante / Criança de 12 anos (Zero Jargão)</option>
                            <option value="Estudante de Graduação">Colega de Graduação (Foco em Causa & Efeito)</option>
                            <option value="Entrevista Técnica Sênior">Entrevista Técnica (Clareza + Trade-offs)</option>
                        </select>
                    </div>

                    <div className="form-field">
                        <label>Sua Explicação (Use analogias, exemplos e conectores como &ldquo;porque&rdquo;, &ldquo;por exemplo&rdquo;)</label>
                        <textarea
                            rows={6}
                            placeholder="Explique o conceito passo a passo como se estivesse ensinando alguém ao vivo..."
                            value={explanationText}
                            onChange={(e) => setExplanationText(e.target.value)}
                            required
                        />
                    </div>

                    <button
                        type="submit"
                        className="btn-primary-action"
                        style={{ width: '100%' }}
                        disabled={loading || !conceptTitle.trim() || explanationText.trim().length < 20}
                    >
                        {loading ? '🔬 Analisando Clareza Cognitiva...' : '🧠 Avaliar Explicação pelo Método Feynman'}
                    </button>
                </form>

                {/* Coluna Direita: Diagnóstico Cognitivo */}
                <div className="feynman-diagnostic-card">
                    {activeEval ? (
                        <>
                            <div className="feynman-score-banner">
                                <div
                                    className="feynman-score-circle"
                                    style={{ borderColor: getScoreColor(activeEval.clarity_score), color: getScoreColor(activeEval.clarity_score) }}
                                >
                                    <strong>{activeEval.clarity_score}%</strong>
                                    <span>Clareza</span>
                                </div>
                                <div className="feynman-score-info">
                                    <span className="badge-pill" style={{ background: '#eef2ff', color: '#4338ca' }}>
                                        Público: {activeEval.target_audience}
                                    </span>
                                    <h4>{activeEval.concept_title}</h4>
                                    <p className="readability-tag">{activeEval.readability_level}</p>
                                </div>
                            </div>

                            <div className="feynman-quote-box">
                                &ldquo;{activeEval.explanation_text}&rdquo;
                            </div>

                            <div className="feynman-feedback-grid">
                                <div className="feedback-block positive">
                                    <h5>✅ Pontos Fortes da Explicação</h5>
                                    <ul>
                                        {activeEval.strengths.map((s, i) => (
                                            <li key={i}>{s}</li>
                                        ))}
                                    </ul>
                                </div>

                                <div className="feedback-block warning">
                                    <h5>🔍 Lacunas & Pontos Cegos (Blind Spots)</h5>
                                    <ul>
                                        {activeEval.blind_spots.map((b, i) => (
                                            <li key={i}>{b}</li>
                                        ))}
                                    </ul>
                                </div>
                            </div>

                            <div className="feedback-block socratic">
                                <h5>🏛️ Perguntas Socráticas para Aprofundar seu Domínio</h5>
                                <ul>
                                    {activeEval.socratic_questions.map((q, i) => (
                                        <li key={i}>{q}</li>
                                    ))}
                                </ul>
                            </div>

                            {activeEval.suggested_analogy && (
                                <div className="analogy-callout">
                                    <strong>💡 Analogia Mental Recomendada:</strong> {activeEval.suggested_analogy}
                                </div>
                            )}
                        </>
                    ) : (
                        <div className="empty-diagnostic">
                            <p>Escreva uma explicação ao lado para receber o diagnóstico completo de clareza, lacunas conceituais e perguntas socráticas.</p>
                        </div>
                    )}
                </div>
            </div>

            {history.length > 0 && (
                <div className="feynman-history-strip">
                    <h4>📚 Portfólio de Conceitos Validados no Método Feynman ({history.length})</h4>
                    <div className="history-pills-row">
                        {history.map((item, idx) => (
                            <button
                                key={item.id || idx}
                                className={`history-concept-pill ${activeEval?.concept_title === item.concept_title ? 'active' : ''}`}
                                onClick={() => setActiveEval(item)}
                            >
                                <span>{item.concept_title}</span>
                                <strong style={{ color: getScoreColor(item.clarity_score) }}>{item.clarity_score}%</strong>
                            </button>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
