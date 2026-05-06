// PPT Master editor - minimal vanilla JS app.
// Talks to /api/* endpoints exposed by edit_server.py.

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

const state = {
  outline: null,
  designSystem: null,
  components: null,
  selectedSlide: null,
  selectedSection: null,
};

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
    ...opts,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText} — ${text}`);
  }
  const ctype = res.headers.get("Content-Type") || "";
  if (ctype.includes("application/json")) return res.json();
  return res.text();
}

function setStatus(text, kind = "") {
  const el = $("#status");
  el.textContent = text;
  el.className = "status" + (kind ? " " + kind : "");
}

// ---------------------------------------------------------------------------
// Theme panel
// ---------------------------------------------------------------------------

function renderThemePanel() {
  const panel = $("#theme-panel");
  panel.innerHTML = "";
  const ds = state.designSystem;
  if (!ds) {
    panel.innerHTML = '<div class="muted">DESIGN.md 없음</div>';
    return;
  }
  Object.entries(ds.colors).forEach(([token, hex]) => {
    const wrap = document.createElement("label");
    wrap.className = "swatch";
    wrap.title = token;
    wrap.innerHTML = `
      <input type="color" value="${hex}" data-token="${token}"/>
      <span>${token}</span>
    `;
    panel.appendChild(wrap);
  });

  panel.addEventListener("change", async (ev) => {
    const t = ev.target;
    if (t.matches('input[type=color][data-token]')) {
      const token = t.dataset.token;
      try {
        await api("/api/design-system", {
          method: "PATCH",
          body: JSON.stringify({ colors: { [token]: t.value } }),
        });
        setStatus(`색 토큰 ${token} → ${t.value}. "테마 적용"으로 반영.`, "success");
        state.designSystem.colors[token] = t.value;
      } catch (e) {
        setStatus("저장 실패: " + e.message, "error");
      }
    }
  }, { once: true });
}

// ---------------------------------------------------------------------------
// Slide tree + sections
// ---------------------------------------------------------------------------

function renderTree() {
  const root = $("#slide-tree");
  root.innerHTML = "";
  for (const slide of state.outline.slides || []) {
    const li = document.createElement("li");
    li.dataset.id = slide.id;
    li.innerHTML = `
      <span>${slide.id}</span>
      <span class="badge">${slide.dirty ? "● dirty" : ""}</span>
    `;
    if (slide.id === state.selectedSlide) li.classList.add("active");
    li.addEventListener("click", () => selectSlide(slide.id));
    root.appendChild(li);
  }

  const slist = $("#section-list");
  slist.innerHTML = "";
  for (const sec of state.outline.sections || []) {
    const li = document.createElement("li");
    li.dataset.id = sec.id;
    li.innerHTML = `<span>${sec.title || sec.id}</span><span class="muted">${(sec.slides || []).length}</span>`;
    if (sec.id === state.selectedSection) li.classList.add("active");
    li.addEventListener("click", () => selectSection(sec.id));
    slist.appendChild(li);
  }

  const sel = $("#select-section");
  sel.innerHTML = (state.outline.sections || [])
    .map((s) => `<option value="${s.id}">${s.title || s.id}</option>`)
    .join("");
}

function selectSlide(id) {
  state.selectedSlide = id;
  state.selectedSection = null;
  $("#btn-regen-slide").disabled = !id;
  $("#btn-regen-section").disabled = true;
  renderTree();
  renderInspector();
  loadPreview(id);
}

function selectSection(id) {
  state.selectedSection = id;
  state.selectedSlide = null;
  $("#btn-regen-section").disabled = !id;
  $("#btn-regen-slide").disabled = true;
  renderTree();
  $("#preview-frame").innerHTML = '<div class="empty">섹션 선택. 슬라이드를 골라 미리보기.</div>';
}

// ---------------------------------------------------------------------------
// Inspector
// ---------------------------------------------------------------------------

function renderInspector() {
  const slide = (state.outline.slides || []).find((s) => s.id === state.selectedSlide);
  const form = $("#slide-form");
  if (!slide) {
    form.reset();
    return;
  }
  form.id.value = slide.id;
  form.title.value = slide.title || "";
  form.subtitle.value = slide.subtitle || "";
  form.slide_template.value = slide.slide_template || "";
  form.section.value = slide.section || "";
  form.components.value = (slide.components || []).join("\n");
  form.bullets.value = (slide.bullets || []).join("\n");
  form.notes.value = slide.notes || "";
}

$("#slide-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const slide = (state.outline.slides || []).find((s) => s.id === state.selectedSlide);
  if (!slide) return;
  const f = ev.target;
  slide.title = f.title.value;
  slide.subtitle = f.subtitle.value;
  slide.slide_template = f.slide_template.value;
  slide.section = f.section.value;
  slide.components = f.components.value.split(/\r?\n/).map((s) => s.trim()).filter(Boolean);
  slide.bullets = f.bullets.value.split(/\r?\n/).map((s) => s.trim()).filter(Boolean);
  slide.notes = f.notes.value;
  slide.dirty = true;
  try {
    await api("/api/outline", { method: "PUT", body: JSON.stringify(state.outline) });
    setStatus(`슬라이드 ${slide.id} 저장됨 (dirty=true)`, "success");
    renderTree();
  } catch (e) {
    setStatus("저장 실패: " + e.message, "error");
  }
});

// ---------------------------------------------------------------------------
// Preview
// ---------------------------------------------------------------------------

async function loadPreview(slideId) {
  const frame = $("#preview-frame");
  frame.innerHTML = '<div class="empty">로딩…</div>';
  try {
    const svg = await api(`/api/slides/${slideId}.svg`);
    frame.innerHTML = svg;
    $("#preview-meta").textContent = `${slideId} · 미리보기`;
  } catch (e) {
    frame.innerHTML = `<div class="empty">미리보기 없음 (${e.message})</div>`;
    $("#preview-meta").textContent = "";
  }
}

// ---------------------------------------------------------------------------
// Component gallery
// ---------------------------------------------------------------------------

function renderComponents() {
  const root = $("#component-gallery");
  root.innerHTML = "";
  if (!state.components) return;
  for (const [name, meta] of Object.entries(state.components.components || {})) {
    const tile = document.createElement("div");
    tile.className = "tile";
    const placeholder = (meta.svg || "")
      .replace(/\{[^{}]+\}/g, "#cccccc")
      .replace(/\{\{[^{}]+\}\}/g, "…");
    tile.innerHTML = `
      ${placeholder}
      <div class="name">${name}</div>
    `;
    tile.title = `Click to append <use data-component="${name}"/> to current slide`;
    tile.addEventListener("click", () => insertComponent(name, meta));
    root.appendChild(tile);
  }
}

function insertComponent(name, meta) {
  const slide = (state.outline.slides || []).find((s) => s.id === state.selectedSlide);
  if (!slide) {
    setStatus("슬라이드를 먼저 선택하세요.", "error");
    return;
  }
  const ref = `${name}?x=80&y=120&w=${meta.defaultWidth}&h=${meta.defaultHeight}`;
  slide.components = [...(slide.components || []), ref];
  renderInspector();
  setStatus(`${name} 삽입됨 (저장 후 재생성 필요)`, "success");
}

// ---------------------------------------------------------------------------
// Regenerate buttons
// ---------------------------------------------------------------------------

async function regenerate(mode, ids) {
  const body = { mode, ids: ids || [] };
  setStatus(`${mode} 재생성 중…`);
  try {
    const r = await api("/api/regenerate", {
      method: "POST",
      body: JSON.stringify(body),
    });
    if (r.ok) {
      setStatus(`${mode} 재생성 완료`, "success");
      await loadAll();
      if (state.selectedSlide) loadPreview(state.selectedSlide);
    } else {
      setStatus(`재생성 실패 (rc=${r.returncode})`, "error");
      console.error(r);
    }
  } catch (e) {
    setStatus("재생성 실패: " + e.message, "error");
  }
}

$("#btn-regen-slide").addEventListener("click", () => {
  if (state.selectedSlide) regenerate("slides", [state.selectedSlide]);
});
$("#btn-regen-section").addEventListener("click", () => {
  if (state.selectedSection) regenerate("sections", [state.selectedSection]);
});
$("#btn-regen-theme").addEventListener("click", () => regenerate("theme"));
$("#btn-reorganize").addEventListener("click", () => regenerate("reorganize"));

$("#btn-add-slide").addEventListener("click", async () => {
  const id = prompt("새 슬라이드 ID (예: 05_demo)");
  if (!id) return;
  state.outline.slides = state.outline.slides || [];
  state.outline.slides.push({
    id,
    section: state.outline.sections?.[0]?.id || "all",
    slide_template: "content_default",
    title: "",
    subtitle: "",
    components: [],
    bullets: [],
    notes: "",
    dirty: true,
  });
  await api("/api/outline", { method: "PUT", body: JSON.stringify(state.outline) });
  await loadAll();
  selectSlide(id);
});

// ---------------------------------------------------------------------------
// Bootstrap
// ---------------------------------------------------------------------------

async function loadAll() {
  state.outline = await api("/api/outline");
  $("#project-name").textContent = state.outline?.meta?.template
    ? `${state.outline.meta.template} · ${state.outline.meta.canvas}`
    : "(no outline)";
  try {
    state.designSystem = await api("/api/design-system");
  } catch {
    state.designSystem = null;
  }
  state.components = await api("/api/components");
  renderThemePanel();
  renderTree();
  renderComponents();
  if (!state.selectedSlide && state.outline.slides?.length) {
    selectSlide(state.outline.slides[0].id);
  }
}

loadAll().catch((e) => setStatus("초기화 실패: " + e.message, "error"));
