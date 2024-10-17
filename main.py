from fastapi import FastAPI, HTTPException
import os
import uuid
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

app = FastAPI()

# Autenticação do Google Drive e Google Sheets
SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/spreadsheets']
service_account_info = json.loads(os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON'))

# Cria as credenciais a partir do dicionário
credentials = service_account.Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)
sheets_service = build('sheets', 'v4', credentials=credentials)

# Função para upload de um arquivo .docx para o Google Drive
def upload_docx_to_drive(file_path, file_name):
    file_metadata = {
        'name': file_name,
        'mimeType': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    media = MediaFileUpload(file_path, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    file_id = file.get('id')

    permission = {
        'type': 'anyone',
        'role': 'reader',
    }
    drive_service.permissions().create(fileId=file_id, body=permission).execute()
    
    return file_id

# Função para criar uma planilha no Google Sheets
def create_google_sheet(sheet_name):
    sheet_metadata = {
        'properties': {
            'title': sheet_name
        }
    }
    
    sheet = sheets_service.spreadsheets().create(body=sheet_metadata, fields='spreadsheetId').execute()
    sheet_id = sheet.get('spreadsheetId')

    # Permissões públicas para leitura
    drive_service.permissions().create(
        fileId=sheet_id,
        body={'type': 'anyone', 'role': 'reader'}
    ).execute()

    return sheet_id

# Endpoint para salvar um arquivo .docx
@app.post("/save_docx/")
async def save_docx(code: str):
    """
    Salva o código em um arquivo .docx e faz upload para o Google Drive.
    """
    try:
        # Gera um nome de arquivo aleatório usando UUID
        file_name = f"{uuid.uuid4()}"
        temp_file_path = f"./{file_name}.py"  # Caminho do arquivo temporário

        # Salva o código Python em um arquivo temporário
        with open(temp_file_path, "w") as temp_file:
            temp_file.write(code.replace("\\n", ";"))  # Usa `;` para separar comandos

        # Executa o script Python
        result = subprocess.run(['python3', temp_file_path], capture_output=True, text=True)

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Erro ao executar o script: {result.stderr}")

        # Caminho do arquivo DOCX gerado
        docx_file_path = "./documento_revolucao_francesa.docx"

        if not os.path.exists(docx_file_path):
            raise HTTPException(status_code=404, detail="Arquivo DOCX não encontrado após execução do script.")

        # Faz upload do arquivo DOCX para o Google Drive
        file_id = upload_docx_to_drive(docx_file_path, "documento_revolucao_francesa.docx")
        file_link = f"https://drive.google.com/file/d/{file_id}/view"

        return {"message": "Documento .docx criado e enviado com sucesso!", "file_link": file_link}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")
    
    finally:
        # Remove o arquivo temporário do script Python gerado após a execução
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

# Endpoint para criar uma planilha Google Sheets
@app.post("/create_sheet/")
async def create_sheet(sheet_name: str):
    """
    Cria uma planilha no Google Sheets e retorna o link para acesso.
    """
    try:
        # Cria uma planilha no Google Sheets
        sheet_id = create_google_sheet(sheet_name)
        file_link = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
        
        return {"message": "Planilha Google Sheets criada com sucesso!", "file_link": file_link}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")
