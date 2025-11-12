import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware # CORS
from groq import Groq # Cliente Groq para interagir com a API do Groq
from dotenv import load_dotenv # Carrega variáveis de ambiente do .env
import json # Para manipulação de JSON

# 1. Carrega o .env
load_dotenv()

# 2. Inicializa o cliente do Groq
try:
    groq_client = Groq()
except Exception as e:
    print(f"Erro ao inicializar o cliente Groq: {e}")
    # Você pode querer lidar com isso de forma mais robusta
    # Por enquanto, vamos permitir que o app continue, mas a API falhará.

# Inicializa o app FastAPI
app = FastAPI()

# Configuração do CORS
origins = ["http://127.0.0.1", "http://localhost", "null"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo de Dados (O que esperamos receber do frontend)
class EmailRequest(BaseModel):
    email_text: str

# 3. O "Prompt do Sistema" - A instrução para a IA
SYSTEM_PROMPT = """
Você é um assistente de IA especialista em classificar e-mails para uma empresa.
Sua tarefa é analisar o e-mail fornecido e retornar um objeto JSON.

O JSON deve ter ESTRITAMENTE o seguinte formato:
{
  "category": "...",
  "suggested_reply": "..."
}

As regras de classificação são:
1.  **Produtivo**: E-mails que requerem uma ação ou resposta específica (ex.: solicitações de suporte, atualização sobre casos em aberto, dúvidas sobre o sistema, pedidos de reunião).
2.  **Improdutivo**: Emails que não necessitam de uma ação imediata (ex.: mensagens de felicitações, agradecimentos, newsletters, spam, avisos gerais).

A 'suggested_reply' deve ser uma resposta profissional curta e apropriada para o e-mail.
- Se for 'Produtivo', a resposta deve ser algo como: "Recebemos sua solicitação e já estamos analisando. Entraremos em contato em breve."
- Se for 'Improdutivo', a resposta deve ser algo como: "Obrigado por sua mensagem!" ou "Entendido, obrigado pelo aviso."

Responda APENAS com o objeto JSON. Não inclua "```json" ou qualquer outro texto antes ou depois.
"""


def clean_email_text(text):
    # Remove assinaturas comuns
    text = re.sub(r'--\s*.*', '', text, flags=re.DOTALL) # Remove "--" (assinatura)
    text = re.sub(r'Atenciosamente,.*', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'Obrigado,.*', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Remove texto de resposta anterior
    text = re.sub(r'Em \d{1,2}/\d{1,2}/\d{4},.*escreveu:', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'De:.*', '', text, flags=re.IGNORECASE)
    
    return text.strip() # Remove espaços em branco extras

    if "obrigado" in email_text_lower or \
       "agradeço" in email_text_lower or \
       "recebido" in email_text_lower:
        # Cuidado: "obrigado, mas ainda não funciona" é produtivo.
        # Esta é uma regra simples, mas é um bom começo.
        if len(email_text_lower.split()) < 10: # Se for um e-mail curto
            return {
                "category": "Improdutivo",
                "suggested_reply": "Obrigado por sua mensagem!"
            }

@app.post("/classify-email")
async def classify_email(request: EmailRequest):
    
    email_content = request.email_text

    try:
        # 4. A chamada para a API do Groq
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": email_content
                }
            ],
            model="llama-3.1-8b-instant", 
            temperature=0.2,
            max_tokens=1024,
            response_format={"type": "json_object"}, 
        )

        # 6. Processar a resposta
        raw_response = chat_completion.choices[0].message.content
        
        # O Groq já nos entrega um JSON validado
        json_response = json.loads(raw_response)

        # Retorna o JSON processado direto para o frontend
        return json_response

    except Exception as e:
        # Em caso de erro na API do Groq ou no JSON
        print(f"Erro na chamada da API: {e}")
        raise HTTPException(status_code=500, detail="Erro ao processar o e-mail com a IA.")