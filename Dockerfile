FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# OCR 依賴的系統庫：libgomp1（onnxruntime 的 OpenMP runtime）、
# libgl1/libglib2.0-0/libxcb1（rapidocr 拉進的 opencv 在 import 時需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
      libgomp1 \
      libgl1 \
      libglib2.0-0 \
      libxcb1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml /app/
COPY src /app/src
COPY web /app/web
COPY README.md /app/README.md
COPY .env.example /app/.env.example

RUN pip install --no-cache-dir ".[ocr]"

# 預下載 PP-OCRv6 medium（預設）與 v5 mobile（退回）ONNX 模型到 image，
# 避免生產端首次呼叫才連外網下載。rapidocr 3.9+ 每階段須同時指定 ocr_version 與 model_type。
RUN python -c "from rapidocr import RapidOCR, OCRVersion, ModelType; \
    RapidOCR(params={'Det.ocr_version': OCRVersion.PPOCRV6, 'Det.model_type': ModelType.MEDIUM, 'Rec.ocr_version': OCRVersion.PPOCRV6, 'Rec.model_type': ModelType.MEDIUM}); \
    RapidOCR(params={'Det.ocr_version': OCRVersion.PPOCRV5, 'Det.model_type': ModelType.MOBILE, 'Rec.ocr_version': OCRVersion.PPOCRV5, 'Rec.model_type': ModelType.MOBILE})"

EXPOSE 9470

CMD ["uvicorn", "photo_pacs.main:app", "--host", "0.0.0.0", "--port", "9470"]
