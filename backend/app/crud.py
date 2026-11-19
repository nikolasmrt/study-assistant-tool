import json
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.orm import Session
from . import models, schemas


def create_subject(db: Session, subject: schemas.SubjectCreate) -> models.Subject:
    """Creates a new subject in the database."""
    existing = db.query(models.Subject).filter(models.Subject.name == subject.name).first()
    if existing:
        return existing
    db_subject = models.Subject(
        name=subject.name,
        description=subject.description,
        category=subject.category or "Geral",
        target_retention=subject.target_retention or 85
    )
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject


def get_subjects(db: Session, skip: int = 0, limit: int = 100) -> list[models.Subject]:
    """Retrieves a list of subjects."""
    return db.query(models.Subject).offset(skip).limit(limit).all()


def delete_subject(db: Session, subject_id: int):
    """Deletes a subject by ID."""
    db_subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if db_subject:
        db.delete(db_subject)
        db.commit()
    return db_subject


def create_session(db: Session, session: schemas.SessionCreate) -> models.StudySession:
    """Creates a new study session entry."""
    db_session = models.StudySession(
        subject_id=session.subject_id,
        duration_minutes=session.duration_minutes,
        notes=session.notes
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def get_sessions_by_subject(db: Session, subject_id: int) -> list[models.StudySession]:
    """Retrieves all sessions for a specific subject."""
    return (
        db.query(models.StudySession)
        .filter(models.StudySession.subject_id == subject_id)
        .order_by(models.StudySession.start_time.desc())
        .all()
    )


def create_flashcard(db: Session, flashcard: schemas.FlashcardCreate) -> models.Flashcard:
    """Creates an SRS flashcard in Box 1 ready for active recall."""
    db_flashcard = models.Flashcard(
        subject_id=flashcard.subject_id,
        front=flashcard.front,
        back=flashcard.back,
        difficulty_tag=flashcard.difficulty_tag or "Médio",
        box_level=1,
        ease_factor=2.5,
        interval_days=0,
        review_count=0,
        next_review_at=datetime.utcnow()
    )
    db.add(db_flashcard)
    db.commit()
    db.refresh(db_flashcard)
    return db_flashcard


def get_flashcards_by_subject(db: Session, subject_id: int) -> list[models.Flashcard]:
    return (
        db.query(models.Flashcard)
        .filter(models.Flashcard.subject_id == subject_id)
        .order_by(models.Flashcard.box_level.asc(), models.Flashcard.id.desc())
        .all()
    )


def delete_flashcard(db: Session, card_id: int):
    card = db.query(models.Flashcard).filter(models.Flashcard.id == card_id).first()
    if card:
        db.delete(card)
        db.commit()
    return card


def review_flashcard(db: Session, card_id: int, rating: str) -> models.Flashcard | None:
    """
    Applies the Spaced Repetition System (Hybrid Leitner + SM-2 algorithm)
    based on student recall confidence: 'again', 'hard', 'good', 'easy'.
    """
    card = db.query(models.Flashcard).filter(models.Flashcard.id == card_id).first()
    if not card:
        return None

    now = datetime.utcnow()
    rating_key = rating.lower().strip()

    box = card.box_level or 1
    ease = card.ease_factor or 2.5

    # Leitner intervals in days per box level
    leitner_intervals = {1: 1, 2: 2, 3: 4, 4: 7, 5: 14}

    if rating_key == "again":
        box = 1
        ease = max(1.3, ease - 0.2)
        interval_days = 0  # Due immediately / today
        card.difficulty_tag = "Difícil"
    elif rating_key == "hard":
        box = max(1, box)
        ease = max(1.3, ease - 0.15)
        interval_days = 1
        card.difficulty_tag = "Difícil"
    elif rating_key == "good":
        box = min(5, box + 1)
        interval_days = leitner_intervals.get(box, 4)
        card.difficulty_tag = "Médio"
    elif rating_key == "easy":
        box = min(5, box + 2)
        ease = min(3.2, ease + 0.15)
        interval_days = int(leitner_intervals.get(box, 7) * 1.4)
        card.difficulty_tag = "Fácil"
    else:
        box = min(5, box + 1)
        interval_days = leitner_intervals.get(box, 2)

    card.box_level = box
    card.ease_factor = round(ease, 2)
    card.interval_days = interval_days
    card.review_count = (card.review_count or 0) + 1
    card.last_reviewed_at = now
    card.next_review_at = now + timedelta(days=interval_days)

    db.commit()
    db.refresh(card)
    return card


def create_feynman_explanation(
    db: Session,
    subject_id: int,
    concept_title: str,
    target_audience: str,
    explanation_text: str,
    evaluation: dict
) -> models.FeynmanExplanation:
    db_item = models.FeynmanExplanation(
        subject_id=subject_id,
        concept_title=concept_title,
        target_audience=target_audience,
        explanation_text=explanation_text,
        clarity_score=evaluation.get("clarity_score", 75),
        strengths_json=json.dumps(evaluation.get("strengths", []), ensure_ascii=False),
        blind_spots_json=json.dumps(evaluation.get("blind_spots", []), ensure_ascii=False),
        socratic_questions_json=json.dumps(evaluation.get("socratic_questions", []), ensure_ascii=False),
        suggested_analogy=evaluation.get("suggested_analogy", "")
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_feynman_by_subject(db: Session, subject_id: int) -> list[dict]:
    rows = (
        db.query(models.FeynmanExplanation)
        .filter(models.FeynmanExplanation.subject_id == subject_id)
        .order_by(models.FeynmanExplanation.created_at.desc())
        .all()
    )
    result = []
    for r in rows:
        score = r.clarity_score or 0
        readability = (
            f"Excelente Didática para {r.target_audience}"
            if score >= 85
            else f"Boa Clareza Conceitual ({r.target_audience})"
            if score >= 70
            else "Em Construção — Simplificar Jargões"
        )
        result.append({
            "id": r.id,
            "subject_id": r.subject_id,
            "concept_title": r.concept_title,
            "target_audience": r.target_audience,
            "explanation_text": r.explanation_text,
            "clarity_score": score,
            "readability_level": readability,
            "strengths": json.loads(r.strengths_json or "[]"),
            "blind_spots": json.loads(r.blind_spots_json or "[]"),
            "socratic_questions": json.loads(r.socratic_questions_json or "[]"),
            "suggested_analogy": r.suggested_analogy or "",
            "created_at": r.created_at
        })
    return result


def create_cornell_note(db: Session, note: schemas.CornellNoteCreate) -> models.CornellNote:
    db_note = models.CornellNote(
        subject_id=note.subject_id,
        title=note.title,
        cues=note.cues,
        notes=note.notes,
        summary=note.summary
    )
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note


def get_cornell_by_subject(db: Session, subject_id: int) -> list[models.CornellNote]:
    return (
        db.query(models.CornellNote)
        .filter(models.CornellNote.subject_id == subject_id)
        .order_by(models.CornellNote.created_at.desc())
        .all()
    )


def delete_cornell_note(db: Session, note_id: int):
    note = db.query(models.CornellNote).filter(models.CornellNote.id == note_id).first()
    if note:
        db.delete(note)
        db.commit()
    return note


def create_quiz_attempt(db: Session, attempt: schemas.QuizAttemptCreate) -> models.QuizAttempt:
    total = max(1, attempt.total_questions)
    score_pct = round((attempt.correct_answers / total) * 100.0, 1)
    db_attempt = models.QuizAttempt(
        subject_id=attempt.subject_id,
        topic_summary=attempt.topic_summary,
        total_questions=attempt.total_questions,
        correct_answers=attempt.correct_answers,
        score_percent=score_pct
    )
    db.add(db_attempt)
    db.commit()
    db.refresh(db_attempt)
    return db_attempt


def get_quiz_attempts_by_subject(db: Session, subject_id: int) -> list[models.QuizAttempt]:
    return (
        db.query(models.QuizAttempt)
        .filter(models.QuizAttempt.subject_id == subject_id)
        .order_by(models.QuizAttempt.created_at.desc())
        .all()
    )


def get_subject_cognitive_stats(db: Session, subject: models.Subject) -> schemas.SubjectCognitiveStats:
    now = datetime.utcnow()
    cards = db.query(models.Flashcard).filter(models.Flashcard.subject_id == subject.id).all()
    feynman_rows = db.query(models.FeynmanExplanation).filter(models.FeynmanExplanation.subject_id == subject.id).all()
    cornell_rows = db.query(models.CornellNote).filter(models.CornellNote.subject_id == subject.id).all()
    quiz_rows = db.query(models.QuizAttempt).filter(models.QuizAttempt.subject_id == subject.id).all()
    session_rows = db.query(models.StudySession).filter(models.StudySession.subject_id == subject.id).all()

    total_cards = len(cards)
    due_cards = sum(1 for c in cards if not c.next_review_at or c.next_review_at <= now)
    mastered_cards = sum(1 for c in cards if (c.box_level or 1) >= 4)

    box_dist = {f"box_{i}": 0 for i in range(1, 6)}
    for c in cards:
        lvl = min(5, max(1, c.box_level or 1))
        box_dist[f"box_{lvl}"] += 1

    # Cognitive Retention Index combines Flashcard Leitner mastery, Feynman score, and Quiz accuracy
    card_retention = (sum((c.box_level or 1) * 20 for c in cards) / total_cards) if total_cards > 0 else 0.0
    avg_feynman = (sum(f.clarity_score for f in feynman_rows) / len(feynman_rows)) if feynman_rows else 0.0
    avg_quiz = (sum(q.score_percent for q in quiz_rows) / len(quiz_rows)) if quiz_rows else 0.0

    signals = [s for s in [card_retention, avg_feynman, avg_quiz] if s > 0]
    retention_index = round(sum(signals) / len(signals), 1) if signals else 0.0

    total_minutes = sum(s.duration_minutes for s in session_rows)

    return schemas.SubjectCognitiveStats(
        subject_id=subject.id,
        subject_name=subject.name,
        category=subject.category or "Geral",
        total_cards=total_cards,
        due_cards=due_cards,
        mastered_cards=mastered_cards,
        retention_index=retention_index,
        box_distribution=box_dist,
        feynman_count=len(feynman_rows),
        avg_feynman_score=round(avg_feynman, 1),
        cornell_count=len(cornell_rows),
        quiz_count=len(quiz_rows),
        avg_quiz_score=round(avg_quiz, 1),
        total_study_minutes=total_minutes
    )


def get_global_analytics(db: Session) -> schemas.GlobalAnalyticsResponse:
    subjects = db.query(models.Subject).all()
    breakdown = [get_subject_cognitive_stats(db, s) for s in subjects]

    total_cards = sum(b.total_cards for b in breakdown)
    due_today = sum(b.due_cards for b in breakdown)
    mastered = sum(b.mastered_cards for b in breakdown)

    global_boxes = {f"box_{i}": 0 for i in range(1, 6)}
    for b in breakdown:
        for k, v in b.box_distribution.items():
            global_boxes[k] = global_boxes.get(k, 0) + v

    total_feynman = sum(b.feynman_count for b in breakdown)
    feynman_scores = [b.avg_feynman_score for b in breakdown if b.feynman_count > 0]
    avg_feynman = round(sum(feynman_scores) / len(feynman_scores), 1) if feynman_scores else 0.0

    total_cornell = sum(b.cornell_count for b in breakdown)
    total_quizzes = sum(b.quiz_count for b in breakdown)
    quiz_scores = [b.avg_quiz_score for b in breakdown if b.quiz_count > 0]
    avg_quiz = round(sum(quiz_scores) / len(quiz_scores), 1) if quiz_scores else 0.0

    retentions = [b.retention_index for b in breakdown if b.retention_index > 0]
    global_retention = round(sum(retentions) / len(retentions), 1) if retentions else 0.0

    total_minutes = sum(b.total_study_minutes for b in breakdown)

    return schemas.GlobalAnalyticsResponse(
        total_subjects=len(subjects),
        total_flashcards=total_cards,
        due_flashcards_today=due_today,
        mastered_flashcards=mastered,
        global_retention_index=global_retention,
        box_distribution=global_boxes,
        total_feynman_evaluations=total_feynman,
        avg_feynman_clarity=avg_feynman,
        total_cornell_notes=total_cornell,
        total_quizzes_taken=total_quizzes,
        avg_quiz_accuracy=avg_quiz,
        total_study_minutes=total_minutes,
        subjects_breakdown=breakdown
    )


def ensure_schema_and_seed(db: Session):
    """
    Safely migrates older SQLite tables if columns are missing and seeds realistic
    Active Recall / SRS / Feynman / Cornell cognitive data when needed.
    """
    migrations = [
        "ALTER TABLE subjects ADD COLUMN category VARCHAR DEFAULT 'Geral'",
        "ALTER TABLE subjects ADD COLUMN target_retention INTEGER DEFAULT 85",
        "ALTER TABLE flashcards ADD COLUMN box_level INTEGER DEFAULT 1",
        "ALTER TABLE flashcards ADD COLUMN ease_factor FLOAT DEFAULT 2.5",
        "ALTER TABLE flashcards ADD COLUMN interval_days INTEGER DEFAULT 0",
        "ALTER TABLE flashcards ADD COLUMN review_count INTEGER DEFAULT 0",
        "ALTER TABLE flashcards ADD COLUMN difficulty_tag VARCHAR DEFAULT 'Médio'",
        "ALTER TABLE flashcards ADD COLUMN last_reviewed_at DATETIME",
        "ALTER TABLE flashcards ADD COLUMN next_review_at DATETIME"
    ]
    for stmt in migrations:
        try:
            db.execute(text(stmt))
            db.commit()
        except Exception:
            db.rollback()

    now = datetime.utcnow()

    # Check if our showcase subjects exist; if not, seed rich cognitive study data
    arq_subject = db.query(models.Subject).filter(models.Subject.name == "Arquitetura de Sistemas & Microsserviços").first()
    if not arq_subject:
        s1 = models.Subject(
            name="Arquitetura de Sistemas & Microsserviços",
            description="Padrões distribuídos, teorema CAP, mensageria assíncrona, cache distribuído e resiliência.",
            category="Engenharia de Software",
            target_retention=90
        )
        s2 = models.Subject(
            name="Estruturas de Dados & Algoritmos Avançados",
            description="Árvores balanceadas, grafos, programação dinâmica, tabelas hash e análise assintótica Big-O.",
            category="Ciência da Computação",
            target_retention=88
        )
        s3 = models.Subject(
            name="Inteligência Artificial & Redes Neurais",
            description="Transformers, mecanismo de Self-Attention, Backpropagation, Embeddings vetoriais e RAG.",
            category="Inteligência Artificial",
            target_retention=85
        )
        db.add_all([s1, s2, s3])
        db.commit()
        db.refresh(s1)
        db.refresh(s2)
        db.refresh(s3)

        # Seed SRS Flashcards across Leitner boxes 1 to 5
        seed_cards = [
            models.Flashcard(
                subject_id=s1.id,
                front="O que afirma o Teorema CAP em sistemas distribuídos?",
                back="Em presença de uma Partição de rede (P), um sistema distribuído deve escolher entre Consistência imediata (C) ou Disponibilidade (A).",
                box_level=4,
                ease_factor=2.65,
                interval_days=7,
                review_count=5,
                difficulty_tag="Fácil",
                last_reviewed_at=now - timedelta(days=2),
                next_review_at=now + timedelta(days=5)
            ),
            models.Flashcard(
                subject_id=s1.id,
                front="Qual a função do padrão Circuit Breaker em microsserviços?",
                back="Interromper chamadas repetidas a um serviço degradado (estado Open), evitando falhas em cascata e permitindo recuperação gradual (Half-Open).",
                box_level=5,
                ease_factor=2.8,
                interval_days=14,
                review_count=7,
                difficulty_tag="Fácil",
                last_reviewed_at=now - timedelta(days=3),
                next_review_at=now + timedelta(days=11)
            ),
            models.Flashcard(
                subject_id=s1.id,
                front="Diferencie Event Sourcing de CQRS.",
                back="Event Sourcing persiste o estado como uma sequência imutável de eventos; CQRS segrega os modelos de escrita (Command) e leitura (Query).",
                box_level=1,
                ease_factor=2.3,
                interval_days=0,
                review_count=2,
                difficulty_tag="Difícil",
                last_reviewed_at=now - timedelta(days=1),
                next_review_at=now - timedelta(hours=2)  # Pendente hoje
            ),
            models.Flashcard(
                subject_id=s1.id,
                front="Quando utilizar o padrão Saga Coreografada vs. Orquestrada?",
                back="Coreografada usa eventos descentralizados para fluxos simples (2-4 serviços); Orquestrada usa um coordenador central para fluxos complexos.",
                box_level=2,
                ease_factor=2.5,
                interval_days=2,
                review_count=3,
                difficulty_tag="Médio",
                last_reviewed_at=now - timedelta(days=2),
                next_review_at=now - timedelta(hours=1)  # Pendente hoje
            ),
            models.Flashcard(
                subject_id=s2.id,
                front="Qual a complexidade temporal média e de pior caso de busca em uma Tabela Hash?",
                back="Média: O(1) com bom fator de carga e função de espalhamento uniforme; Pior caso: O(n) quando todas as chaves colidem no mesmo bucket.",
                box_level=5,
                ease_factor=2.9,
                interval_days=14,
                review_count=6,
                difficulty_tag="Fácil",
                last_reviewed_at=now - timedelta(days=1),
                next_review_at=now + timedelta(days=13)
            ),
            models.Flashcard(
                subject_id=s2.id,
                front="Quais duas propriedades definem um problema resolvível por Programação Dinâmica?",
                back="Subestrutura ótima (solução ótima global contém soluções ótimas dos subproblemas) e Superposição de subproblemas (memoização evita recálculo).",
                box_level=3,
                ease_factor=2.5,
                interval_days=4,
                review_count=4,
                difficulty_tag="Médio",
                last_reviewed_at=now - timedelta(days=4),
                next_review_at=now - timedelta(minutes=30)  # Pendente hoje
            ),
            models.Flashcard(
                subject_id=s3.id,
                front="Qual o papel das matrizes Query (Q), Key (K) e Value (V) no Self-Attention?",
                back="Calculam a relevância contextual entre tokens via softmax(Q·K^T / √d_k)·V, permitindo capturar dependências de longo alcance em paralelo.",
                box_level=4,
                ease_factor=2.6,
                interval_days=7,
                review_count=5,
                difficulty_tag="Médio",
                last_reviewed_at=now - timedelta(days=2),
                next_review_at=now + timedelta(days=5)
            ),
            models.Flashcard(
                subject_id=s3.id,
                front="Como a arquitetura RAG (Retrieval-Augmented Generation) reduz alucinações em LLMs?",
                back="Recupera documentos relevantes via busca vetorial semântica antes da geração, ancorando a resposta do modelo em fatos verificáveis do contexto.",
                box_level=2,
                ease_factor=2.45,
                interval_days=2,
                review_count=2,
                difficulty_tag="Médio",
                last_reviewed_at=now - timedelta(days=2),
                next_review_at=now - timedelta(hours=3)  # Pendente hoje
            ),
        ]
        db.add_all(seed_cards)

        # Seed Feynman Technique Evaluations
        feynman_seeds = [
            models.FeynmanExplanation(
                subject_id=s1.id,
                concept_title="Circuit Breaker em Sistemas Distribuídos",
                target_audience="Iniciante",
                explanation_text=(
                    "O Circuit Breaker funciona exatamente como o disjuntor elétrico da nossa casa. "
                    "Quando um serviço externo começa a demorar ou falhar repetidamente porque está sobrecarregado, "
                    "o disjuntor 'desarma' (estado Aberto) e bloqueia novas chamadas instantaneamente. "
                    "Assim evitamos que todo o sistema trave esperando. Depois de alguns segundos, ele deixa passar "
                    "uma chamada de teste (Meio-Aberto) para ver se o serviço voltou ao normal."
                ),
                clarity_score=94,
                strengths_json=json.dumps([
                    "Analogia perfeita com o disjuntor elétrico residencial, tornando o conceito imediato.",
                    "Explicou claramente a transição entre os estados Fechado, Aberto e Meio-Aberto.",
                    "Conectou a causa (sobrecarga) ao benefício prático (evitar efeito cascata)."
                ], ensure_ascii=False),
                blind_spots_json=json.dumps([
                    "Poderia mencionar o uso de fallback (resposta padrão em cache) enquanto o disjuntor está aberto."
                ], ensure_ascii=False),
                socratic_questions_json=json.dumps([
                    "O que o sistema deve retornar ao usuário final enquanto o Circuit Breaker está no estado Aberto?",
                    "Como definir o limite ideal de falhas (threshold) sem desarmar por oscilações momentâneas de rede?",
                    "Qual a diferença entre usar apenas Timeout e combinar Timeout + Circuit Breaker?"
                ], ensure_ascii=False),
                suggested_analogy="Disjuntor elétrico inteligente que protege os aparelhos da casa contra sobrecarga e testa a rede antes de religar."
            ),
            models.FeynmanExplanation(
                subject_id=s2.id,
                concept_title="Programação Dinâmica e Memoização",
                target_audience="Estudante de Graduação",
                explanation_text=(
                    "Programação Dinâmica resolve problemas complexos quebrando-os em subproblemas menores e salvando "
                    "o resultado em uma tabela de memória (memoização), como se fosse um caderno de rascunho. "
                    "Por exemplo, ao calcular Fibonacci, em vez de recalcular Fib(5) dezenas de vezes na árvore recursiva, "
                    "consultamos o valor já anotado em tempo O(1), reduzindo a complexidade exponencial para linear."
                ),
                clarity_score=91,
                strengths_json=json.dumps([
                    "Excelente contraste entre complexidade exponencial e tempo linear O(n).",
                    "Uso da metáfora do caderno de rascunho para explicar memoização."
                ], ensure_ascii=False),
                blind_spots_json=json.dumps([
                    "Diferencie a abordagem Top-Down (recursão com cache) da Bottom-Up (tabulação iterativa)."
                ], ensure_ascii=False),
                socratic_questions_json=json.dumps([
                    "Quando a abordagem Bottom-Up economiza mais memória de pilha do que a Top-Down?",
                    "Por que algoritmos gulosos não funcionam para todos os problemas de Programação Dinâmica?"
                ], ensure_ascii=False),
                suggested_analogy="Guardar o resultado de uma conta longa no bloco de notas para nunca precisar refazer o mesmo cálculo."
            ),
        ]
        db.add_all(feynman_seeds)

        # Seed Structured Cornell Notes
        cornell_seeds = [
            models.CornellNote(
                subject_id=s1.id,
                title="Teorema CAP, Consistência Eventual e Padrão Saga",
                cues="• Teorema CAP (Brewer)\n• CP vs AP\n• Consistência Eventual\n• Transações Distribuídas (Saga)\n• Idempotência",
                notes=(
                    "1. Teorema CAP: Em sistemas distribuídos sujeitos a Partições de rede (P), é impossível garantir simultaneamente "
                    "Consistência linearizável (C) e Disponibilidade total (A).\n"
                    "2. Bancos CP (ex: ZooKeeper, etcd, HBase) priorizam consistência bloqueando escritas na partição minoritária.\n"
                    "3. Bancos AP (ex: Cassandra, DynamoDB) aceitam escritas locais e sincronizam via Consistência Eventual.\n"
                    "4. Padrão Saga: Substitui o 2PC (Two-Phase Commit) por uma sequência de transações locais com transações compensatórias "
                    "em caso de falha. Exige consumidores idempotentes."
                ),
                summary=(
                    "Em síntese, arquiteturas distribuídas modernas evitam bloqueios globais (2PC) adotando Consistência Eventual "
                    "e o padrão Saga com chaves de idempotência para manter alta disponibilidade e resiliência a partições."
                )
            ),
            models.CornellNote(
                subject_id=s3.id,
                title="Arquitetura Transformer e Mecanismo de Self-Attention",
                cues="• Limitação das RNNs\n• Vetores Q, K, V\n• Produto Escalar Escalado\n• Multi-Head Attention\n• Positional Encoding",
                notes=(
                    "1. Ao contrário de RNNs/LSTMs que processam tokens sequencialmente, o Transformer processa toda a sequência em paralelo.\n"
                    "2. Cada token gera três projeções lineares: Query (o que busco), Key (o que ofereço) e Value (conteúdo semântico).\n"
                    "3. A divisão por raiz de d_k evita que produtos escalares grandes empurrem o Softmax para regiões de gradiente zero.\n"
                    "4. Multi-Head Attention permite focar simultaneamente em relações sintáticas, semânticas e referenciais."
                ),
                summary=(
                    "O Self-Attention revolucionou o NLP ao substituir a recorrência sequencial por matrizes de atenção paralelizáveis "
                    "ponderadas pela similaridade entre Queries e Keys."
                )
            ),
        ]
        db.add_all(cornell_seeds)

        # Seed Quiz Attempts & Study Sessions
        quiz_seeds = [
            models.QuizAttempt(
                subject_id=s1.id,
                topic_summary="Resiliência, Teorema CAP e Mensageria",
                total_questions=5,
                correct_answers=5,
                score_percent=100.0
            ),
            models.QuizAttempt(
                subject_id=s1.id,
                topic_summary="Padrão Saga e Idempotência em Microsserviços",
                total_questions=5,
                correct_answers=4,
                score_percent=80.0
            ),
            models.QuizAttempt(
                subject_id=s2.id,
                topic_summary="Complexidade Assintótica e Tabelas Hash",
                total_questions=5,
                correct_answers=4,
                score_percent=80.0
            ),
            models.QuizAttempt(
                subject_id=s3.id,
                topic_summary="Transformers, Attention e RAG",
                total_questions=5,
                correct_answers=5,
                score_percent=100.0
            ),
        ]
        db.add_all(quiz_seeds)

        session_seeds = [
            models.StudySession(subject_id=s1.id, duration_minutes=45, notes="Revisão SRS Leitner + Laboratório Feynman sobre Circuit Breaker"),
            models.StudySession(subject_id=s2.id, duration_minutes=35, notes="Prática de Programação Dinâmica e Flashcards ativos"),
            models.StudySession(subject_id=s3.id, duration_minutes=40, notes="Síntese Cornell sobre Self-Attention e Quiz IA"),
        ]
        db.add_all(session_seeds)
        db.commit()
