"""健保卡身分證 OCR 辨識率回歸測試（需放入去識別化樣本才會執行）。

把樣本影像放進 tests/fixtures/id_cards/，檔名即預期身分證字號，例如：
    A123456789.jpg
測試會跑真實 RapidOCR、計算整體辨識率，低於門檻即失敗。
無樣本或未安裝 rapidocr 時自動 skip，不影響一般 CI。
"""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "id_cards"
# 調整 OCR 參數時，這個門檻就是「不可退步」的護欄。
MIN_ACCURACY = 0.9

pytestmark = pytest.mark.skipif(
    not FIXTURE_DIR.exists() or not any(FIXTURE_DIR.glob("*.jpg")),
    reason="no de-identified ID card fixtures present",
)


def _cases() -> list[tuple[str, Path]]:
    cases = []
    for path in sorted(FIXTURE_DIR.glob("*.jpg")):
        expected = path.stem.upper()
        cases.append((expected, path))
    return cases


def test_id_card_recognition_accuracy() -> None:
    pytest.importorskip("rapidocr")
    from photo_pacs.services.patient_id_ocr import recognize_patient_id_from_image

    cases = _cases()
    correct = 0
    failures: list[str] = []
    for expected, path in cases:
        result = recognize_patient_id_from_image(path.read_bytes())
        if result.patient_id == expected:
            correct += 1
        else:
            failures.append(f"{path.name}: got {result.patient_id!r}")

    accuracy = correct / len(cases)
    assert accuracy >= MIN_ACCURACY, (
        f"OCR accuracy {accuracy:.2%} < {MIN_ACCURACY:.0%}; misses: {failures}"
    )
