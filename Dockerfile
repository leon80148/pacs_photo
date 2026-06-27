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

# 預下載 PP-OCRv6（主）與 v5（fallback）ONNX 模型到 image，
# 避免生產端首次呼叫才連外網下載。若 v6 尚不可用，改成只預載 PPOCRV5。
RUN python -c "from rapidocr import RapidOCR, OCRVersion; \
    RapidOCR(params={'Det.ocr_version': OCRVersion.PPOCRV6, 'Rec.ocr_version': OCRVersion.PPOCRV6}); \
    RapidOCR(params={'Det.ocr_version': OCRVersion.PPOCRV5, 'Rec.ocr_version': OCRVersion.PPOCRV5})"

EXPOSE 9470

CMD ["uvicorn", "photo_pacs.main:app", "--host", "0.0.0.0", "--port", "9470"]
