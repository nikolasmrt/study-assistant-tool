import google.generativeai as genai
import json
import os

API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    print("ERRO CRÍTICO: API Key do Gemini não encontrada!")
else:
    genai.configure(api_key=API_KEY)



def generate_quiz_from_text(text: str):
    """
    Usa o Google Gemini para criar um quiz baseado no texto fornecido.
    """
    model = genai.GenerativeModel('gemini-2.5-pro')
    
    
    prompt = f"""
    Atue como um professor especialista. Baseado no texto de estudo abaixo, 
    crie 15 perguntas de múltipla escolha desafiadoras.
    
    Regras estritas de formatação:
    1. Retorne APENAS um array JSON válido.
    2. Não use Markdown (```json).
    3. O formato deve ser exatamente:
    [
        {{
            "question": "Texto da pergunta?",
            "options": ["Opção A", "Opção B", "Opção C", "Opção D"],
            "answer": "Texto exato da opção correta"
        }}
    ]

    Texto de estudo:
    "{text}"
    """

    try:
        response = model.generate_content(prompt)
        cleaned_text = response.text.strip()
        
        
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
            
        return json.loads(cleaned_text)
    except Exception as e:
        print(f"Erro na IA: {e}")
        return []