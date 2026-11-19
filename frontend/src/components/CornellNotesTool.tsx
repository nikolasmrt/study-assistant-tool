import { useState, useEffect } from 'react';
import api from '../services/api';
import { CornellNote } from '../types';

interface Props {
    subjectId: number;
    onDataChanged?: () => void;
}

export function CornellNotesTool({ subjectId, onDataChanged }: Props) {
    const [notesList, setNotesList] = useState<CornellNote[]>([]);
    const [title, setTitle] = useState('');
    const [cues, setCues] = useState('');
    const [notes, setNotes] = useState('');
    const [summary, setSummary] = useState('');
    const [showForm, setShowForm] = useState(false);
    const [convertingId, setConvertingId] = useState<number | null>(null);
    const [conversionBanner, setConversionBanner] = useState<string | null>(null);

    const fetchCornellNotes = async () => {
        try {
            const res = await api.get<CornellNote[]>(`/subjects/${subjectId}/cornell`);
            setNotesList(res.data);
        } catch (error) {
            console.error('Erro ao buscar notas Cornell', error);
        }
    };

    useEffect(() => {
        fetchCornellNotes();
    }, [subjectId]);

    const handleSaveNote = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!title.trim() || !cues.trim() || !notes.trim() || !summary.trim()) return;
        try {
            await api.post('/cornell/', {
                subject_id: subjectId,
                title,
                cues,
                notes,
                summary,
            });
            setTitle('');
            setCues('');
            setNotes('');
            setSummary('');
            setShowForm(false);
            fetchCornellNotes();
            onDataChanged?.();
        } catch (error) {
            console.error('Erro ao salvar ficha Cornell', error);
        }
    };

    const handleConvertToFlashcards = async (noteId: number, noteTitle: string) => {
        setConvertingId(noteId);
        try {
            const res = await api.post(`/cornell/${noteId}/to-flashcards`);
            const createdCount = res.data.length;
            setConversionBanner(`✨ ${createdCount} novos Flashcards SRS criados automaticamente a partir da ficha "${noteTitle}"!`);
            onDataChanged?.();
            setTimeout(() => setConversionBanner(null), 4000);
        } catch (error) {
            console.error('Erro ao converter ficha Cornell em flashcards', error);
        } finally {
            setConvertingId(null);
        }
    };

    const handleDeleteNote = async (noteId: number) => {
        try {
            await api.delete(`/cornell/${noteId}`);
            fetchCornellNotes();
            onDataChanged?.();
        } catch (error) {
            console.error('Erro ao excluir nota Cornell', error);
        }
    };

    return (
        <div className="module-section">
            <div className="module-toolbar">
                <div>
                    <h3>📓 Caderno Estruturado de Cornell (Pistas • Notas • Síntese)</h3>
                    <p className="module-subtitle">
                        Organize suas anotações nas 3 zonas clássicas da Universidade de Cornell e converta fichas diretamente em Flashcards SRS.
                    </p>
                </div>
                <button className="btn-primary-action" onClick={() => setShowForm(!showForm)}>
                    {showForm ? '✕ Fechar Editor Cornell' : '+ Nova Ficha Cornell'}
                </button>
            </div>

            {conversionBanner && <div className="srs-toast-feedback">{conversionBanner}</div>}

            {showForm && (
                <form className="cornell-editor-sheet" onSubmit={handleSaveNote}>
                    <div className="cornell-sheet-header">
                        <input
                            type="text"
                            placeholder="Título da Aula ou Tópico (ex: Indexação B-Tree e Isolamento Transacional)"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            required
                        />
                    </div>
                    <div className="cornell-two-columns">
                        <div className="cornell-cues-col">
                            <label>🔑 Coluna de Pistas & Perguntas-Chave (30%)</label>
                            <textarea
                                rows={6}
                                placeholder="• O que é B-Tree?&#10;• Custo de busca O(log n)&#10;• Write-Ahead Logging (WAL)"
                                value={cues}
                                onChange={(e) => setCues(e.target.value)}
                                required
                            />
                        </div>
                        <div className="cornell-notes-col">
                            <label>📝 Coluna de Anotações Detalhadas (70%)</label>
                            <textarea
                                rows={6}
                                placeholder="1. Árvores B+ mantêm dados apenas nas folhas encadeadas, otimizando range scans sequenciais em disco.&#10;2. O protocolo WAL grava alterações em log sequencial antes de modificar páginas de dados."
                                value={notes}
                                onChange={(e) => setNotes(e.target.value)}
                                required
                            />
                        </div>
                    </div>
                    <div className="cornell-summary-row">
                        <label>🎯 Síntese Final (Resuma a essência da página em 2 linhas com suas próprias palavras)</label>
                        <textarea
                            rows={2}
                            placeholder="Em resumo, índices B+ aliados ao Write-Ahead Logging garantem leituras rápidas em disco sem comprometer a durabilidade ACID."
                            value={summary}
                            onChange={(e) => setSummary(e.target.value)}
                            required
                        />
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '12px' }}>
                        <button type="submit" className="btn-primary-action">
                            💾 Salvar Ficha no Caderno Cornell
                        </button>
                    </div>
                </form>
            )}

            <div className="cornell-sheets-list">
                {notesList.map((sheet) => (
                    <article key={sheet.id} className="cornell-sheet-card">
                        <div className="cornell-card-top">
                            <div>
                                <span className="badge-pill" style={{ background: '#fef3c7', color: '#b45309' }}>
                                    Ficha Método Cornell
                                </span>
                                <h4>{sheet.title}</h4>
                            </div>
                            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                <button
                                    className="btn-secondary-action"
                                    disabled={convertingId === sheet.id}
                                    onClick={() => handleConvertToFlashcards(sheet.id, sheet.title)}
                                >
                                    {convertingId === sheet.id ? 'Gerando...' : '🃏 Converter em Flashcards SRS'}
                                </button>
                                <button
                                    className="btn-icon-delete"
                                    onClick={() => handleDeleteNote(sheet.id)}
                                    title="Excluir Ficha Cornell"
                                >
                                    ✕
                                </button>
                            </div>
                        </div>

                        <div className="cornell-grid-display">
                            <div className="cornell-cues-pane">
                                <h5>🔑 PISTAS & CONCEITOS</h5>
                                <pre>{sheet.cues}</pre>
                            </div>
                            <div className="cornell-notes-pane">
                                <h5>📝 ANOTAÇÕES PRINCIPAIS</h5>
                                <pre>{sheet.notes}</pre>
                            </div>
                        </div>

                        <div className="cornell-summary-pane">
                            <h5>🎯 SÍNTESE CONSOLIDADA</h5>
                            <p>{sheet.summary}</p>
                        </div>
                    </article>
                ))}
            </div>
        </div>
    );
}
