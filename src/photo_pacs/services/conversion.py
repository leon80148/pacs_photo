from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError
from pydicom.dataset import Dataset, FileDataset
from pydicom.uid import UID, SecondaryCaptureImageStorage, generate_uid


@dataclass
class PatientInfo:
    patient_id: str
    patient_name: str | None = None
    birth_date: str | None = None
    sex: str | None = None


@dataclass
class ExamInfo:
    exam_datetime: datetime
    exam_description: str | None = None


@dataclass
class ConversionConfig:
    modality: str
    resize_max: int
    transfer_syntax: str
    charset: str | None
    include_patient_info_except_id: bool
    include_exam_description: bool


class ConversionError(Exception):
    pass


def _load_image(image_path: Path, resize_max: int) -> tuple[bytes, int, int]:
    try:
        with Image.open(image_path) as image:
            image = ImageOps.exif_transpose(image)
            image = image.convert("RGB")
            if resize_max:
                longest = max(image.size)
                if longest > resize_max:
                    ratio = resize_max / longest
                    new_size = (
                        max(1, int(image.width * ratio)),
                        max(1, int(image.height * ratio)),
                    )
                    image = image.resize(new_size, Image.LANCZOS)
            pixel_bytes = image.tobytes()
            rows = image.height
            cols = image.width
    except UnidentifiedImageError as exc:
        raise ConversionError("unsupported_image") from exc
    return pixel_bytes, rows, cols


def image_to_dicom(
    image_path: Path,
    patient: PatientInfo,
    exam: ExamInfo,
    study_uid: str,
    series_uid: str,
    instance_number: int,
    config: ConversionConfig,
) -> FileDataset:
    pixel_bytes, rows, cols = _load_image(image_path, config.resize_max)
    transfer_syntax_uid = UID(config.transfer_syntax)

    file_meta = Dataset()
    file_meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = transfer_syntax_uid
    file_meta.ImplementationClassUID = generate_uid()

    ds = FileDataset(
        image_path.name,
        {},
        file_meta=file_meta,
        preamble=b"\0" * 128,
    )
    ds.is_little_endian = transfer_syntax_uid.is_little_endian
    ds.is_implicit_VR = transfer_syntax_uid.is_implicit_VR

    ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.StudyInstanceUID = study_uid
    ds.SeriesInstanceUID = series_uid

    ds.PatientID = patient.patient_id
    if config.include_patient_info_except_id:
        if patient.patient_name:
            ds.PatientName = patient.patient_name
        if patient.birth_date:
            ds.PatientBirthDate = patient.birth_date.replace("-", "")
        if patient.sex:
            ds.PatientSex = patient.sex

    ds.Modality = config.modality
    ds.SeriesNumber = 1
    ds.InstanceNumber = instance_number
    ds.ConversionType = "WSD"

    ds.StudyDate = exam.exam_datetime.strftime("%Y%m%d")
    ds.StudyTime = exam.exam_datetime.strftime("%H%M%S")
    if config.include_exam_description and exam.exam_description:
        ds.StudyDescription = exam.exam_description
        ds.SeriesDescription = exam.exam_description

    if config.charset:
        ds.SpecificCharacterSet = config.charset

    ds.Rows = rows
    ds.Columns = cols
    ds.SamplesPerPixel = 3
    ds.PhotometricInterpretation = "RGB"
    ds.PlanarConfiguration = 0
    ds.BitsAllocated = 8
    ds.BitsStored = 8
    ds.HighBit = 7
    ds.PixelRepresentation = 0
    ds.PixelData = pixel_bytes

    return ds
