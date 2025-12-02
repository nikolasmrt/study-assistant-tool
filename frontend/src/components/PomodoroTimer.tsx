import { useState, useEffect } from 'react';
import api from '../services/api';

interface Props {
    subjectId: number;
    onSessionComplete: () => void;
}

export function PomodoroTimer({ subjectId, onSessionComplete }: Props) {
    const POMODORO_TIME = 25 * 60; // 25 minutos em segundos
    const [timeLeft, setTimeLeft] = useState(POMODORO_TIME);
    const [isActive, setIsActive] = useState(false);

    // Lógica do Timer
    useEffect(() => {
        let interval: number | undefined;

        if (isActive && timeLeft > 0) {
            interval = setInterval(() => {
                setTimeLeft((prev) => prev - 1);
            }, 1000);
        } else if (timeLeft === 0) {
            // Tempo acabou! Salvar sessão.
            setIsActive(false);
            saveSession();
            alert("Parabéns! Sessão de estudo concluída.");
            setTimeLeft(POMODORO_TIME);
        }

        return () => clearInterval(interval);
    }, [isActive, timeLeft]);

    const saveSession = async () => {
        try {
            await api.post('/sessions/', {
                subject_id: subjectId,
                duration_minutes: 25,
                notes: "Sessão Pomodoro Automática"
            });
            onSessionComplete(); // Atualiza a lista na tela principal
        } catch (error) {
            console.error("Erro ao salvar sessão", error);
        }
    };

    // Formata segundos para MM:SS
    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    return (
        <div className="pomodoro-card" style={{ padding: '20px', border: '2px solid #646cff', borderRadius: '10px', marginTop: '20px' }}>
            <h3>⏱️ Pomodoro Timer</h3>
            <div style={{ fontSize: '3rem', fontWeight: 'bold', margin: '10px 0' }}>
                {formatTime(timeLeft)}
            </div>
            
            <div style={{ display: 'flex', gap: '10px' }}>
                <button onClick={() => setIsActive(!isActive)} style={{ backgroundColor: isActive ? '#ff4444' : '#4caf50' }}>
                    {isActive ? 'Pausar' : 'Iniciar Foco'}
                </button>
                <button onClick={() => { setIsActive(false); setTimeLeft(POMODORO_TIME); }} style={{ backgroundColor: '#666' }}>
                    Resetar
                </button>
            </div>
        </div>
    );
}