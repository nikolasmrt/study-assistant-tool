import { useState, useEffect } from 'react';
import api from '../services/api';
import { Flashcard } from '../types';

interface Props {
    subjectId: number;
    onDataChanged?: () => void;
}

const BOX_LABELS: Record<number, { title: string; interval: string; color: string; bg: string }> = {
    1: { title: 'Caixa 1 • Curto Prazo', interval: 'Revisão Diária', color: '#dc2626', bg: '#fef2f2' },
    2: { title: 'Caixa 2 • Fixação', interval: 'A cada 2 dias', color: '#d97706', bg: '#fffbeb' },
    3: { title: 'Caixa 3 • Consolidação', interval: 'A cada 4 dias', color: '#2563eb', bg: '#eff6ff' },
    4: { title: 'Caixa 4 • Longo Prazo', interval: 'A cada 7 dias', color: '#7c3aed', bg: '#f5f3ff' },
    5: { title: 'Caixa 5 • Domínio Mestre', interval: 'A cada 14+ dias', color: '#059669', bg: '#ecfdf5' },
};

export function FlashcardTool({ subjectId, onDataChanged }: Props) {
    const [cards, setCards] = useState<Flashcard[]>([]);
    const [front, setFront] = useState('');
    const [back, setBack] = useState('');
    const [difficultyTag, setDifficultyTag] = useState('Médio');

    const [autoText, setAutoText] = useState('');
    const [extracting, setExtracting] = useState(false);
    const [showExtractor, setShowExtractor] = useState(false);

    const [filterMode, setFilterMode] = useState<'all' | 'due' | number>('all');
    const [isStudying, setIsStudying] = useState(false);
    const [currentCardIndex, setCurrentCardIndex] = useState(0);
    const [showBack, setShowBack] = useState(false);
    const [reviewFeedback, setReviewFeedback] = useState<string | null>(null);

    const fetchCards = async () => {
        try {
            const response = await api.get<Flashcard[]>(`/subjects/${subjectId}/flashcards`);
            setCards(response.data);
        } catch (error) {
            console.error('Erro ao buscar flashcards', error);
        }
    };

    useEffect(() => {
        fetchCards();
    }, [subjectId]);

    const isCardDue = (card: Flashcard) => {
        if (!card.next_review_at) return true;
        return new Date(card.next_review_at) <= new Date();
    };

    const filteredCards = cards.filter((c) => {
        if (filterMode === 'due') return isCardDue(c);
        if (typeof filterMode === 'number') return (c.box_level || 1) === filterMode;
        return true;
    });

    const dueCount = cards.filter(isCardDue).length;

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!front.trim() || !back.trim()) return;
        try {
            await api.post('/flashcards/', {
                subject_id: subjectId,
                front,
                back,
                difficulty_tag: difficultyTag,
            });
            setFront('');
            setBack('');
            fetchCards();
            onDataChanged?.();
        } catch (error) {
            console.error('Erro ao criar cartão', error);
        }
    };

    const handleAutoExtract = async () => {
        if (autoText.trim().length < 30) return;
        setExtracting(true);
        try {
            await api.post('/ai/extract_flashcards', {
                subject_id: subjectId,
                text: autoText,
                max_cards: 4,
            });
            setAutoText('');
            setShowExtractor(false);
            fetchCards();
            onDataChanged?.();
        } catch (error) {
            console.error('Erro ao extrair flashcards', error);
        } finally {
            setExtracting(false);
        }
    };

    const handleDeleteCard = async (id: number) => {
        try {
            await api.delete(`/flashcards/${id}`);
            fetchCards();
            onDataChanged?.();
        } catch (error) {
            console.error('Erro ao remover flashcard', error);
        }
    };

    const handleRateCard = async (rating: 'again' | 'hard' | 'good' | 'easy') => {
        const activeList = filteredCards.length > 0 ? filteredCards : cards;
        const currentCard = activeList[currentCardIndex % activeList.length];
        if (!currentCard) return;

        try {
            const res = await api.post<Flashcard>(`/flashcards/${currentCard.id}/review`, { rating });
            const updated = res.data;
            const boxInfo = BOX_LABELS[updated.box_level] || BOX_LABELS[1];
            setReviewFeedback(`Cartão movido para ${boxInfo.title} (próxima revisão em ${updated.interval_days}d)`);
            setShowBack(false);

            await fetchCards();
            onDataChanged?.();

            setTimeout(() => setReviewFeedback(null), 2600);
            if (activeList.length > 1) {
                setCurrentCardIndex((prev) => (prev + 1) % activeList.length);
            }
        } catch (error) {
            console.error('Erro ao registrar revisão SRS', error);
        }
    };

    const studyDeck = filteredCards.length > 0 ? filteredCards : cards;

    if (isStudying && studyDeck.length > 0) {
        const safeIndex = currentCardIndex % studyDeck.length;
        const currentCard = studyDeck[safeIndex];
        const boxInfo = BOX_LABELS[currentCard.box_level || 1] || BOX_LABELS[1];

        return (
            <div className="srs-study-arena">
                <div className="srs-arena-header">
                    <div>
                        <span className="badge-pill" style={{ background: boxInfo.bg, color: boxInfo.color }}>
                            {boxInfo.title} • {boxInfo.interval}
                        </span>
                        <span className="srs-counter">
                            Cartão {safeIndex + 1} de {studyDeck.length} • {currentCard.review_count || 0} revisões acumuladas
                        </span>
                    </div>
                    <button className="btn-outline-sm" onClick={() => setIsStudying(false)}>
                        ✕ Encerrar Sessão SRS
                    </button>
                </div>

                {reviewFeedback && <div className="srs-toast-feedback">✨ {reviewFeedback}</div>}

                <div
                    className={`srs-flip-card ${showBack ? 'flipped' : ''}`}
                    onClick={() => setShowBack(!showBack)}
                >
                    <div className="srs-card-role">
                        {showBack ? '💡 RESPOSTA & CONCEITO-CHAVE' : '❓ PERGUNTA DE RECORDAÇÃO ATIVA (CLIQUE PARA VIRAR)'}
                    </div>
                    <div className="srs-card-content">
                        {showBack ? currentCard.back : currentCard.front}
                    </div>
                    <div className="srs-card-meta">
                        <span>Fator de Facilidade SM-2: {currentCard.ease_factor?.toFixed(2) || '2.50'}x</span>
                        <span>Dificuldade: {currentCard.difficulty_tag || 'Médio'}</span>
                    </div>
                </div>

                {!showBack ? (
                    <button className="btn-primary-lg" onClick={() => setShowBack(true)}>
                        👁️ Revelar Resposta e Avaliar Retenção
                    </button>
                ) : (
                    <div className="srs-rating-panel">
                        <p className="srs-rating-prompt">Qual foi seu nível de esforço para recordar esta resposta?</p>
                        <div className="srs-rating-grid">
                            <button className="srs-rate-btn rate-again" onClick={() => handleRateCard('again')}>
                                <strong>1. Errei / Branco</strong>
                                <span>Volta à Caixa 1 (Hoje)</span>
                            </button>
                            <button className="srs-rate-btn rate-hard" onClick={() => handleRateCard('hard')}>
                                <strong>2. Difícil</strong>
                                <span>Mantém Caixa (1 dia)</span>
                            </button>
                            <button className="srs-rate-btn rate-good" onClick={() => handleRateCard('good')}>
                                <strong>3. Bom</strong>
                                <span>Avança +1 Caixa Leitner</span>
                            </button>
                            <button className="srs-rate-btn rate-easy" onClick={() => handleRateCard('easy')}>
                                <strong>4. Fácil / Instantâneo</strong>
                                <span>Salta +2 Caixas Leitner</span>
                            </button>
                        </div>
                    </div>
                )}
            </div>
        );
    }

    return (
        <div className="module-section">
            <div className="module-toolbar">
                <div>
                    <h3>🃏 Repetição Espaçada SRS (Sistema Leitner & SM-2)</h3>
                    <p className="module-subtitle">
                        Cartões evoluem da Caixa 1 (curto prazo) até a Caixa 5 (memória consolidada) conforme sua confiança na resposta.
                    </p>
                </div>
                <div className="toolbar-actions">
                    <button
                        className="btn-secondary-action"
                        onClick={() => setShowExtractor(!showExtractor)}
                    >
                        ✨ {showExtractor ? 'Fechar Extrator IA' : 'Extrair Flashcards de Texto com IA'}
                    </button>
                    {cards.length > 0 && (
                        <button
                            className="btn-primary-action"
                            onClick={() => {
                                setCurrentCardIndex(0);
                                setShowBack(false);
                                setIsStudying(true);
                            }}
                        >
                            ▶ Iniciar Revisão SRS ({filteredCards.length})
                        </button>
                    )}
                </div>
            </div>

            {/* Leitner Box Pipeline Filter */}
            <div className="leitner-pipeline">
                <button
                    className={`leitner-filter-chip ${filterMode === 'all' ? 'active' : ''}`}
                    onClick={() => setFilterMode('all')}
                >
                    <strong>Todos</strong>
                    <span>{cards.length} cartões</span>
                </button>
                <button
                    className={`leitner-filter-chip due-chip ${filterMode === 'due' ? 'active' : ''}`}
                    onClick={() => setFilterMode('due')}
                >
                    <strong>⏰ Pendentes Hoje</strong>
                    <span>{dueCount} para revisar</span>
                </button>
                {[1, 2, 3, 4, 5].map((box) => {
                    const count = cards.filter((c) => (c.box_level || 1) === box).length;
                    const info = BOX_LABELS[box];
                    return (
                        <button
                            key={box}
                            className={`leitner-filter-chip ${filterMode === box ? 'active' : ''}`}
                            onClick={() => setFilterMode(box)}
                            style={{ borderColor: filterMode === box ? info.color : undefined }}
                        >
                            <strong style={{ color: info.color }}>Caixa {box}</strong>
                            <span>{count} • {info.interval}</span>
                        </button>
                    );
                })}
            </div>

            {showExtractor && (
                <div className="ai-extractor-box">
                    <h4>🤖 Gerador Automático de Flashcards SRS a partir de Anotações</h4>
                    <p>Cole um resumo ou trecho teórico e a IA converterá os conceitos centrais em cartões de pergunta e resposta.</p>
                    <textarea
                        rows={4}
                        value={autoText}
                        onChange={(e) => setAutoText(e.target.value)}
                        placeholder="Ex: O protocolo TLS utiliza criptografia assimétrica durante o handshake para negociar chaves de sessão simétricas..."
                    />
                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
                        <button
                            className="btn-primary-action"
                            disabled={extracting || autoText.trim().length < 30}
                            onClick={handleAutoExtract}
                        >
                            {extracting ? 'Extraindo Conceitos...' : '⚡ Gerar 4 Flashcards no Deck'}
                        </button>
                    </div>
                </div>
            )}

            <form onSubmit={handleCreate} className="srs-create-form">
                <input
                    placeholder="Pergunta de Recordação Ativa (Frente)"
                    value={front}
                    onChange={(e) => setFront(e.target.value)}
                    required
                />
                <input
                    placeholder="Resposta Objetiva / Explicação (Verso)"
                    value={back}
                    onChange={(e) => setBack(e.target.value)}
                    required
                />
                <select
                    value={difficultyTag}
                    onChange={(e) => setDifficultyTag(e.target.value)}
                    className="select-input"
                >
                    <option value="Fácil">Fácil</option>
                    <option value="Médio">Médio</option>
                    <option value="Difícil">Difícil</option>
                </select>
                <button type="submit" className="btn-add-card">+ Adicionar</button>
            </form>

            <div className="srs-cards-grid">
                {filteredCards.map((card) => {
                    const boxInfo = BOX_LABELS[card.box_level || 1] || BOX_LABELS[1];
                    const due = isCardDue(card);
                    return (
                        <div key={card.id} className="srs-card-item">
                            <div className="srs-card-item-header">
                                <span className="badge-pill" style={{ background: boxInfo.bg, color: boxInfo.color }}>
                                    {boxInfo.title}
                                </span>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    {due ? (
                                        <span className="due-tag">Revisar Hoje</span>
                                    ) : (
                                        <span className="scheduled-tag">Agendado ({card.interval_days}d)</span>
                                    )}
                                    <button
                                        className="btn-icon-delete"
                                        onClick={() => handleDeleteCard(card.id)}
                                        title="Excluir cartão"
                                    >
                                        ✕
                                    </button>
                                </div>
                            </div>
                            <p className="srs-front-text"><strong>P:</strong> {card.front}</p>
                            <p className="srs-back-text"><strong>R:</strong> {card.back}</p>
                            <div className="srs-card-footer">
                                <span>Facilidade SM-2: <strong>{card.ease_factor?.toFixed(2) || '2.50'}</strong></span>
                                <span>Revisões: <strong>{card.review_count || 0}</strong></span>
                                <span>Nível: <strong>{card.difficulty_tag || 'Médio'}</strong></span>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
