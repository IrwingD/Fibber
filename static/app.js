// ---------------------------------------------------------------------
// Auth token: the server embedded it in the URL it opened us with.
// Every API call must echo it back as a header.
// ---------------------------------------------------------------------
const APP_TOKEN = new URLSearchParams(location.search).get("token") || "";

async function api(path, options = {}) {
  const res = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-App-Token": APP_TOKEN,
      ...(options.headers || {}),
    },
  });
  if (!res.ok) throw new Error(`${path} -> ${res.status}`);
  return res;
}

// ---------------------------------------------------------------------
// Heartbeat: tells the Python process we're still open. If this stops
// (tab closed), the server shuts itself down within ~20s.
// ---------------------------------------------------------------------
setInterval(() => {
  api("/api/heartbeat", { method: "POST" }).catch(() => {});
}, 8000);

// ---------------------------------------------------------------------
// State
// ---------------------------------------------------------------------
let providersByCategory = {};
let previewTimer = null;

const el = {
  locale: document.getElementById("locale"),
  seed: document.getElementById("seed"),
  themeToggle: document.getElementById("theme-toggle"),
  fieldList: document.getElementById("field-list"),
  addField: document.getElementById("add-field"),
  rows: document.getElementById("rows"),
  rowsNumber: document.getElementById("rows-number"),
  exportCsv: document.getElementById("export-csv"),
  exportJson: document.getElementById("export-json"),
  shuffle: document.getElementById("shuffle"),
  status: document.getElementById("status"),
  previewHead: document.getElementById("preview-head"),
  previewBody: document.getElementById("preview-body"),
  template: document.getElementById("field-row-template"),
};

// ---------------------------------------------------------------------
// Dark mode. NOTE: this can't reliably use localStorage -- the server
// binds a different random port every launch, so from the browser's
// perspective each session is a different origin with fresh storage.
// Persist it server-side in settings.json instead, same as the schema.
// ---------------------------------------------------------------------
function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  el.themeToggle.textContent = theme === "dark" ? "Light mode" : "Dark mode";
}
applyTheme("light"); // instant paint while settings load
el.themeToggle.addEventListener("click", () => {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  applyTheme(next);
  saveSettings();
});

// ---------------------------------------------------------------------
// Rows: slider and number box stay in sync both directions
// ---------------------------------------------------------------------
function setRows(value) {
  const clamped = Math.max(1, Math.min(500000, Math.round(Number(value) || 0)));
  el.rows.value = Math.min(100000, clamped);
  el.rowsNumber.value = clamped;
  return clamped;
}
el.rows.addEventListener("input", () => {
  setRows(el.rows.value);
  saveSettings();
});
el.rowsNumber.addEventListener("input", () => {
  setRows(el.rowsNumber.value);
  saveSettings();
});

function currentFields() {
  return [...el.fieldList.querySelectorAll(".field-row")].map((row) => ({
    name: row.querySelector(".field-name").value.trim() || "field",
    provider: row.querySelector(".field-provider").value,
  }));
}

function currentSchema() {
  return {
    locale: el.locale.value,
    seed: el.seed.value ? el.seed.value : null,
    fields: currentFields(),
    rows: Number(el.rowsNumber.value),
    theme: document.documentElement.dataset.theme || "light",
  };
}

// ---------------------------------------------------------------------
// Field rows
// ---------------------------------------------------------------------
function addFieldRow(initial = {}) {
  const node = el.template.content.firstElementChild.cloneNode(true);
  const nameInput = node.querySelector(".field-name");
  const categorySelect = node.querySelector(".field-category");
  const providerSelect = node.querySelector(".field-provider");

  nameInput.value = initial.name || "";

  Object.keys(providersByCategory).forEach((cat) => {
    const opt = document.createElement("option");
    opt.value = cat;
    opt.textContent = cat;
    categorySelect.appendChild(opt);
  });

  function fillProviders(selectedProvider) {
    providerSelect.innerHTML = "";
    const list = providersByCategory[categorySelect.value] || [];
    list.forEach((p) => {
      const opt = document.createElement("option");
      opt.value = p;
      opt.textContent = p;
      providerSelect.appendChild(opt);
    });
    if (selectedProvider && list.includes(selectedProvider)) {
      providerSelect.value = selectedProvider;
    }
  }

  if (initial.provider) {
    // find category containing this provider
    const cat = Object.keys(providersByCategory).find((c) =>
      providersByCategory[c].includes(initial.provider)
    );
    if (cat) categorySelect.value = cat;
  }
  fillProviders(initial.provider);

  categorySelect.addEventListener("change", () => {
    fillProviders();
    schedulePreview();
  });
  providerSelect.addEventListener("change", schedulePreview);
  nameInput.addEventListener("input", schedulePreview);
  node.querySelector(".remove-field").addEventListener("click", () => {
    node.remove();
    schedulePreview();
  });

  el.fieldList.appendChild(node);
  schedulePreview();
}

// ---------------------------------------------------------------------
// Preview
// ---------------------------------------------------------------------
function schedulePreview() {
  clearTimeout(previewTimer);
  previewTimer = setTimeout(runPreview, 350);
  saveSettings();
}

async function runPreview() {
  const schema = currentSchema();
  if (schema.fields.length === 0) {
    el.previewHead.innerHTML = "";
    el.previewBody.innerHTML = "";
    el.status.textContent = "";
    return;
  }
  el.status.textContent = "Generating preview…";
  try {
    const res = await api("/api/preview", {
      method: "POST",
      body: JSON.stringify(schema),
    });
    const rows = await res.json();
    renderPreview(schema.fields, rows);
    el.status.textContent = "";
  } catch (e) {
    el.status.textContent = `Preview failed: ${e.message}`;
  }
}

function renderPreview(fields, rows) {
  el.previewHead.innerHTML = fields
    .map((f) => `<th>${escapeHtml(f.name)}</th>`)
    .join("");
  el.previewBody.innerHTML = rows
    .map(
      (row) =>
        "<tr>" +
        fields.map((f) => `<td>${escapeHtml(String(row[f.name] ?? ""))}</td>`).join("") +
        "</tr>"
    )
    .join("");
}

function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

// ---------------------------------------------------------------------
// Export (downloads via streamed response -> blob -> temp link click)
// ---------------------------------------------------------------------
async function runExport(format) {
  const schema = currentSchema();
  if (schema.fields.length === 0) {
    el.status.textContent = "Add at least one field first.";
    return;
  }
  el.status.textContent = `Generating ${schema.rows.toLocaleString()} rows…`;
  try {
    const res = await api("/api/generate", {
      method: "POST",
      body: JSON.stringify({ ...schema, format }),
    });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = format === "json" ? "synthetic_data.json" : "synthetic_data.csv";
    a.click();
    URL.revokeObjectURL(url);
    el.status.textContent = `Done — ${schema.rows.toLocaleString()} rows exported.`;
  } catch (e) {
    el.status.textContent = "Export failed.";
  }
}

// ---------------------------------------------------------------------
// Settings persistence (saved next to the exe, restored on next launch)
// ---------------------------------------------------------------------
let saveTimer = null;
function saveSettings() {
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {
    api("/api/settings", { method: "POST", body: JSON.stringify(currentSchema()) }).catch(() => {});
  }, 500);
}

async function loadSettings() {
  try {
    const res = await api("/api/settings");
    return await res.json();
  } catch (e) {
    return null;
  }
}

// ---------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------
async function loadProviders() {
  const res = await api(`/api/providers?locale=${encodeURIComponent(el.locale.value)}`);
  providersByCategory = await res.json();
}

async function init() {
  const localesRes = await api("/api/locales");
  const localeList = await localesRes.json();
  el.locale.innerHTML = localeList.map((l) => `<option value="${l}">${l}</option>`).join("");

  const saved = await loadSettings();
  if (saved && saved.locale) el.locale.value = saved.locale;
  if (saved && saved.theme) applyTheme(saved.theme);

  await loadProviders();

  if (saved && saved.fields && saved.fields.length) {
    if (saved.seed) el.seed.value = saved.seed;
    if (saved.rows) setRows(saved.rows);
    saved.fields.forEach((f) => addFieldRow(f));
  } else {
    // sensible starter schema
    addFieldRow({ name: "full_name", provider: "name" });
    addFieldRow({ name: "email", provider: "email" });
    addFieldRow({ name: "company", provider: "company" });
  }
}

el.locale.addEventListener("change", async () => {
  await loadProviders();
  // re-render existing rows against the new locale's provider list
  const fields = currentFields();
  el.fieldList.innerHTML = "";
  fields.forEach((f) => addFieldRow(f));
  schedulePreview();
});

el.seed.addEventListener("input", schedulePreview);
el.addField.addEventListener("click", () => addFieldRow());
el.shuffle.addEventListener("click", runPreview);
el.exportCsv.addEventListener("click", () => runExport("csv"));
el.exportJson.addEventListener("click", () => runExport("json"));

init();