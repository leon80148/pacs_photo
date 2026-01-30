const tabs = document.querySelectorAll(".tab");
const panels = document.querySelectorAll(".tab-panel");
const statusPill = document.getElementById("statusPill");

const patientIdInput = document.getElementById("patientId");
const chartNoInput = document.getElementById("chartNo");
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

const state = {
  images: [],
};

const errorMessages = {
  VALIDATION_ERROR: "欄位未填完整或格式錯誤。",
  PATIENT_NOT_FOUND: "病歷號查不到，請確認病歷號是否正確。",
  PATIENT_ID_MISMATCH: "患者ID與病歷號不一致，請修正。",
  HIS_UNAVAILABLE: "HIS 無法連線或逾時。",
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
    state.images.length > 0 &&
    (patientIdInput.value.trim() || chartNoInput.value.trim());
  submitBtn.disabled = !valid;
}

[patientIdInput, chartNoInput].forEach((input) =>
  input.addEventListener("input", updateSubmitState)
);

document.querySelectorAll("[data-clear]").forEach((button) => {
  button.addEventListener("click", () => {
    const target = button.dataset.clear;
    if (target === "patient") {
      patientIdInput.value = "";
      chartNoInput.value = "";
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
  if (chartNoInput.value.trim()) {
    formData.append("chartNo", chartNoInput.value.trim());
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
    chartNoInput.value = "";
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
    his: {
      baseUrl: null,
      apiKey: null,
      timeout: 5,
      retry: 0,
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

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js").catch(() => undefined);
}

applyBackendVisibility();
loadSettings();
refreshImageList();
updateSubmitState();
