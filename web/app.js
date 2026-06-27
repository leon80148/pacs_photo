const tabs = document.querySelectorAll(".tab");
const panels = document.querySelectorAll(".tab-panel");
const statusPill = document.getElementById("statusPill");

const patientIdInput = document.getElementById("patientId");
const patientNameInput = document.getElementById("patientName");
const birthDateInput = document.getElementById("birthDate");
const sexInput = document.getElementById("sex");

const examModeInput = document.getElementById("examMode");
const examDateTimeInput = document.getElementById("examDateTime");
const examDescriptionInput = document.getElementById("examDescription");

const captureBtn = document.getElementById("captureBtn");
const albumBtn = document.getElementById("albumBtn");
const cameraInput = document.getElementById("cameraInput");
const albumInput = document.getElementById("albumInput");
const imageList = document.getElementById("imageList");
const imageCount = document.getElementById("imageCount");

const submitBtn = document.getElementById("submitBtn");
const progressText = document.getElementById("progressText");

const pacsCalledAet = document.getElementById("pacsCalledAet");
const pacsHost = document.getElementById("pacsHost");
const pacsPort = document.getElementById("pacsPort");
const echoBtn = document.getElementById("echoBtn");
const echoResult = document.getElementById("echoResult");

const dicomwebBaseUrl = document.getElementById("dicomwebBaseUrl");
const dicomwebVerifyTls = document.getElementById("dicomwebVerifyTls");
const dicomwebTimeout = document.getElementById("dicomwebTimeout");
const dicomwebEchoBtn = document.getElementById("dicomwebEchoBtn");
const dicomwebEchoResult = document.getElementById("dicomwebEchoResult");

const localCallingAet = document.getElementById("localCallingAet");
const localModality = document.getElementById("localModality");
const localResizeMax = document.getElementById("localResizeMax");
const localTransferSyntax = document.getElementById("localTransferSyntax");
const localCharset = document.getElementById("localCharset");

const flagPatientInfo = document.getElementById("flagPatientInfo");
const flagExamDescription = document.getElementById("flagExamDescription");
const flagThemeDark = document.getElementById("flagThemeDark");

const saveSettingsBtn = document.getElementById("saveSettingsBtn");
const settingsStatus = document.getElementById("settingsStatus");

const ocrCardBtn = document.getElementById("ocrCardBtn");
const ocrCardInput = document.getElementById("ocrCardInput");
const ocrStatus = document.getElementById("ocrStatus");

const scannerRoiHeight = document.getElementById("scannerRoiHeight");
const scannerRoiWidth = document.getElementById("scannerRoiWidth");
const scannerInterval = document.getElementById("scannerInterval");

const toastContainer = document.getElementById("toastContainer");

const state = {
  images: [],
};

const errorMessages = {
  VALIDATION_ERROR: "欄位未填完整或格式錯誤。",
  PATIENT_ID_NOT_FOUND: "AI 找不到身分字號，請重拍或手動輸入。",
  OCR_UNAVAILABLE: "AI 辨識服務目前不可用。",
  PACS_TIMEOUT: "PACS 連線逾時，請稍後再試。",
  PACS_REJECTED: "PACS 拒絕連線或傳輸失敗。",
  INTERNAL_ERROR: "系統發生錯誤，請稍後再試。",
};

function setStatus(text, type = "idle") {
  statusPill.textContent = text;
  if (type === "ok") {
    statusPill.style.color = "var(--accent-2)";
    statusPill.style.background = "rgba(14, 165, 168, 0.12)";
  } else if (type === "error") {
    statusPill.style.color = "#ef4444";
    statusPill.style.background = "rgba(239, 68, 68, 0.12)";
  } else {
    statusPill.style.color = "var(--accent-2)";
    statusPill.style.background = "rgba(14, 165, 168, 0.12)";
  }
}

function showToast(message, variant = "info", timeoutMs = 3200) {
  if (!toastContainer) return;
  const toast = document.createElement("div");
  toast.className = `toast toast-${variant}`;
  toast.setAttribute("role", variant === "error" ? "alert" : "status");
  toast.setAttribute("aria-live", variant === "error" ? "assertive" : "polite");
  toast.textContent = message;
  toastContainer.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add("toast-visible"));
  const dismiss = () => {
    toast.classList.remove("toast-visible");
    toast.addEventListener("transitionend", () => toast.remove(), { once: true });
  };
  setTimeout(dismiss, timeoutMs);
  toast.addEventListener("click", dismiss);
}

function switchTab(target) {
  tabs.forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.tab === target);
  });
  panels.forEach((panel) => {
    panel.classList.toggle("active", panel.id === target);
  });
}

tabs.forEach((tab) => {
  tab.addEventListener("click", () => switchTab(tab.dataset.tab));
});

function updateExamMode() {
  const mode = examModeInput.value;
  examDateTimeInput.disabled = mode === "auto";
}

function toLocalDateTimeValue(date) {
  const offset = date.getTimezoneOffset();
  const local = new Date(date.getTime() - offset * 60000);
  return local.toISOString().slice(0, 16);
}

examModeInput.addEventListener("change", updateExamMode);
examDateTimeInput.value = toLocalDateTimeValue(new Date());
updateExamMode();

function refreshImageList() {
  imageList.innerHTML = "";
  imageCount.textContent = `已選 ${state.images.length} 張`;
  state.images.forEach((item, index) => {
    const wrapper = document.createElement("div");
    wrapper.className = "thumb";
    const img = document.createElement("img");
    img.src = item.url;
    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.textContent = "刪除";
    removeBtn.addEventListener("click", () => removeImage(index));
    wrapper.appendChild(img);
    wrapper.appendChild(removeBtn);
    imageList.appendChild(wrapper);
  });
  updateSubmitState();
}

function addImages(files) {
  Array.from(files).forEach((file) => {
    const url = URL.createObjectURL(file);
    state.images.push({ file, url });
  });
  refreshImageList();
}

function removeImage(index) {
  const item = state.images[index];
  if (item) {
    URL.revokeObjectURL(item.url);
    state.images.splice(index, 1);
    refreshImageList();
  }
}

function clearImages() {
  state.images.forEach((item) => URL.revokeObjectURL(item.url));
  state.images = [];
  refreshImageList();
}

captureBtn.addEventListener("click", () => cameraInput.click());
albumBtn.addEventListener("click", () => albumInput.click());

cameraInput.addEventListener("change", (event) => {
  addImages(event.target.files);
  cameraInput.value = "";
});

albumInput.addEventListener("change", (event) => {
  addImages(event.target.files);
  albumInput.value = "";
});

function updateSubmitState() {
  const valid =
    state.images.length > 0 && patientIdInput.value.trim();
  submitBtn.disabled = !valid;
}

patientIdInput.addEventListener("input", updateSubmitState);

document.querySelectorAll("[data-clear]").forEach((button) => {
  button.addEventListener("click", () => {
    const target = button.dataset.clear;
    if (target === "patient") {
      patientIdInput.value = "";
      patientNameInput.value = "";
      birthDateInput.value = "";
      sexInput.value = "";
    }
    if (target === "exam") {
      examModeInput.value = "auto";
      updateExamMode();
      examDateTimeInput.value = toLocalDateTimeValue(new Date());
      examDescriptionInput.value = "";
    }
    if (target === "images") {
      clearImages();
    }
    updateSubmitState();
  });
});

function buildFormData() {
  const formData = new FormData();
  state.images.forEach((item) => formData.append("images[]", item.file));
  if (patientIdInput.value.trim()) {
    formData.append("patientId", patientIdInput.value.trim());
  }
  if (patientNameInput.value.trim()) {
    formData.append("patientName", patientNameInput.value.trim());
  }
  if (birthDateInput.value) {
    formData.append("birthDate", birthDateInput.value);
  }
  if (sexInput.value) {
    formData.append("sex", sexInput.value);
  }
  if (examModeInput.value === "manual" && examDateTimeInput.value) {
    formData.append("examDateTime", examDateTimeInput.value);
  }
  if (examDescriptionInput.value.trim()) {
    formData.append("examDescription", examDescriptionInput.value.trim());
  }
  return formData;
}

async function submitStudy() {
  submitBtn.disabled = true;
  progressText.textContent = "送出中...";
  setStatus("上傳中", "idle");

  try {
    const response = await fetch("/api/studies", {
      method: "POST",
      body: buildFormData(),
    });
    const data = await response.json();
    if (!response.ok) {
      const code = data.code || "INTERNAL_ERROR";
      throw new Error(code);
    }
    progressText.textContent = "送出成功";
    setStatus("送信完成", "ok");
    clearImages();
    patientIdInput.value = "";
    patientNameInput.value = "";
    birthDateInput.value = "";
    sexInput.value = "";
    examDescriptionInput.value = "";
    if (examModeInput.value === "manual") {
      examDateTimeInput.value = "";
    }
  } catch (error) {
    const code = error.message;
    progressText.textContent = errorMessages[code] || "送出失敗，請稍後再試。";
    setStatus("送信失敗", "error");
  } finally {
    submitBtn.disabled = false;
    updateSubmitState();
  }
}

submitBtn.addEventListener("click", submitStudy);

async function loadSettings() {
  const response = await fetch("/api/settings");
  if (!response.ok) {
    return;
  }
  const data = await response.json();
  const settings = data.settings;

  pacsCalledAet.value = settings.pacs.calledAET || "";
  pacsHost.value = settings.pacs.host || "";
  pacsPort.value = settings.pacs.port || 0;

  if (settings.dicomweb) {
    dicomwebBaseUrl.value = settings.dicomweb.baseUrl || "";
    dicomwebVerifyTls.checked = settings.dicomweb.verifyTls !== false;
    dicomwebTimeout.value = settings.dicomweb.timeout || 30;
  }

  localCallingAet.value = settings.localAE.callingAET || "";
  localModality.value = settings.localAE.modality || "";
  localResizeMax.value = settings.localAE.resizeMax || 1024;
  localTransferSyntax.value = settings.localAE.transferSyntax || "";
  localCharset.value = settings.localAE.charset || "";

  flagPatientInfo.checked = settings.flags.includePatientInfoExceptId;
  flagExamDescription.checked = settings.flags.includeExamDescription;
  flagThemeDark.checked = settings.flags.themeDark;

  if (settings.scanner) {
    scannerConfig.roiHeightRatio = settings.scanner.roiHeightRatio ?? 0.4;
    scannerConfig.roiTargetWidth = settings.scanner.roiTargetWidth ?? 800;
    scannerConfig.detectIntervalMs = settings.scanner.detectIntervalMs ?? 100;
    scannerRoiHeight.value = scannerConfig.roiHeightRatio;
    scannerRoiWidth.value = scannerConfig.roiTargetWidth;
    scannerInterval.value = scannerConfig.detectIntervalMs;
  }

  applyTheme(flagThemeDark.checked);
}

function buildSettingsPayload() {
  return {
    pacs: {
      calledAET: pacsCalledAet.value.trim(),
      host: pacsHost.value.trim(),
      port: Number(pacsPort.value),
    },
    dicomweb: {
      baseUrl: dicomwebBaseUrl.value.trim() || null,
      verifyTls: dicomwebVerifyTls.checked,
      timeout: Number(dicomwebTimeout.value) || 30,
    },
    localAE: {
      callingAET: localCallingAet.value.trim(),
      modality: localModality.value.trim(),
      resizeMax: Number(localResizeMax.value),
      transferSyntax: localTransferSyntax.value.trim(),
      charset: localCharset.value.trim(),
    },
    flags: {
      includePatientInfoExceptId: flagPatientInfo.checked,
      includeExamDescription: flagExamDescription.checked,
      themeDark: flagThemeDark.checked,
    },
    scanner: {
      roiHeightRatio: Number(scannerRoiHeight.value) || 0.4,
      roiTargetWidth: Number(scannerRoiWidth.value) || 800,
      detectIntervalMs: Number(scannerInterval.value) || 0,
    },
  };
}

async function saveSettings() {
  settingsStatus.textContent = "儲存中...";
  try {
    const response = await fetch("/api/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildSettingsPayload()),
    });
    if (!response.ok) {
      throw new Error("SAVE_FAILED");
    }
    settingsStatus.textContent = "已儲存";
    applyTheme(flagThemeDark.checked);
    // 立即套用掃描器參數，免重整頁面即可生效。
    scannerConfig.roiHeightRatio = Number(scannerRoiHeight.value) || 0.4;
    scannerConfig.roiTargetWidth = Number(scannerRoiWidth.value) || 800;
    scannerConfig.detectIntervalMs = Number(scannerInterval.value) || 0;
  } catch (error) {
    settingsStatus.textContent = "儲存失敗";
  }
}

saveSettingsBtn.addEventListener("click", saveSettings);

function applyTheme(isDark) {
  document.body.dataset.theme = isDark ? "dark" : "light";
}

flagThemeDark.addEventListener("change", (event) => {
  applyTheme(event.target.checked);
});

async function testEcho() {
  echoResult.textContent = "測試中...";
  try {
    const payload = {
      calledAET: pacsCalledAet.value.trim(),
      host: pacsHost.value.trim(),
      port: Number(pacsPort.value),
      callingAET: localCallingAet.value.trim(),
    };
    const response = await fetch("/api/pacs/echo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
      const code = data.code || "PACS_REJECTED";
      echoResult.textContent = errorMessages[code] || "PACS 測試失敗";
      return;
    }
    echoResult.textContent = data.message || "C-ECHO OK";
  } catch (error) {
    echoResult.textContent = "連線失敗";
  }
}

echoBtn.addEventListener("click", testEcho);

async function testDicomwebEcho() {
  dicomwebEchoResult.textContent = "測試中...";
  try {
    const payload = {
      calledAET: pacsCalledAet.value.trim(),
      host: pacsHost.value.trim(),
      port: Number(pacsPort.value),
      callingAET: localCallingAet.value.trim(),
    };
    const response = await fetch("/api/pacs/echo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
      const code = data.code || "PACS_REJECTED";
      dicomwebEchoResult.textContent = errorMessages[code] || "DICOMweb 測試失敗";
      return;
    }
    dicomwebEchoResult.textContent = data.message || "DICOMweb OK";
  } catch (error) {
    dicomwebEchoResult.textContent = "連線失敗";
  }
}

dicomwebEchoBtn.addEventListener("click", testDicomwebEcho);

async function applyBackendVisibility() {
  const cardCstore = document.getElementById("cardCstore");
  const cardDicomweb = document.getElementById("cardDicomweb");
  try {
    const res = await fetch("/api/settings/info");
    if (!res.ok) return;
    const data = await res.json();
    const backend = data.pacsBackend;
    cardCstore.style.display = backend === "cstore" ? "" : "none";
    cardDicomweb.style.display = backend === "dicomweb" ? "" : "none";
  } catch {
    // 取得失敗時預設全部顯示
  }
}

// ─── 健保卡 AI OCR ───
async function resizeImageForOcr(file, maxSide = 1280, quality = 0.85) {
  const url = URL.createObjectURL(file);
  try {
    const img = await new Promise((resolve, reject) => {
      const image = new Image();
      image.onload = () => resolve(image);
      image.onerror = reject;
      image.src = url;
    });
    const longSide = Math.max(img.width, img.height);
    if (longSide <= maxSide) {
      return file;
    }
    const scale = maxSide / longSide;
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(img.width * scale);
    canvas.height = Math.round(img.height * scale);
    const ctx = canvas.getContext("2d");
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise((resolve) =>
      canvas.toBlob(resolve, "image/jpeg", quality)
    );
    if (!blob) {
      return file;
    }
    return new File([blob], file.name || "card.jpg", { type: "image/jpeg" });
  } finally {
    URL.revokeObjectURL(url);
  }
}

async function recognizeCardImage(file) {
  if (!file) return;
  ocrStatus.textContent = "AI 辨識中...";
  ocrCardBtn.disabled = true;
  try {
    const resized = await resizeImageForOcr(file);
    const formData = new FormData();
    formData.append("card_image", resized);
    const response = await fetch("/api/patient-id/ocr", {
      method: "POST",
      body: formData,
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const code = data.code || "INTERNAL_ERROR";
      const message = errorMessages[code] || "辨識失敗，請手動輸入。";
      ocrStatus.textContent = message;
      showToast(message, "error");
      return;
    }
    patientIdInput.value = (data.patientId || "").toUpperCase();
    updateSubmitState();
    // checksumValid=false 代表辨識結果未通過身分證檢查碼，極可能認錯一碼，
    // 務必請使用者核對，避免歸錯病患。
    const elapsed = data.elapsedMs ? `，辨識耗時 ${data.elapsedMs} ms` : "";
    if (data.checksumValid === false) {
      ocrStatus.textContent =
        `AI 填入：${patientIdInput.value}（檢查碼未通過，請核對！${elapsed}）`;
      patientIdInput.setAttribute("aria-invalid", "true");
      showToast("辨識結果檢查碼未通過，請務必核對身分證字號", "error", 5000);
    } else {
      patientIdInput.removeAttribute("aria-invalid");
      ocrStatus.textContent = `AI 已填入：${patientIdInput.value}${elapsed}`;
      showToast("健保卡辨識成功", "success", 2400);
    }
  } catch (error) {
    ocrStatus.textContent = "辨識失敗，請手動輸入。";
    showToast("健保卡辨識失敗", "error");
  } finally {
    ocrCardBtn.disabled = false;
  }
}

if (ocrCardBtn) {
  ocrCardBtn.addEventListener("click", () => ocrCardInput.click());
  ocrCardInput.addEventListener("change", (event) => {
    const file = event.target.files[0];
    if (file) recognizeCardImage(file);
    ocrCardInput.value = "";
  });
}

// ─── 條碼掃描器（原生 BarcodeDetector 優先，html5-qrcode 為 fallback）───
const scanBarcodeBtn = document.getElementById("scanBarcodeBtn");
const scannerModal = document.getElementById("scannerModal");
const closeScannerBtn = document.getElementById("closeScannerBtn");
const toggleTorchBtn = document.getElementById("toggleTorchBtn");
const scannerHint = document.getElementById("scannerHint");
let html5QrCode = null;
let torchEnabled = false;
let scannerActive = false;
let lastScanText = "";
let lastScanAt = 0;
let nativeStream = null;
let nativeRafId = null;
let nativeVideoEl = null;
let isDetecting = false;
let useBarcodeDetector = false;
let barcodeDetector = null;
let lastDetectAt = 0;
let scanStartedAt = 0;
let scannerOpener = null;

// 條碼掃描器可調參數（由設定頁載入並即時套用）。預設與後端 ScannerConfig 一致。
const scannerConfig = {
  roiHeightRatio: 0.4,
  roiTargetWidth: 800,
  detectIntervalMs: 100,
};

// ROI 裁切用的離屏 canvas：只把畫面中央橫條送進解碼器，
// 大幅減少像素量並濾掉上下雜訊，CODE 128 解碼更快也更穩。
const roiCanvas = document.createElement("canvas");
const roiCtx = roiCanvas.getContext("2d", { willReadFrequently: true });

// html5-qrcode 動態載入（僅原生 BarcodeDetector 不支援時，例如 iOS Safari）。
// 放本地 assets，確保離線 / 內網環境也能 fallback。
let html5QrLoaded = false;
function loadHtml5Qrcode() {
  if (html5QrLoaded || typeof Html5Qrcode !== "undefined") {
    return Promise.resolve();
  }
  return new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = "/assets/html5-qrcode.min.js";
    s.onload = () => {
      html5QrLoaded = true;
      resolve();
    };
    s.onerror = () => reject(new Error("無法載入掃描元件"));
    document.head.appendChild(s);
  });
}

function getBarcodeFormats() {
  return typeof Html5QrcodeSupportedFormats !== "undefined"
    ? [Html5QrcodeSupportedFormats.CODE_128]
    : [];
}

function getScannerBox() {
  const width = Math.min(window.innerWidth * 0.8, 420);
  const height = Math.max(80, Math.round(width * 0.45));
  return { width: Math.round(width), height };
}

async function detectBarcodeDetectorSupport() {
  if (!("BarcodeDetector" in window)) return false;
  try {
    const formats = await Promise.race([
      BarcodeDetector.getSupportedFormats(),
      new Promise((r) => setTimeout(() => r([]), 500)),
    ]);
    return formats.includes("code_128");
  } catch {
    return false;
  }
}

function isRearCameraLabel(label) {
  const l = (label || "").toLowerCase();
  return (
    l.includes("back") ||
    l.includes("rear") ||
    l.includes("environment") ||
    l.includes("後")
  );
}

async function chooseCamera() {
  const cameras = await Html5Qrcode.getCameras();
  if (!Array.isArray(cameras) || cameras.length === 0) {
    throw new Error("NO_CAMERA");
  }
  const rear = cameras.find((c) => isRearCameraLabel(c.label));
  return rear ? rear.id : cameras[cameras.length - 1].id;
}

async function getRearCameraStream() {
  const stream = await navigator.mediaDevices.getUserMedia({
    video: {
      facingMode: "environment",
      width: { ideal: 1280 },
      height: { ideal: 720 },
    },
  });
  const track = stream.getVideoTracks()[0];
  const settings = track.getSettings();
  if (settings.facingMode === "environment" || isRearCameraLabel(track.label)) {
    return stream;
  }
  const devices = await navigator.mediaDevices.enumerateDevices();
  const cameras = devices.filter((d) => d.kind === "videoinput");
  const rearByLabel = cameras.find((d) => isRearCameraLabel(d.label));
  if (rearByLabel && rearByLabel.deviceId !== settings.deviceId) {
    stream.getTracks().forEach((t) => t.stop());
    return navigator.mediaDevices.getUserMedia({
      video: {
        deviceId: { exact: rearByLabel.deviceId },
        width: { ideal: 1280 },
        height: { ideal: 720 },
      },
    });
  }
  for (const cam of cameras) {
    if (cam.deviceId === settings.deviceId) continue;
    try {
      const s = await navigator.mediaDevices.getUserMedia({
        video: {
          deviceId: { exact: cam.deviceId },
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
      });
      const fs = s.getVideoTracks()[0].getSettings();
      if (
        fs.facingMode === "environment" ||
        isRearCameraLabel(s.getVideoTracks()[0].label)
      ) {
        stream.getTracks().forEach((t) => t.stop());
        return s;
      }
      s.getTracks().forEach((t) => t.stop());
    } catch {
      // ignore – 試下一台鏡頭
    }
  }
  return stream;
}

function setTorchButtonState(enabled, on = false) {
  toggleTorchBtn.disabled = !enabled;
  toggleTorchBtn.textContent = on ? "關燈" : "開燈";
  toggleTorchBtn.setAttribute("aria-pressed", on ? "true" : "false");
}

function handleScan(decodedText) {
  const text = decodedText.trim();
  if (!text) return;
  const now = Date.now();
  if (text === lastScanText && now - lastScanAt < 1200) return;
  lastScanText = text;
  lastScanAt = now;
  patientIdInput.value = text;
  updateSubmitState();
  // 量化：從開啟掃描到解碼成功的耗時，供調參參考。
  const elapsed = scanStartedAt
    ? Math.round(
        (typeof performance !== "undefined" ? performance.now() : now) -
          scanStartedAt
      )
    : 0;
  closeScanner();
  showToast(
    elapsed ? `已掃描：${text}（${elapsed} ms）` : `已掃描：${text}`,
    "success",
    2400
  );
}

// 把畫面中央橫條（全寬、上下各裁約 30%）downscale 後交給解碼器。
// 一維條碼水平擺放，保留足夠水平解析度即可正確解碼。
function detectFromRoi() {
  const vw = nativeVideoEl.videoWidth;
  const vh = nativeVideoEl.videoHeight;
  if (!vw || !vh) return Promise.resolve([]);
  const roiH = Math.max(1, Math.round(vh * scannerConfig.roiHeightRatio));
  const sy = Math.round((vh - roiH) / 2);
  const targetW = Math.min(vw, scannerConfig.roiTargetWidth);
  const scale = targetW / vw;
  roiCanvas.width = targetW;
  roiCanvas.height = Math.max(1, Math.round(roiH * scale));
  roiCtx.drawImage(
    nativeVideoEl,
    0, sy, vw, roiH,
    0, 0, roiCanvas.width, roiCanvas.height
  );
  return barcodeDetector.detect(roiCanvas);
}

function nativeScanLoop(ts) {
  if (!scannerActive) return;
  nativeRafId = requestAnimationFrame(nativeScanLoop);
  if (isDetecting || !nativeVideoEl || nativeVideoEl.readyState < 2) return;
  // 節流：偵測間隔由設定決定（預設 100ms ≈ 10 次/秒），降低 CPU 負擔。
  if (ts && ts - lastDetectAt < scannerConfig.detectIntervalMs) return;
  lastDetectAt = ts || 0;
  isDetecting = true;
  detectFromRoi()
    .then((results) => {
      if (results.length > 0) handleScan(results[0].rawValue);
    })
    .catch(() => {})
    .finally(() => {
      isDetecting = false;
    });
}

async function startNativeScanner() {
  const scannerContainer = document.getElementById("scannerContainer");
  scannerContainer.innerHTML = "";
  const videoEl = document.createElement("video");
  videoEl.setAttribute("playsinline", "");
  videoEl.setAttribute("autoplay", "");
  videoEl.setAttribute("muted", "");
  scannerContainer.appendChild(videoEl);
  nativeVideoEl = videoEl;

  const box = getScannerBox();
  const overlay = document.createElement("div");
  overlay.className = "scan-overlay";
  const frame = document.createElement("div");
  frame.className = "scan-frame";
  frame.style.width = box.width + "px";
  frame.style.height = box.height + "px";
  overlay.appendChild(frame);
  scannerContainer.appendChild(overlay);

  nativeStream = await getRearCameraStream();
  videoEl.srcObject = nativeStream;
  await videoEl.play();

  const track = nativeStream.getVideoTracks()[0];
  const capabilities = track.getCapabilities ? track.getCapabilities() : {};
  setTorchButtonState(!!capabilities.torch, false);

  scannerHint.textContent = "將 CODE 128 條碼放入框內";
  isDetecting = false;
  nativeScanLoop();
}

async function openScannerFallback() {
  try {
    await loadHtml5Qrcode();
  } catch (err) {
    scannerHint.textContent = "無法載入掃描元件：" + err;
    showToast("無法載入掃描元件", "error");
    return;
  }
  html5QrCode = new Html5Qrcode("scannerContainer");
  chooseCamera()
    .then((cameraId) =>
      html5QrCode.start(
        cameraId,
        {
          fps: 12,
          qrbox: getScannerBox(),
          aspectRatio: 1.777778,
          formatsToSupport: getBarcodeFormats(),
        },
        handleScan,
        () => {}
      )
    )
    .then(() => {
      scannerHint.textContent = "請把 CODE 128 條碼放進框內，盡量靠近鏡頭";
      setTorchButtonState(true, false);
    })
    .catch((err) => {
      scannerHint.textContent = "無法啟動相機：" + err;
      showToast("無法啟動相機：" + err, "error");
    });
}

async function openScanner() {
  if (scannerActive) return;
  scannerOpener = document.activeElement;
  scannerActive = true;
  scanStartedAt = typeof performance !== "undefined" ? performance.now() : 0;
  scannerModal.classList.add("active");
  scannerModal.setAttribute("aria-hidden", "false");
  scannerHint.textContent = "啟動相機中...";
  setTorchButtonState(false);
  closeScannerBtn && closeScannerBtn.focus();
  useBarcodeDetector = await detectBarcodeDetectorSupport();
  if (useBarcodeDetector) {
    barcodeDetector = new BarcodeDetector({ formats: ["code_128"] });
    startNativeScanner().catch((err) => {
      scannerHint.textContent = "無法啟動相機：" + err;
      showToast("無法啟動相機：" + err, "error");
    });
  } else {
    openScannerFallback();
  }
}

function closeScanner() {
  scannerActive = false;
  torchEnabled = false;
  setTorchButtonState(false);
  if (nativeRafId) {
    cancelAnimationFrame(nativeRafId);
    nativeRafId = null;
  }
  if (nativeStream) {
    nativeStream.getTracks().forEach((t) => t.stop());
    nativeStream = null;
  }
  const scannerContainer = document.getElementById("scannerContainer");
  if (scannerContainer) scannerContainer.innerHTML = "";
  nativeVideoEl = null;
  if (html5QrCode) {
    html5QrCode
      .stop()
      .then(() => {
        html5QrCode.clear();
        html5QrCode = null;
      })
      .catch(() => {
        html5QrCode = null;
      });
  }
  scannerModal.classList.remove("active");
  scannerModal.setAttribute("aria-hidden", "true");
  if (scannerOpener && typeof scannerOpener.focus === "function") {
    scannerOpener.focus();
  }
  scannerOpener = null;
}

async function toggleTorch() {
  if (toggleTorchBtn.disabled) return;
  try {
    torchEnabled = !torchEnabled;
    if (useBarcodeDetector && nativeStream) {
      const track = nativeStream.getVideoTracks()[0];
      await track.applyConstraints({ advanced: [{ torch: torchEnabled }] });
    } else if (html5QrCode) {
      await html5QrCode.applyVideoConstraints({
        advanced: [{ torch: torchEnabled }],
      });
    }
    setTorchButtonState(true, torchEnabled);
  } catch {
    torchEnabled = false;
    setTorchButtonState(false, false);
    scannerHint.textContent = "此裝置不支援手電筒控制";
  }
}

if (scanBarcodeBtn) {
  scanBarcodeBtn.addEventListener("click", openScanner);
  closeScannerBtn.addEventListener("click", closeScanner);
  toggleTorchBtn.addEventListener("click", toggleTorch);
  scannerModal.addEventListener("click", (e) => {
    if (e.target === scannerModal) closeScanner();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    if (scannerModal.classList.contains("active")) closeScanner();
  });
}

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js").catch(() => undefined);
}

applyBackendVisibility();
loadSettings();
refreshImageList();
updateSubmitState();
