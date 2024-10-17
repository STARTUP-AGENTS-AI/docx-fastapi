from fastapi import FastAPI, HTTPException
import os
import uuid
import json
import subprocess
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from pptx import Presentation  # Importando a biblioteca pptx

app = FastAPI()

# Autenticação do Google Drive e Google Sheets
SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/spreadsheets']
service_account_info = json.loads(os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON'))

# Cria as credenciais a partir do dicionário
credentials = service_account.Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)
sheets_service = build('sheets', 'v4', credentials=credentials)

#-----------------------------------------------------DOCX-------------------------------------------
# Função para upload de um arquivo .docx para o Google Drive
def upload_docx_to_drive(file_path, file_name):
    file_metadata = {
        'name': file_name,
        'mimeType': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    media = MediaFileUpload(file_path, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

    # Logando o upload
    print(f"Fazendo upload do arquivo: {file_path}")

    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    file_id = file.get('id')

    # Tornar o arquivo público
    permission = {
        'type': 'anyone',
        'role': 'reader',
    }
    drive_service.permissions().create(fileId=file_id, body=permission).execute()

    return file_id

# Endpoint para salvar um arquivo .docx com nome dinâmico
@app.post("/save_docx/")
async def save_docx(code: str, file_name: str):
    # Gera um nome de arquivo temporário para o código Python
    temp_file_name = f"{uuid.uuid4()}.py"
    temp_file_path = f"./{temp_file_name}"  # Caminho do arquivo temporário no Railway

    try:
        # Salva o código em uma única linha
        print("Salvando o código em:", temp_file_path)
        with open(temp_file_path, "w") as temp_file:
            temp_file.write(code.replace("\\n", ";"))  # Usa `;` para separar comandos

        # Executa o script
        print("Executando o script...")
        result = subprocess.run(['python3', temp_file_path], capture_output=True, text=True)

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Erro ao executar o script: {result.stderr}")

        # Caminho do arquivo DOCX gerado pelo script
        docx_file_path = f"./{file_name}.docx"  # Nome dinâmico do arquivo .docx

        # Verifica se o arquivo DOCX foi realmente gerado
        if not os.path.exists(docx_file_path):
            raise HTTPException(status_code=404, detail="Arquivo DOCX não encontrado após execução do script.")

        print("Arquivo DOCX encontrado:", docx_file_path)

        # Faz upload do arquivo DOCX para o Google Drive
        file_id = upload_docx_to_drive(docx_file_path, file_name)

        # Construindo o link para o arquivo no Google Drive
        file_link = f"https://drive.google.com/file/d/{file_id}/view"

        return {"message": "Script executado e documento enviado com sucesso!", "file_link": file_link}

    except Exception as e:
        print("Erro encontrado:", str(e))  # Logando o erro
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

    finally:
        # Remove o arquivo temporário do script Python gerado após a execução
        if os.path.exists(temp_file_path):
            print("Removendo arquivo temporário:", temp_file_path)
            os.remove(temp_file_path)
