import { useState, useEffect } from 'react';
import api from '../services/api';

interface Flashcard {
    id: number;
    front: string;
    back: string;
}

interface Props {
    subjectId: number;
}

export function FlashcardTool({ subjectId }: Props) {
    const [cards, setCards] = useState<Flashcard[]>([]);
    const [front, setFront] = useState('');
    const [back, setBack] = useState('');
    
    const [isStudying, setIsStudying] = useState(false);
    const [currentCardIndex, setCurrentCardIndex] = useState(0);
    const [showBack, setShowBack] = useState(false);

    const fetchCards = async () => {
        try {
            const response = await api.get(`/subjects/${subjectId}/flashcards`);
            setCards(response.data);
        } catch (error) {
            console.error("Erro ao buscar flashcards", error);
        }
    };

    useEffect(() => {
        fetchCards();
    }, [subjectId]);

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!front || !back) return;
        try {
            await api.post('/flashcards/', { subject_id: subjectId, front, back });
            setFront('');
            setBack('');
            fetchCards();
        } catch (error) {
            alert("Erro ao criar cartão");
        }
    };

    const handleNextCard = () => {
        setShowBack(false);
        setCurrentCardIndex((prev) => (prev + 1) % cards.length);
    };

    if (isStudying && cards.length > 0) {
        const currentCard = cards[currentCardIndex];
        return (
            <div className="card" style={{ textAlign: 'center', minHeight: '300px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <h3>Modo Estudo ({currentCardIndex + 1}/{cards.length})</h3>
                
                <div 
                    onClick={() => setShowBack(!showBack)}
                    style={{ 
                        border: '2px solid #646cff', 
                        padding: '40px', 
                        borderRadius: '12px', 
                        cursor: 'pointer',
                        background: showBack ? '#f0f0ff' : 'white',
                        fontSize: '1.5rem',
                        marginBottom: '20px',
                        userSelect: 'none'
                    }}
                >
                    <p style={{ fontSize: '0.9rem', color: '#888' }}>
                        {showBack ? "RESPOSTA:" : "PERGUNTA:"}
                    </p>
                    {showBack ? currentCard.back : currentCard.front}
                </div>

                <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
                    <button onClick={() => setShowBack(!showBack)}>
                        {showBack ? 'Esconder Resposta' : 'Ver Resposta'}
                    </button>
                    <button onClick={handleNextCard} style={{ backgroundColor: '#2ecc71' }}>
                        Próximo Cartão
                    </button>
                    <button onClick={() => setIsStudying(false)} style={{ backgroundColor: '#666' }}>
                        Parar
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div style={{ marginTop: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
                <h3>📚 Flashcards ({cards.length})</h3>
                {cards.length > 0 && (
                    <button onClick={() => setIsStudying(true)} style={{ width: 'auto' }}>
                        ▶ Praticar Agora
                    </button>
                )}
            </div>

            
            <form onSubmit={handleCreate} style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
                <input 
                    placeholder="Frente (Pergunta)" 
                    value={front} 
                    onChange={e => setFront(e.target.value)} 
                    style={{ flex: 1 }}
                />
                <input 
                    placeholder="Verso (Resposta)" 
                    value={back} 
                    onChange={e => setBack(e.target.value)} 
                    style={{ flex: 1 }}
                />
                <button type="submit" style={{ width: 'auto' }}>+</button>
            </form>

            
            <div className="grid">
                {cards.map(card => (
                    <div key={card.id} style={{ border: '1px solid #ddd', padding: '10px', borderRadius: '8px', fontSize: '0.9rem' }}>
                        <strong>P:</strong> {card.front}<br/>
                        <strong>R:</strong> {card.back}
                    </div>
                ))}
            </div>
        </div>
    );
}