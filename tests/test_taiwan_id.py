"""台灣身分證號 checksum 驗證與多候選抽取（OCR 糾錯核心）。"""

from __future__ import annotations

from photo_pacs.services.patient_id_ocr import (
    extract_patient_id_candidates,
    select_patient_id,
    verify_taiwan_id_checksum,
)


def test_checksum_valid_known_id():
    assert verify_taiwan_id_checksum("A123456789") is True


def test_checksum_rejects_single_digit_error():
    # 最後一碼錯一位 → checksum 應抓出
    assert verify_taiwan_id_checksum("A123456780") is False


def test_checksum_rejects_bad_format():
    assert verify_taiwan_id_checksum("1234567890") is False
    assert verify_taiwan_id_checksum("A12345678") is False
    assert verify_taiwan_id_checksum("") is False


def test_extract_candidates_per_line_avoids_cross_line_false_positive():
    text = "健保卡號 0000123456\n身分證號 A123456789"
    candidates = extract_patient_id_candidates(text)
    assert "A123456789" in candidates


def test_select_prefers_checksum_valid_over_first_seen():
    # 第一個出現的是 OCR 認錯一碼的無效號，第二個才是有效號
    text = "姓名欄雜訊 A123456788\n身分證號 A123456789"
    pid, valid = select_patient_id(text)
    assert pid == "A123456789"
    assert valid is True


def test_select_falls_back_to_invalid_candidate_with_flag():
    text = "身分證號 A123456788"  # 格式對但 checksum 不過
    pid, valid = select_patient_id(text)
    assert pid == "A123456788"
    assert valid is False


def test_select_returns_none_when_no_candidate():
    pid, valid = select_patient_id("沒有任何身分證字號")
    assert pid is None
    assert valid is False
