import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def client():
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_root_endpoint(client: TestClient):
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["message"] == "API is running"


def test_create_and_list_subjects(client: TestClient):
    res = client.post(
        "/subjects/",
        json={
            "name": "Compiladores & Linguagens Formais",
            "description": "Análise léxica, sintática, semântica e geração de código intermediário",
            "category": "Ciência da Computação",
            "target_retention": 92
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Compiladores & Linguagens Formais"
    assert data["category"] == "Ciência da Computação"
    assert data["target_retention"] == 92

    list_res = client.get("/subjects/")
    assert list_res.status_code == 200
    names = [s["name"] for s in list_res.json()]
    assert "Compiladores & Linguagens Formais" in names


def test_spaced_repetition_flashcard_lifecycle(client: TestClient):
    sub = client.post(
        "/subjects/",
        json={"name": "Redes de Computadores", "description": "TCP/IP, BGP, DNS e TLS"}
    ).json()

    card_res = client.post(
        "/flashcards/",
        json={
            "subject_id": sub["id"],
            "front": "Como funciona o Three-Way Handshake do TCP?",
            "back": "SYN -> SYN-ACK -> ACK para sincronizar números de sequência antes da transmissão.",
            "difficulty_tag": "Médio"
        }
    )
    assert card_res.status_code == 200
    card = card_res.json()
    assert card["box_level"] == 1
    assert card["review_count"] == 0

    # Review as 'good' -> advances to Box 2
    rev_good = client.post(f"/flashcards/{card['id']}/review", json={"rating": "good"})
    assert rev_good.status_code == 200
    assert rev_good.json()["box_level"] == 2
    assert rev_good.json()["review_count"] == 1

    # Review as 'easy' -> jumps +2 boxes to Box 4
    rev_easy = client.post(f"/flashcards/{card['id']}/review", json={"rating": "easy"})
    assert rev_easy.status_code == 200
    assert rev_easy.json()["box_level"] == 4
    assert rev_easy.json()["ease_factor"] > 2.5

    # Review as 'again' -> resets to Box 1 for immediate reinforcement
    rev_again = client.post(f"/flashcards/{card['id']}/review", json={"rating": "again"})
    assert rev_again.status_code == 200
    assert rev_again.json()["box_level"] == 1
    assert rev_again.json()["interval_days"] == 0


def test_feynman_evaluation_and_history(client: TestClient):
    sub = client.post(
        "/subjects/",
        json={"name": "Sistemas Operacionais", "description": "Paginação, escalonamento e concorrência"}
    ).json()

    feynman_res = client.post(
        "/ai/feynman_evaluate",
        json={
            "subject_id": sub["id"],
            "concept_title": "Memória Virtual e Paginação",
            "target_audience": "Iniciante",
            "explanation_text": (
                "A memória virtual funciona como uma mesa de trabalho inteligente porque divide os programas "
                "em blocos chamados páginas. Por exemplo, apenas as páginas que o processador está usando agora "
                "ficam na memória RAM rápida, enquanto o restante aguarda no disco, permitindo rodar programas "
                "maiores que a própria RAM física."
            )
        }
    )
    assert feynman_res.status_code == 200
    eval_data = feynman_res.json()
    assert eval_data["clarity_score"] >= 75
    assert len(eval_data["strengths"]) >= 1
    assert len(eval_data["socratic_questions"]) >= 2

    history_res = client.get(f"/subjects/{sub['id']}/feynman")
    assert history_res.status_code == 200
    assert len(history_res.json()) == 1
    assert history_res.json()[0]["concept_title"] == "Memória Virtual e Paginação"


def test_cornell_notes_and_flashcard_conversion(client: TestClient):
    sub = client.post(
        "/subjects/",
        json={"name": "Banco de Dados Distribuídos", "description": "ACID, BASE, Sharding e Replicação"}
    ).json()

    cornell_res = client.post(
        "/cornell/",
        json={
            "subject_id": sub["id"],
            "title": "Propriedades ACID vs BASE",
            "cues": "• Atomicidade\n• Isolamento\n• Consistência Eventual",
            "notes": (
                "Atomicidade: garante que toda a transação seja concluída ou revertida integralmente.\n"
                "Isolamento: evita que transações concorrentes leiam estados intermediários inconsistentes."
            ),
            "summary": "Sistemas relacionais priorizam ACID enquanto bancos NoSQL distribuídos adotam BASE para escalar horizontalmente."
        }
    )
    assert cornell_res.status_code == 200
    note = cornell_res.json()

    conv_res = client.post(f"/cornell/{note['id']}/to-flashcards")
    assert conv_res.status_code == 200
    generated_cards = conv_res.json()
    assert len(generated_cards) >= 2


def test_ai_quiz_generation_and_analytics(client: TestClient):
    sub = client.post(
        "/subjects/",
        json={"name": "Engenharia de Confiabilidade (SRE)", "description": "SLI, SLO, SLA e Error Budget"}
    ).json()

    study_text = (
        "Na Engenharia de Confiabilidade de Sites (SRE), um SLI (Service Level Indicator) é uma métrica quantitativa "
        "precisa do comportamento do sistema, como latência do percentil 99 ou taxa de erros HTTP 5xx. "
        "Já o SLO (Service Level Objective) define a meta interna de confiabilidade para esse indicador, "
        "enquanto o Error Budget representa a margem de indisponibilidade aceitável para inovar com segurança."
    )

    quiz_res = client.post(
        "/ai/generate_quiz",
        json={"text": study_text, "num_questions": 4, "difficulty": "Avançado"}
    )
    assert quiz_res.status_code == 200
    questions = quiz_res.json()
    assert len(questions) == 4
    assert "explanation" in questions[0]
    assert "options" in questions[0]

    attempt_res = client.post(
        "/quizzes/attempts",
        json={
            "subject_id": sub["id"],
            "topic_summary": "SLI, SLO e Error Budget em SRE",
            "total_questions": 4,
            "correct_answers": 4
        }
    )
    assert attempt_res.status_code == 200
    assert attempt_res.json()["score_percent"] == 100.0

    overview_res = client.get("/analytics/overview")
    assert overview_res.status_code == 200
    overview = overview_res.json()
    assert overview["total_subjects"] >= 1
    assert overview["total_quizzes_taken"] >= 1
