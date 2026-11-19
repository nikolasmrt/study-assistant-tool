import { useEffect, useState } from 'react';
import api from './services/api';
import { Subject, GlobalAnalytics, SubjectCognitiveStats } from './types';
import { FlashcardTool } from './components/FlashcardTool';
import { FeynmanLabTool } from './components/FeynmanLabTool';
import { CornellNotesTool } from './components/CornellNotesTool';
import { AIQuizTool } from './components/AIQuizTool';
import './App.css';

type StudioTab = 'srs' | 'feynman' | 'cornell' | 'quiz';

function App() {
    const [subjects, setSubjects] = useState<Subject[]>([]);
    const [analytics, setAnalytics] = useState<GlobalAnalytics | null>(null);
    const [loading, setLoading] = useState(false);

    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [category, setCategory] = useState('Engenharia de Software');
    const [targetRetention, setTargetRetention] = useState(85);
    const [showNewSubjectForm, setShowNewSubjectForm] = useState(false);

    const [selectedSubject, setSelectedSubject] = useState<Subject | null>(null);
    const [activeTab, setActiveTab] = useState<StudioTab>('srs');

    const fetchDashboardData = async () => {
        try {
            const [subRes, anaRes] = await Promise.all([
                api.get<Subject[]>('/subjects/'),
                api.get<GlobalAnalytics>('/analytics/overview'),
            ]);
            setSubjects(subRes.data);
            setAnalytics(anaRes.data);
        } catch (error) {
            console.error('Erro ao carregar dados cognitivos:', error);
        }
    };

    useEffect(() => {
        fetchDashboardData();
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!name.trim()) return;
        setLoading(true);
        try {
            await api.post('/subjects/', {
                name,
                description,
                category,
                target_retention: targetRetention,
            });
            setName('');
            setDescription('');
            setShowNewSubjectForm(false);
            await fetchDashboardData();
        } catch (error) {
            console.error('Erro ao criar matéria:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id: number, subjectName: string) => {
        if (!window.confirm(`Deseja realmente excluir "${subjectName}" e todo seu acervo cognitivo?`)) return;
        try {
            await api.delete(`/subjects/${id}`);
            if (selectedSubject?.id === id) {
                setSelectedSubject(null);
            }
            fetchDashboardData();
        } catch (error) {
            console.error('Erro ao deletar matéria:', error);
        }
    };

    const openSubjectStudio = (sub: Subject, initialTab: StudioTab = 'srs') => {
        setSelectedSubject(sub);
        setActiveTab(initialTab);
    };

    const getSubjectStats = (subjectId: number): SubjectCognitiveStats | undefined => {
        return analytics?.subjects_breakdown.find((s) => s.subject_id === subjectId);
    };

    const selectedStats = selectedSubject ? getSubjectStats(selectedSubject.id) : undefined;

    const leitnerBoxes = [
        { key: 'box_1', label: 'Caixa 1 • Diário', desc: 'Memória Imediata', color: '#dc2626', bg: '#fef2f2' },
        { key: 'box_2', label: 'Caixa 2 • 2 Dias', desc: 'Fixação Inicial', color: '#d97706', bg: '#fffbeb' },
        { key: 'box_3', label: 'Caixa 3 • 4 Dias', desc: 'Consolidação', color: '#2563eb', bg: '#eff6ff' },
        { key: 'box_4', label: 'Caixa 4 • 7 Dias', desc: 'Longo Prazo', color: '#7c3aed', bg: '#f5f3ff' },
        { key: 'box_5', label: 'Caixa 5 • 14+ Dias', desc: 'Domínio Mestre', color: '#059669', bg: '#ecfdf5' },
    ];

    return (
        <div className="app-shell">
            <header className="top-navbar">
                <div className="navbar-inner">
                    <div className="brand-group" onClick={() => setSelectedSubject(null)} style={{ cursor: 'pointer' }}>
                        <div className="brand-logo">🧠</div>
                        <div>
                            <h1>NeuroStudy AI</h1>
                            <p>Plataforma Full-Stack de Recordação Ativa, Repetição Espaçada SRS, Método Feynman & Cornell</p>
                        </div>
                    </div>

                    <div className="navbar-actions">
                        {selectedSubject ? (
                            <button className="btn-back-nav" onClick={() => setSelectedSubject(null)}>
                                ← Voltar ao Painel Cognitivo
                            </button>
                        ) : (
                            <button
                                className="btn-primary-action"
                                onClick={() => setShowNewSubjectForm(!showNewSubjectForm)}
                            >
                                {showNewSubjectForm ? '✕ Fechar Formulário' : '+ Novo Domínio de Estudo'}
                            </button>
                        )}
                    </div>
                </div>
            </header>

            <main className="main-workspace">
                {selectedSubject ? (
                    <div className="studio-container">
                        <div className="studio-subject-banner">
                            <div>
                                <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '6px' }}>
                                    <span className="category-chip">{selectedSubject.category || 'Geral'}</span>
                                    <span className="retention-chip">
                                        Índice de Retenção: <strong>{selectedStats?.retention_index ?? 85}%</strong> (Meta: {selectedSubject.target_retention || 85}%)
                                    </span>
                                </div>
                                <h2>{selectedSubject.name}</h2>
                                <p>{selectedSubject.description}</p>
                            </div>

                            <div className="studio-mini-kpis">
                                <div className="mini-kpi">
                                    <span>Pendentes SRS</span>
                                    <strong style={{ color: '#dc2626' }}>{selectedStats?.due_cards ?? 0}</strong>
                                </div>
                                <div className="mini-kpi">
                                    <span>Dominados</span>
                                    <strong style={{ color: '#059669' }}>{selectedStats?.mastered_cards ?? 0}</strong>
                                </div>
                                <div className="mini-kpi">
                                    <span>Feynman</span>
                                    <strong style={{ color: '#4f46e5' }}>{selectedStats?.avg_feynman_score || 0}%</strong>
                                </div>
                                <div className="mini-kpi">
                                    <span>Fichas Cornell</span>
                                    <strong style={{ color: '#b45309' }}>{selectedStats?.cornell_count ?? 0}</strong>
                                </div>
                            </div>
                        </div>

                        {/* Navegação dos 4 Laboratórios Cognitivos */}
                        <div className="studio-tabs-bar">
                            <button
                                className={`studio-tab-btn ${activeTab === 'srs' ? 'active' : ''}`}
                                onClick={() => setActiveTab('srs')}
                            >
                                <span>🃏</span>
                                <div>
                                    <strong>Repetição Espaçada SRS</strong>
                                    <small>Leitner Box 1-5 & SM-2 ({selectedStats?.total_cards ?? 0})</small>
                                </div>
                            </button>

                            <button
                                className={`studio-tab-btn ${activeTab === 'feynman' ? 'active' : ''}`}
                                onClick={() => setActiveTab('feynman')}
                            >
                                <span>🎙️</span>
                                <div>
                                    <strong>Laboratório Feynman</strong>
                                    <small>Avaliador de Clareza & Socrático ({selectedStats?.feynman_count ?? 0})</small>
                                </div>
                            </button>

                            <button
                                className={`studio-tab-btn ${activeTab === 'cornell' ? 'active' : ''}`}
                                onClick={() => setActiveTab('cornell')}
                            >
                                <span>📓</span>
                                <div>
                                    <strong>Caderno Cornell</strong>
                                    <small>Pistas, Notas & Síntese ({selectedStats?.cornell_count ?? 0})</small>
                                </div>
                            </button>

                            <button
                                className={`studio-tab-btn ${activeTab === 'quiz' ? 'active' : ''}`}
                                onClick={() => setActiveTab('quiz')}
                            >
                                <span>🧠</span>
                                <div>
                                    <strong>Simulador Quiz IA</strong>
                                    <small>Explicações & Conversão SRS ({selectedStats?.quiz_count ?? 0})</small>
                                </div>
                            </button>
                        </div>

                        <div className="studio-active-panel">
                            {activeTab === 'srs' && (
                                <FlashcardTool subjectId={selectedSubject.id} onDataChanged={fetchDashboardData} />
                            )}
                            {activeTab === 'feynman' && (
                                <FeynmanLabTool
                                    subjectId={selectedSubject.id}
                                    subjectName={selectedSubject.name}
                                    onDataChanged={fetchDashboardData}
                                />
                            )}
                            {activeTab === 'cornell' && (
                                <CornellNotesTool subjectId={selectedSubject.id} onDataChanged={fetchDashboardData} />
                            )}
                            {activeTab === 'quiz' && (
                                <AIQuizTool
                                    subjectId={selectedSubject.id}
                                    subjectName={selectedSubject.name}
                                    onDataChanged={fetchDashboardData}
                                />
                            )}
                        </div>
                    </div>
                ) : (
                    <>
                        {/* Formulário de Criação de Novo Domínio Cognitivo */}
                        {showNewSubjectForm && (
                            <section className="create-domain-panel">
                                <h3>Cadastrar Novo Domínio de Conhecimento</h3>
                                <form onSubmit={handleSubmit} className="domain-form-grid">
                                    <div className="form-field">
                                        <label>Nome da Matéria / Domínio</label>
                                        <input
                                            type="text"
                                            placeholder="Ex: Compiladores & Geração de Código"
                                            value={name}
                                            onChange={(e) => setName(e.target.value)}
                                            required
                                        />
                                    </div>
                                    <div className="form-field">
                                        <label>Área / Categoria</label>
                                        <select
                                            className="select-input"
                                            value={category}
                                            onChange={(e) => setCategory(e.target.value)}
                                        >
                                            <option value="Engenharia de Software">Engenharia de Software</option>
                                            <option value="Ciência da Computação">Ciência da Computação</option>
                                            <option value="Inteligência Artificial">Inteligência Artificial</option>
                                            <option value="Arquitetura & Cloud">Arquitetura & Cloud</option>
                                            <option value="Matemática & Dados">Matemática & Dados</option>
                                        </select>
                                    </div>
                                    <div className="form-field">
                                        <label>Meta de Retenção Cognitiva (%)</label>
                                        <input
                                            type="number"
                                            min={60}
                                            max={100}
                                            value={targetRetention}
                                            onChange={(e) => setTargetRetention(Number(e.target.value))}
                                        />
                                    </div>
                                    <div className="form-field full-span">
                                        <label>Ementa & Conceitos-Chave</label>
                                        <input
                                            type="text"
                                            placeholder="Principais tópicos que serão praticados via SRS, Feynman e Cornell..."
                                            value={description}
                                            onChange={(e) => setDescription(e.target.value)}
                                        />
                                    </div>
                                    <div className="full-span" style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                                        <button type="submit" className="btn-primary-action" disabled={loading}>
                                            {loading ? 'Criando Domínio...' : '✓ Criar Domínio Cognitivo'}
                                        </button>
                                    </div>
                                </form>
                            </section>
                        )}

                        {/* KPIs Executivos de Retenção Cognitiva */}
                        {analytics && (
                            <section className="cognitive-kpi-grid">
                                <div className="cog-kpi-card accent-indigo">
                                    <span className="kpi-eyebrow">ÍNDICE DE RETENÇÃO COGNITIVA</span>
                                    <div className="kpi-value-row">
                                        <strong>{analytics.global_retention_index}%</strong>
                                        <span className="kpi-badge-ok">Memória Ativa</span>
                                    </div>
                                    <p>Média ponderada entre caixas Leitner SRS, clareza Feynman e precisão em simulados.</p>
                                </div>

                                <div className="cog-kpi-card accent-amber">
                                    <span className="kpi-eyebrow">FILA DE REPETIÇÃO ESPAÇADA (SRS)</span>
                                    <div className="kpi-value-row">
                                        <strong>{analytics.due_flashcards_today}</strong>
                                        <span className="kpi-sub-pill">de {analytics.total_flashcards} cartões totais</span>
                                    </div>
                                    <p>{analytics.mastered_flashcards} cartões consolidados nas Caixas 4 e 5 de longo prazo.</p>
                                </div>

                                <div className="cog-kpi-card accent-emerald">
                                    <span className="kpi-eyebrow">CLAREZA MÉDIA MÉTODO FEYNMAN</span>
                                    <div className="kpi-value-row">
                                        <strong>{analytics.avg_feynman_clarity}%</strong>
                                        <span className="kpi-sub-pill">{analytics.total_feynman_evaluations} conceitos explicados</span>
                                    </div>
                                    <p>Avaliação de didática, uso de analogias e ausência de jargões inexplicados.</p>
                                </div>

                                <div className="cog-kpi-card accent-purple">
                                    <span className="kpi-eyebrow">PRECISÃO EM QUIZZES & CORNELL</span>
                                    <div className="kpi-value-row">
                                        <strong>{analytics.avg_quiz_accuracy}%</strong>
                                        <span className="kpi-sub-pill">{analytics.total_cornell_notes} fichas Cornell</span>
                                    </div>
                                    <p>{analytics.total_quizzes_taken} simulados concluídos com conversão direta de erros para SRS.</p>
                                </div>
                            </section>
                        )}

                        {/* Pirâmide / Mapa de Maturidade Leitner SRS (Caixas 1 a 5) */}
                        {analytics && (
                            <section className="leitner-overview-panel">
                                <div className="leitner-panel-header">
                                    <div>
                                        <h3>📦 Mapa de Maturidade da Memória — Algoritmo Leitner & SM-2</h3>
                                        <p>Distribuição real de todos os seus Flashcards entre memória imediata (Caixa 1) e domínio consolidado (Caixa 5).</p>
                                    </div>
                                    <span className="badge-pill" style={{ background: '#ecfdf5', color: '#059669' }}>
                                        {analytics.mastered_flashcards} Cartões em Longo Prazo
                                    </span>
                                </div>

                                <div className="leitner-boxes-showcase">
                                    {leitnerBoxes.map((b) => {
                                        const count = analytics.box_distribution[b.key] || 0;
                                        const pct = analytics.total_flashcards > 0
                                            ? Math.round((count / analytics.total_flashcards) * 100)
                                            : 0;
                                        return (
                                            <div key={b.key} className="leitner-stage-card" style={{ borderTopColor: b.color }}>
                                                <div className="leitner-stage-top">
                                                    <span style={{ color: b.color, fontWeight: 700 }}>{b.label}</span>
                                                    <span className="leitner-pct" style={{ background: b.bg, color: b.color }}>
                                                        {pct}%
                                                    </span>
                                                </div>
                                                <div className="leitner-count">{count} <small>cartões</small></div>
                                                <p className="leitner-desc">{b.desc}</p>
                                                <div className="leitner-bar-track">
                                                    <div
                                                        className="leitner-bar-fill"
                                                        style={{ width: `${Math.max(8, pct)}%`, background: b.color }}
                                                    />
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </section>
                        )}

                        {/* Lista de Domínios & Matérias Cognitivas */}
                        <section className="domains-section">
                            <div className="section-heading-row">
                                <div>
                                    <h2>📚 Domínios de Conhecimento & Estúdios de Estudo Ativo</h2>
                                    <p>Selecione uma matéria ou abra diretamente qualquer ferramenta cognitiva (SRS, Feynman, Cornell ou Quiz IA).</p>
                                </div>
                            </div>

                            <div className="domains-grid">
                                {subjects.map((sub) => {
                                    const st = getSubjectStats(sub.id);
                                    const retention = st?.retention_index ?? 80;
                                    return (
                                        <article key={sub.id} className="domain-card">
                                            <div className="domain-card-top">
                                                <span className="category-chip">{sub.category || 'Geral'}</span>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                    {st && st.due_cards > 0 && (
                                                        <span className="due-alert-badge">
                                                            ⏰ {st.due_cards} revisão SRS hoje
                                                        </span>
                                                    )}
                                                    <button
                                                        className="btn-icon-delete"
                                                        onClick={() => handleDelete(sub.id, sub.name)}
                                                        title="Excluir Matéria"
                                                    >
                                                        🗑️
                                                    </button>
                                                </div>
                                            </div>

                                            <h3>{sub.name}</h3>
                                            <p className="domain-desc">{sub.description || 'Sem descrição cadastrada.'}</p>

                                            <div className="retention-meter-box">
                                                <div className="retention-meter-labels">
                                                    <span>Índice de Retenção Cognitiva</span>
                                                    <strong>{retention}% / Meta {sub.target_retention || 85}%</strong>
                                                </div>
                                                <div className="retention-meter-track">
                                                    <div
                                                        className="retention-meter-fill"
                                                        style={{
                                                            width: `${Math.min(100, retention)}%`,
                                                            background: retention >= 85 ? '#059669' : '#4f46e5',
                                                        }}
                                                    />
                                                </div>
                                            </div>

                                            <div className="domain-metrics-strip">
                                                <div>
                                                    <strong>{st?.total_cards ?? 0}</strong>
                                                    <span>Cartões SRS</span>
                                                </div>
                                                <div>
                                                    <strong>{st?.feynman_count ?? 0}</strong>
                                                    <span>Feynman ({st?.avg_feynman_score ?? 0}%)</span>
                                                </div>
                                                <div>
                                                    <strong>{st?.cornell_count ?? 0}</strong>
                                                    <span>Fichas Cornell</span>
                                                </div>
                                                <div>
                                                    <strong>{st?.avg_quiz_score ?? 0}%</strong>
                                                    <span>Média Quiz</span>
                                                </div>
                                            </div>

                                            <div className="domain-quick-launchers">
                                                <button
                                                    className="btn-launch-primary"
                                                    onClick={() => openSubjectStudio(sub, 'srs')}
                                                >
                                                    🃏 Revisar SRS
                                                </button>
                                                <button
                                                    className="btn-launch-secondary"
                                                    onClick={() => openSubjectStudio(sub, 'feynman')}
                                                >
                                                    🎙️ Feynman
                                                </button>
                                                <button
                                                    className="btn-launch-secondary"
                                                    onClick={() => openSubjectStudio(sub, 'cornell')}
                                                >
                                                    📓 Cornell
                                                </button>
                                                <button
                                                    className="btn-launch-secondary"
                                                    onClick={() => openSubjectStudio(sub, 'quiz')}
                                                >
                                                    🧠 Quiz IA
                                                </button>
                                            </div>
                                        </article>
                                    );
                                })}
                            </div>
                        </section>
                    </>
                )}
            </main>
        </div>
    );
}

export default App;
