"""Rotas de upload e ingestão de arquivos CSV de pedidos."""

import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.services.ingest_service import IngestService

router = APIRouter(tags=["Ingestão e Uploads"])


@router.post("/uploads", summary="Upload e ingestão de arquivo CSV de pedidos")
def upload_orders_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Recebe um arquivo CSV de pedidos, executa a validação, limpeza, cubagem e persistência."""
    if not file.filename.endswith((".csv", ".txt")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato inválido. O arquivo deve ser um CSV (.csv)."
        )

    # Salva em arquivo temporário para processamento com Pandas
    with NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)

    try:
        service = IngestService(db)
        result = service.ingest_orders_csv(tmp_path, scope_regional=True)
        return {"status": "SUCESSO", "detalhes": result}
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


@router.post("/ingest/all", summary="Processar todos os arquivos brutos da pasta data/raw/")
def ingest_all_raw_data(db: Session = Depends(get_db)):
    """Lê todos os arquivos de pedidos e catálogo disponíveis no diretório data/raw/."""
    service = IngestService(db)
    result = service.ingest_all_raw_files()
    return result
