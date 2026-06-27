from __future__ import annotations

import re
import tempfile
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

# 偵測解析度預設值；實際值由 settings.ocr_det_side_len 傳入。
DEFAULT_DET_SIDE_LEN = 960


class OcrBackendUnavailableError(RuntimeError):
    """OCR backend is unavailable in the runtime environment."""


@dataclass
class PatientIdOcrResult:
    patient_id: str | None
    full_text: str
    backend: str
    checksum_valid: bool = False
    elapsed_ms: int = 0


# 台灣身分證字號：字首英文字母 + 9 位數字。第二碼性別碼(1/2/8/9)與整體
# 正確性都交給 checksum 把關，所以抽取階段用最寬鬆的 [A-Z][0-9]{9}。
_TW_ID_RE = re.compile(r"[A-Z][0-9]{9}")
# 舊式外來人口統一證號（次要候選，不做 checksum）。
_RESIDENT_RE = re.compile(r"[A-Z]{2}[0-9]{8}")

# 字首字母對應的兩位數值（內政部標準）。
_LETTER_VALUES = {
    "A": 10,
    "B": 11,
    "C": 12,
    "D": 13,
    "E": 14,
    "F": 15,
    "G": 16,
    "H": 17,
    "I": 34,
    "J": 18,
    "K": 19,
    "L": 20,
    "M": 21,
    "N": 22,
    "O": 35,
    "P": 23,
    "Q": 24,
    "R": 25,
    "S": 26,
    "T": 27,
    "U": 28,
    "V": 29,
    "W": 32,
    "X": 30,
    "Y": 31,
    "Z": 33,
}
_WEIGHTS = (1, 9, 8, 7, 6, 5, 4, 3, 2, 1, 1)


def verify_taiwan_id_checksum(pid: str) -> bool:
    """以內政部加權演算法驗證身分證字號的檢查碼。"""
    if not re.fullmatch(r"[A-Z][0-9]{9}", pid or ""):
        return False
    letter_value = _LETTER_VALUES.get(pid[0])
    if letter_value is None:
        return False
    digits = [letter_value // 10, letter_value % 10] + [int(c) for c in pid[1:]]
    total = sum(d * w for d, w in zip(digits, _WEIGHTS, strict=True))
    return total % 10 == 0


def extract_patient_id_candidates(raw_text: str) -> list[str]:
    """逐行抽取身分證候選，避免把跨行數字黏成假號。

    回傳保留出現順序、去重後的候選清單。
    """
    seen: set[str] = set()
    candidates: list[str] = []
    for line in raw_text.splitlines():
        normalized = re.sub(r"[^A-Z0-9]", "", line.upper())
        for match in _TW_ID_RE.finditer(normalized):
            value = match.group(0)
            if value not in seen:
                seen.add(value)
                candidates.append(value)
    return candidates


def _extract_resident_candidate(raw_text: str) -> str | None:
    for line in raw_text.splitlines():
        normalized = re.sub(r"[^A-Z0-9]", "", line.upper())
        match = _RESIDENT_RE.search(normalized)
        if match:
            return match.group(0)
    return None


def select_patient_id(raw_text: str) -> tuple[str | None, bool]:
    """從 OCR 文字選出最可信的身分證字號。

    策略：
    1. 優先回傳第一個 checksum 通過的身分證候選（valid=True）。
    2. 否則回傳第一個格式符合但 checksum 未過的候選（valid=False，供前端警示）。
    3. 否則退回舊式居留證候選（valid=False）。
    4. 都沒有 → (None, False)。
    """
    candidates = extract_patient_id_candidates(raw_text)
    for candidate in candidates:
        if verify_taiwan_id_checksum(candidate):
            return candidate, True
    if candidates:
        return candidates[0], False
    resident = _extract_resident_candidate(raw_text)
    if resident:
        return resident, False
    return None, False


DEFAULT_OCR_VERSION = "PPOCRV6"


@lru_cache
def _get_rapid_ocr(ocr_version: str, det_side_len: int):
    # 統一 rapidocr 套件（ONNX）：以 OCRVersion 選 PP-OCRv4/v5/v6，免裝 paddlepaddle。
    try:
        from rapidocr import OCRVersion, RapidOCR
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise OcrBackendUnavailableError("rapidocr not installed") from exc

    version_map = {
        "PPOCRV4": OCRVersion.PPOCRV4,
        "PPOCRV5": OCRVersion.PPOCRV5,
        # PP-OCRv6 需較新的 rapidocr；舊版缺此 enum 時自動退回 v5，避免 AttributeError。
        "PPOCRV6": getattr(OCRVersion, "PPOCRV6", OCRVersion.PPOCRV5),
    }
    version = version_map.get(ocr_version.upper(), version_map["PPOCRV6"])
    try:
        # limit_side_len 越大越準、越慢；由部署端用環境變數調整。
        # 不同（版本, 解析度）各自快取一個引擎實例。
        return RapidOCR(
            params={
                "Det.ocr_version": version,
                "Rec.ocr_version": version,
                "Det.limit_side_len": det_side_len,
            }
        )
    except Exception as exc:  # pragma: no cover - depends on environment
        raise OcrBackendUnavailableError(f"RapidOCR init failed: {exc}") from exc


def _extract_texts(result) -> list[str]:  # noqa: ANN001 - 第三方回傳型別
    """從 RapidOCR 回傳取出文字行，兼容新版 RapidOCROutput 與舊版 list。"""
    if result is None:
        return []
    texts = getattr(result, "txts", None)
    if texts is not None:
        return [str(t) for t in texts if t]
    # 舊式：list of [box, text, score]
    lines: list[str] = []
    for item in result or []:
        if item and len(item) >= 2 and item[1]:
            lines.append(str(item[1]))
    return lines


def _recognize_text_by_rapidocr(
    image_bytes: bytes, ocr_version: str, det_side_len: int
) -> str:
    ocr = _get_rapid_ocr(ocr_version, det_side_len)
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
        tmp_file.write(image_bytes)
        tmp_path = Path(tmp_file.name)

    try:
        try:
            result = ocr(str(tmp_path))
        except Exception as exc:  # pragma: no cover - depends on environment
            raise OcrBackendUnavailableError(
                f"RapidOCR inference failed: {exc}"
            ) from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    return "\n".join(_extract_texts(result))


def recognize_patient_id_from_image(
    image_bytes: bytes,
    det_side_len: int = DEFAULT_DET_SIDE_LEN,
    ocr_version: str = DEFAULT_OCR_VERSION,
) -> PatientIdOcrResult:
    started = time.perf_counter()
    text = _recognize_text_by_rapidocr(image_bytes, ocr_version, det_side_len)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    patient_id, checksum_valid = select_patient_id(text)
    return PatientIdOcrResult(
        patient_id=patient_id,
        full_text=text,
        backend=f"rapidocr-{ocr_version.lower()}",
        checksum_valid=checksum_valid,
        elapsed_ms=elapsed_ms,
    )
