import json
import os
import re
from typing import List, Dict, Any

try:
    import google.generativeai as genai
except ImportError:
    genai = None

API_KEY = os.environ.get("GEMINI_API_KEY")

if API_KEY and genai is not None:
    genai.configure(api_key=API_KEY)


def _split_clean_sentences(text: str) -> List[str]:
    """Splits study text into meaningful sentences for cognitive extraction."""
    raw = re.split(r'(?<=[.!?])\s+|\n+', text.strip())
    sentences = [s.strip() for s in raw if len(s.strip()) > 25]
    if not sentences and len(text.strip()) >= 20:
        sentences = [text.strip()]
    return sentences


def _extract_key_terms(text: str) -> List[str]:
    """Extracts important multi-letter terms from study text."""
    stopwords = {
        "para", "como", "mais", "pelo", "pela", "seus", "suas", "este", "esta",
        "isso", "esse", "essa", "entre", "sobre", "quando", "onde", "porque",
        "muito", "pode", "podem", "sendo", "foram", "será", "através", "durante",
        "cada", "todo", "toda", "todos", "todas", "outro", "outra", "mesmo",
        "também", "apenas", "então", "assim", "desde", "forma", "parte", "dados"
    }
    words = re.findall(r'\b[A-Za-zÀ-ÿ]{5,}\b', text)
    seen = []
    for w in words:
        lw = w.lower()
        if lw not in stopwords and lw not in [s.lower() for s in seen]:
            seen.append(w)
    return seen[:25]


def _fallback_generate_quiz(text: str, num_questions: int = 5, difficulty: str = "Intermediário") -> List[Dict[str, Any]]:
    """
    Deterministic NLP Quiz Generator fallback when GEMINI_API_KEY is not configured.
    Analyzes the provided study text and constructs contextual active-recall questions.
    """
    sentences = _split_clean_sentences(text)
    key_terms = _extract_key_terms(text)
    if not key_terms:
        key_terms = ["Conceito Principal", "Estrutura Modular", "Processo Cognitivo", "Abstração"]

    distractor_templates = [
        "Elimina completamente a necessidade de validação estrutural ou controle de estado no sistema.",
        "Opera exclusivamente de forma estática sem interação com os demais componentes do domínio.",
        "Substitui todas as camadas de abstração por execução linear sem retroalimentação."
    ]

    questions: List[Dict[str, Any]] = []
    target_count = max(3, min(num_questions or 5, 10))

    for idx in range(target_count):
        sentence = sentences[idx % len(sentences)]
        term = key_terms[idx % len(key_terms)]
        secondary_term = key_terms[(idx + 1) % len(key_terms)]

        if idx % 3 == 0:
            q_text = f"Com base no material estudado sobre '{term}', qual afirmação sintetiza corretamente o conceito apresentado?"
            correct = sentence if len(sentence) <= 180 else sentence[:177] + "..."
            options = [
                correct,
                f"O conceito de {term} restringe-se a cenários isolados sem relação com {secondary_term}.",
                distractor_templates[0],
                distractor_templates[1],
            ]
            explanation = f"O trecho original destaca diretamente que: \"{correct}\", conectando {term} ao contexto central do estudo."
        elif idx % 3 == 1:
            q_text = f"Em uma análise de nível {difficulty.lower()}, qual termo-chave está diretamente associado à seguinte definição: \"{sentence[:140]}...\"?"
            correct = f"{term} — atuando em conjunto com {secondary_term} no contexto apresentado."
            options = [
                f"Isolamento estático independente de {term}.",
                correct,
                f"Redundância cíclica oposta ao princípio de {secondary_term}.",
                distractor_templates[2],
            ]
            explanation = f"O conceito '{term}' é o elemento nuclear descrito na passagem analisada."
        else:
            q_text = f"Qual é a implicação prática ao aplicar os princípios de '{term}' e '{secondary_term}' descritos no texto?"
            correct = f"Permite compreender e estruturar: {sentence[:145]}"
            options = [
                distractor_templates[1],
                distractor_templates[0],
                correct,
                f"Impede a integração entre {term} e qualquer fluxo dinâmico.",
            ]
            explanation = f"A aplicação correta baseia-se na premissa do texto: \"{sentence[:150]}\"."

        questions.append({
            "question": q_text,
            "options": options,
            "answer": correct,
            "explanation": explanation,
            "topic_tag": term.capitalize()
        })

    return questions


def generate_quiz_from_text(text: str, num_questions: int = 5, difficulty: str = "Intermediário") -> List[Dict[str, Any]]:
    """
    Uses Google Gemini (when configured) or deterministic Cognitive NLP engine
    to generate an active-recall quiz with explanations.
    """
    if API_KEY and genai is not None:
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            prompt = f"""
            Atue como um professor especialista em aprendizagem ativa.
            Baseado no texto de estudo abaixo, crie {num_questions} perguntas de múltipla escolha de nível {difficulty}.

            Regras estritas de formatação:
            1. Retorne APENAS um array JSON válido, sem markdown.
            2. Formato exato:
            [
                {{
                    "question": "Texto da pergunta?",
                    "options": ["Opção A", "Opção B", "Opção C", "Opção D"],
                    "answer": "Texto exato da opção correta",
                    "explanation": "Explicação pedagógica concisa do porquê a resposta está correta",
                    "topic_tag": "Conceito-chave"
                }}
            ]

            Texto de estudo:
            "{text}"
            """
            response = model.generate_content(prompt)
            cleaned_text = response.text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            parsed = json.loads(cleaned_text.strip())
            if isinstance(parsed, list) and len(parsed) > 0:
                return parsed
        except Exception as e:
            print(f"Aviso: Fallback cognitivo local acionado para quiz ({e})")

    return _fallback_generate_quiz(text, num_questions=num_questions, difficulty=difficulty)


def evaluate_feynman_explanation(concept_title: str, explanation_text: str, target_audience: str = "Iniciante") -> Dict[str, Any]:
    """
    Evaluates a student's explanation using the Feynman Learning Technique:
    - Measures clarity, analogy usage, causal reasoning, and absence of unexplained jargon.
    """
    if API_KEY and genai is not None:
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            prompt = f"""
            Avalie a explicação do aluno aplicando o Método Feynman de Aprendizagem.
            Conceito: "{concept_title}"
            Público-alvo: "{target_audience}"
            Explicação do aluno: "{explanation_text}"

            Retorne APENAS um objeto JSON válido com as chaves:
            {{
                "clarity_score": 85,
                "readability_level": "Claro e Didático",
                "strengths": ["Ponto forte 1", "Ponto forte 2"],
                "blind_spots": ["Lacuna ou jargão não explicado 1", "Lacuna 2"],
                "socratic_questions": ["Pergunta socrática 1?", "Pergunta socrática 2?", "Pergunta socrática 3?"],
                "suggested_analogy": "Uma analogia prática do mundo real para fixar o conceito."
            }}
            """
            response = model.generate_content(prompt)
            cleaned = response.text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict) and "clarity_score" in parsed:
                return parsed
        except Exception as e:
            print(f"Aviso: Fallback cognitivo local acionado para Método Feynman ({e})")

    # Deterministic Cognitive Feynman Analyzer
    words = explanation_text.strip().split()
    word_count = len(words)
    lower_text = explanation_text.lower()

    has_analogy = any(k in lower_text for k in ["como se fosse", "imagina", "por exemplo", "analogia", "funciona como", "parecido com", "exemplo"])
    has_causal = any(k in lower_text for k in ["porque", "portanto", "assim", "para que", "consequência", "gera", "permite", "quando"])
    has_structure = any(k in lower_text for k in ["primeiro", "depois", "etapa", "resumo", "ou seja", "isto é", "significa"])

    base_score = 52
    if word_count >= 25:
        base_score += 14
    if word_count >= 50:
        base_score += 10
    if has_analogy:
        base_score += 11
    if has_causal:
        base_score += 8
    if has_structure:
        base_score += 5
    clarity_score = min(98, max(35, base_score))

    if clarity_score >= 85:
        readability_level = f"Excelente Didática para {target_audience}"
    elif clarity_score >= 70:
        readability_level = f"Boa Clareza Conceitual ({target_audience})"
    else:
        readability_level = "Em Construção — Precisa Simplificar Jargões"

    strengths = []
    if word_count >= 25:
        strengths.append(f"Boa articulação textual ({word_count} palavras) contextualizando '{concept_title}'.")
    if has_causal:
        strengths.append("Uso eficaz de conectores causais ('porque', 'para que', 'permite') demonstrando entendimento de causa e efeito.")
    if has_analogy:
        strengths.append("Excelente aplicação de exemplos ou analogias concretas, pilar central do Método Feynman.")
    if not strengths:
        strengths.append(f"Iniciativa direta de sintetizar '{concept_title}' com as próprias palavras.")

    blind_spots = []
    if not has_analogy:
        blind_spots.append(f"Faltou incluir uma analogia concreta do cotidiano para tornar '{concept_title}' intuitivo a um {target_audience.lower()}.")
    if not has_causal:
        blind_spots.append("Explique melhor o 'porquê' o mecanismo funciona assim, evitando apenas descrever 'o que' ele é.")
    if word_count < 35:
        blind_spots.append("Explicação muito curta: detalhe um caso de uso prático ou o que aconteceria se esse conceito não existisse.")
    if not blind_spots:
        blind_spots.append(f"Experimente explicitar os limites ou casos de borda onde '{concept_title}' pode falhar.")

    socratic_questions = [
        f"Se você precisasse explicar '{concept_title}' sem usar nenhum termo técnico da área, qual metáfora do dia a dia usaria?",
        f"Qual problema crítico surgiria imediatamente se '{concept_title}' fosse removido ou aplicado incorretamente?",
        f"Como '{concept_title}' se conecta com os conceitos anteriores que você estudou nesta matéria?"
    ]

    suggested_analogy = (
        f"Pense em '{concept_title}' como o maestro de uma orquestra ou um sistema de triagem inteligente: "
        f"em vez de cada elemento agir isoladamente, ele organiza o fluxo para que um {target_audience.lower()} "
        f"compreenda exatamente como a entrada se transforma no resultado esperado."
    )

    return {
        "clarity_score": clarity_score,
        "readability_level": readability_level,
        "strengths": strengths,
        "blind_spots": blind_spots,
        "socratic_questions": socratic_questions,
        "suggested_analogy": suggested_analogy
    }


def extract_flashcards_from_text(text: str, max_cards: int = 5) -> List[Dict[str, str]]:
    """
    Extracts Front/Back Active Recall flashcards from study notes or Cornell sheets.
    """
    sentences = _split_clean_sentences(text)
    key_terms = _extract_key_terms(text)
    cards: List[Dict[str, str]] = []
    limit = max(1, min(max_cards or 5, 10))

    for i, sentence in enumerate(sentences[:limit]):
        term = key_terms[i % len(key_terms)] if key_terms else f"Conceito #{i + 1}"
        if ":" in sentence and len(sentence.split(":", 1)[0]) < 65:
            parts = sentence.split(":", 1)
            front = f"O que significa e como funciona: {parts[0].strip()}?"
            back = parts[1].strip()
        else:
            front = f"Qual é o papel e funcionamento de '{term}' no contexto estudado?"
            back = sentence

        difficulty = "Difícil" if len(back) > 130 else ("Fácil" if len(back) < 70 else "Médio")
        cards.append({
            "front": front,
            "back": back,
            "difficulty_tag": difficulty
        })

    return cards
