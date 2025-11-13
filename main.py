import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware # CORS
from groq import Groq # Cliente Groq para interagir com a API do Groq
from dotenv import load_dotenv # Carrega variáveis de ambiente do .env
import json # Para manipulação de JSON
import re # Importe o 're' para o clean_email_text
import base64 # Para decodificar PDF
import io # Para ler PDF
import pdfplumber # Para ler PDF

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Carrega o .env
load_dotenv()

# Inicializa o cliente do Groq
try:
    groq_client = Groq()
except Exception as e:
    print(f"Erro ao inicializar o cliente Groq: {e}")
    groq_client = None # Define como None para podermos checar depois

# Inicializa o FastAPI
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

# Modelo de Dados
class EmailRequest(BaseModel):
    filename: str
    fileType: str
    content: str

# Modelo para o novo endpoint de PDF
class PdfRequest(BaseModel):
    content_base64: str
    filename: str
    
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
    text_lower = text.lower()
    # Remove assinaturas, etc.
    text_lower = re.sub(r'atenciosamente,.*', '', text_lower, flags=re.DOTALL | re.IGNORECASE)
    text_lower = re.sub(r'obrigado,.*', '', text_lower, flags=re.DOTALL | re.IGNORECASE)
    return text_lower.strip()


@app.post("/classify-email")
async def classify_email(request: EmailRequest):
    
    email_content = request.content
    
    if not groq_client:
        raise HTTPException(status_code=500, detail="Cliente Groq não inicializado. Verifique a API Key.")
    
    try:
        # chamada para a API do Groq
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

        # Processa a resposta
        raw_response = chat_completion.choices[0].message.content
        
        # O Groq entrega o JSON
        json_response = json.loads(raw_response)

        # Retorna o JSON processado direto para o frontend
        return json_response

    except Exception as e:
        # Em caso de erro na API do Groq ou no JSON
        print(f"Erro na chamada da API: {e}")
        raise HTTPException(status_code=500, detail="Erro ao processar o e-mail com a IA.")
    
    
    
@app.post("/extract-text-from-pdf")
async def extract_text_from_pdf(request: PdfRequest):
    try:
        decoded_data = base64.b64decode(request.content_base64)
        pdf_file = io.BytesIO(decoded_data)
        text_content = ""
        
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content += page_text + "\n"
        
        return {"text_content": text_content.strip()}
    except Exception as e:
        print(f"Erro ao processar PDF {request.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao ler o arquivo PDF: {e}")
    
# Carrega os arquivos da pasta "assets"
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# Retorna o seu arquivo index.html
@app.get("/")
async def read_index():
    return FileResponse("index.html")