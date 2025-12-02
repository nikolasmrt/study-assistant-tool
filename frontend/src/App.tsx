import { useEffect, useState } from 'react';
import api from './services/api';
import { Subject } from './types';
import { AIQuizTool } from './components/AIQuizTool';
import { PomodoroTimer } from './components/PomodoroTimer';
import { FlashcardTool } from './components/FlashcardTool';
import './App.css';

function App() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [selectedSubject, setSelectedSubject] = useState<Subject | null>(null);
  const [activeTab, setActiveTab] = useState<'timer' | 'flashcards' | 'ai'>('timer');

  const fetchSubjects = async () => {
    try {
      const response = await api.get<Subject[]>('/subjects/');
      setSubjects(response.data);
    } catch (error) {
      console.error("Erro ao buscar matérias:", error);
    }
  };

  useEffect(() => {
    fetchSubjects();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name) return;
    setLoading(true);
    try {
      await api.post('/subjects/', { name, description });
      setName('');
      setDescription('');
      fetchSubjects();
    } catch (error) {
      console.error("Erro ao criar matéria:", error);
      alert("Erro ao criar matéria.");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number, subjectName: string) => {
    if (!window.confirm(`Tem certeza que deseja excluir "${subjectName}"?`)) return;

    try {
      await api.delete(`/subjects/${id}`);
      if (selectedSubject?.id === id) {
        setSelectedSubject(null);
      }
      fetchSubjects(); 
    } catch (error) {
      console.error("Erro ao deletar:", error);
      alert("Erro ao deletar matéria.");
    }
  };

  return (
    <div className="container">
      <header>
        <h1>🎓 Study Assistant</h1>
        {selectedSubject ? (
          <button 
            onClick={() => { setSelectedSubject(null); setActiveTab('timer'); }}
            style={{ background: '#666', marginTop: '10px', width: 'auto', padding: '10px 20px' }}
          >
            ← Voltar para Lista
          </button>
        ) : (
          <p>Gerenciador de Estudos Full Stack</p>
        )}
      </header>

      <main>
        <div className="content-wrapper">
          {selectedSubject ? (
            <div className="study-mode-container">
              <h2 style={{ textAlign: 'center', color: '#646cff' }}>Estudando: {selectedSubject.name}</h2>
              <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', marginBottom: '20px' }}>
                <button onClick={() => setActiveTab('timer')} style={{ background: activeTab === 'timer' ? '#646cff' : '#ccc', color: activeTab === 'timer' ? 'white' : '#333', width: 'auto' }}>⏱️ Timer</button>
                <button onClick={() => setActiveTab('flashcards')} style={{ background: activeTab === 'flashcards' ? '#646cff' : '#ccc', color: activeTab === 'flashcards' ? 'white' : '#333', width: 'auto' }}>🃏 Flashcards</button>
                <button onClick={() => setActiveTab('ai')}style={{background: activeTab === 'ai' ? '#646cff' : '#ccc',color: activeTab === 'ai' ? 'white' : '#333',width: 'auto'}}>🧠 AI Quiz</button>
              </div>
              <div className="tab-content">
                {activeTab === 'timer' ? (
                  <PomodoroTimer subjectId={selectedSubject.id} onSessionComplete={() => console.log("Sessão registrada!")} />) : activeTab === 'flashcards' ? (<FlashcardTool subjectId={selectedSubject.id} />) : (<AIQuizTool />)}
              </div>
            </div>
          ) : (
            <>
              <section className="card">
                <h2>Nova Matéria</h2>
                <form onSubmit={handleSubmit}>
                  <div className="form-group">
                    <input type="text" placeholder="Nome da Matéria" value={name} onChange={(e) => setName(e.target.value)} required />
                  </div>
                  <div className="form-group">
                    <input type="text" placeholder="Descrição (opcional)" value={description} onChange={(e) => setDescription(e.target.value)} />
                  </div>
                  <button type="submit" disabled={loading}>{loading ? 'Salvando...' : 'Adicionar Matéria'}</button>
                </form>
              </section>

              <section className="list-section">
                <h2>Minhas Matérias</h2>
                {subjects.length === 0 ? (
                  <p className="empty-state">Nenhuma matéria cadastrada.</p>
                ) : (
                  <div className="grid">
                    {subjects.map((sub) => (
                      <div key={sub.id} className="subject-card" style={{ position: 'relative' }}>
                        
                        <button 
                          onClick={(e) => {
                            e.stopPropagation(); 
                            handleDelete(sub.id, sub.name);
                          }}
                          style={{
                            position: 'absolute',
                            top: '10px',
                            right: '10px',
                            background: '#ff4444',
                            width: '30px',
                            height: '30px',
                            borderRadius: '50%',
                            padding: '0',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '0.8rem',
                            border: 'none',
                            cursor: 'pointer'
                          }}
                          title="Excluir Matéria"
                        >
                          🗑️
                        </button>

                        <h3>{sub.name}</h3>
                        <p>{sub.description || "Sem descrição"}</p>
                        <button className="btn-study" onClick={() => setSelectedSubject(sub)} style={{ marginTop: '15px', backgroundColor: '#2ecc71' }}>
                          🚀 Começar a Estudar
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            </>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;