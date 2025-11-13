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
origins = ["*"] # Permitindo todas as origens, visto que é um app de desafio
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
Você é um assistente de IA especialista em **triagem e roteamento** de e-mails para uma empresa financeira.
Sua tarefa é analisar o e-mail e retornar um objeto JSON.

O JSON deve ter ESTRITAMENTE o seguinte formato:
{
  "reasoning": "...",
  "category": "...",
  "suggested_reply": "..."
}

### Campos JSON Explicados
1.  **reasoning**: Uma análise em uma frase do *porquê* o e-mail se encaixa na categoria. (Ex: "O usuário está relatando um erro crítico que impede o uso do sistema.")
2.  **category**: A categoria de triagem. Deve ser UMA das seguintes:
    * `URGENT_SUPPORT`: Problema crítico, erro de sistema, sistema fora do ar, falha de pagamento, usuário impedido de trabalhar. (Ex: "servidor caiu", "erro 504", "não consigo logar").
    * `STANDARD_SUPPORT`: Dúvida sobre funcionalidade, pedido de "como fazer", solicitação de acesso, alteração de dados. (Ex: "como gero o relatório?", "podem me dar acesso à pasta?").
    * `INFO_REQUEST`: Pedido de status, solicitação de atualização, follow-up. (Ex: "qual o status do contrato?", "alguma atualização sobre o chamado 123?").
    * `BILLING_ISSUE`: Dúvida sobre fatura, cobrança indevida, problema de faturamento. (Ex: "cobrança adicional", "fatura errada").
    * `NO_ACTION_NEEDED`: E-mails que não requerem ação. (Ex: agradecimentos, felicitações, avisos de férias, FYI, spam, newsletters).
3.  **suggested_reply**: Uma resposta profissional e **específica** para a categoria.

### Regras de Resposta por Categoria
* **Se `URGENT_SUPPORT`**: "Recebemos seu alerta crítico. Nossa equipe de engenharia já foi notificada e está tratando com prioridade máxima. Entraremos em contato assim que tivermos uma atualização."
* **Se `STANDARD_SUPPORT`**: "Sua solicitação de suporte foi registrada. Um especialista de nossa equipe analisará seu pedido e responderá em breve."
* **Se `INFO_REQUEST`**: "Recebemos sua solicitação de status. Estamos verificando a informação e retornaremos assim que possível."
* **Se `BILLING_ISSUE`**: "Sua dúvida sobre faturamento foi recebida e encaminhada ao nosso time financeiro para análise. Eles entrarão em contato em breve."
* **Se `NO_ACTION_NEDDED`**: "Obrigado por sua mensagem!"

Responda APENAS com o objeto JSON. Não inclua "```json" ou qualquer outro texto.
"""


def clean_email_text(text):
    # Encontra o ponto de corte (o ruído)
    text_lower = text.lower()
    
    # Padrões desnecessários comuns para cortar
    cut_off_patterns = [
        # Marcadores de citação de e-mail
        r'em \d{1,2}/\d{1,2}/\d{4}', # "Em 13/11/2025"
        r'em \d{1,2} de \w+ de \d{4}', # "Em 13 de novembro de 2024"
        r'on \w+, \w+ \d{1,2}, \d{4}', # "On Thu, Nov 13, 2025"
        r'>(.*)\n', # Linhas de citação ( > )
        r'de:',
        r'from:',    
        
        # Assinaturas comuns (PT e EN)
        r'atenciosamente',
        r'obrigado',
        r'grato\(a\)?',
        r'grato',
        r'abs,',
        r'abraços,',
        r'att\.,?',
        r'best regards',
        r'kind regards',
        r'sincerely',
        
        # Disclaimers legais/confidenciais
        r'esta mensagem pode conter',
        r'this email may contain',
        r'aviso legal',
        r'confidencial'
    ]

    # Encontra o *primeiro* ponto de corte no e-mail
    cut_off_index = len(text) # Assume o texto todo por padrão

    for pattern in cut_off_patterns:
        match = re.search(pattern, text_lower)
        if match and match.start() < cut_off_index:
            cut_off_index = match.start()

    # Retorna o texto *original* (com casing) até o ponto de corte.
    cleaned_text = text[:cut_off_index].strip()

    # 3. Fallback: Se o "corte" removeu tudo (ex: um email que só diz "Obrigado"),
    #    é melhor enviar o texto original curto do que nada.
    if not cleaned_text:
        return text.strip() 

    return cleaned_text


@app.post("/classify-email")
async def classify_email(request: EmailRequest):
    
    # --- TESTE TEMPORÁRIO ---
    print("--- 1. EMAIL BRUTO ---")
    print(request.content)
    # ------------------------
    
      # Limpa o conteúdo do e-mail
    email_content = clean_email_text(request.content)
    
    # --- TESTE TEMPORÁRIO ---
    print("--- 2. EMAIL LIMPO (SINAL) ---")
    print(email_content)
    print("---------------------------------")
    # ------------------------

  
    
    if not email_content:
        raise HTTPException(status_code=400, detail="E-mail vazio após limpeza.")
    
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