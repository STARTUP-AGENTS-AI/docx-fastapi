from fastapi import FastAPI, HTTPException
import os

app = FastAPI()

@app.post("/save_script/")
async def save_script(code: str):
    temp_file_path = "/tmp/temp_script.py"  # Caminho do arquivo temporário no Railway
    try:
        # Salva o código no arquivo temporário
        with open(temp_file_path, "w") as temp_file:
            temp_file.write(code)
        return {"message": "Script salvo com sucesso!", "file_path": temp_file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar o script: {str(e)}")
