/* static/app.js — замените старый файл этим кодом */
const qs = id => document.getElementById(id);

const statusEl = qs('status');
const urlInput = qs('urlInput');
const btnParse = qs('btnParse');
const btnScan = qs('btnScan');
const resultArea = qs('resultArea');
const resultsBody = document.querySelector('#resultsTable tbody');
const rawJson = qs('rawJson');
const summary = qs('summary');
const btnClear = qs('btnClear');

function setBusy(busy, text) {
  if (busy) {
    statusEl.classList.remove('hidden');
    statusEl.textContent = text || 'Выполняется...';
    btnParse.disabled = btnScan.disabled = true;
    resultArea.classList.add('hidden'); // прячем результаты на время запроса
  } else {
    statusEl.classList.add('hidden');
    statusEl.textContent = '';
    btnParse.disabled = btnScan.disabled = false;
  }
}

function showResultArea() {
  resultArea.classList.remove('hidden');
  resultArea.setAttribute('aria-hidden', 'false');
}
function hideResultArea() {
  resultArea.classList.add('hidden');
  resultArea.setAttribute('aria-hidden', 'true');
}

/* --- полезные функции для извлечения текста из возможных объектов --- */

/**
 * Попытаться достать понятный текст из поля payload (которое может быть строкой или объектом).
 * Возвращает строку (не null/undefined). Не показывает "[object Object]" — если не получилось,
 * возвращает укороченную JSON-строку или '-'.
 */
function extractPayloadText(v) {
  if (v === null || v === undefined) return '-';
  if (typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean') return String(v);

  if (typeof v === 'object') {
    // Часто объект полезной нагрузки имеет форму { payload: "...", payload_id: "...", ... }
    if (typeof v.payload === 'string' && v.payload.trim() !== '') return v.payload;
    if (typeof v.payload_text === 'string' && v.payload_text.trim() !== '') return v.payload_text;
    if (typeof v.value === 'string' && v.value.trim() !== '') return v.value;
    if (typeof v.raw === 'string' && v.raw.trim() !== '') return v.raw;

    // иногда payload вложен ещё глубже: payload.payload
    if (v.payload && typeof v.payload === 'object') {
      const nested = extractPayloadText(v.payload);
      if (nested !== '-') return nested;
    }

    // fallback: сериализуем объект и вернём укороченную версию для таблицы
    try {
      const s = JSON.stringify(v);
      return s.length > 180 ? s.slice(0, 180) + '…' : s;
    } catch (e) {
      return '[object]';
    }
  }

  return String(v);
}

/**
 * Аналогично для evidence — пытаемся вывести читабельный текст.
 */
function extractEvidenceText(v) {
  if (v === null || v === undefined) return '-';
  if (typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean') return String(v);

  if (typeof v === 'object') {
    // Если это HTML/фрагмент — попробуем найти читаемые поля
    if (typeof v.evidence === 'string' && v.evidence.trim() !== '') return v.evidence;
    if (typeof v.ctx === 'string' && v.ctx.trim() !== '') return v.ctx;
    if (typeof v.message === 'string' && v.message.trim() !== '') return v.message;

    if (v.toString && v.toString() !== '[object Object]') {
      try {
        const s = v.toString();
        if (s && s.length < 200) return s;
      } catch (e) {}
    }

    // fallback: stringify (укороченно)
    try {
      const s = JSON.stringify(v);
      return s.length > 300 ? s.slice(0, 300) + '…' : s;
    } catch (e) {
      return '[object]';
    }
  }

  return String(v);
}

/* Короткий вид для таблицы (чтобы не раздувать столбцы) */
function shortForTable(s, max = 120) {
  if (!s && s !== 0) return '-';
  const str = String(s);
  return str.length > max ? (str.slice(0, max) + '…') : str;
}

/* --- рендеринг --- */
function renderFindings(data) {
  resultsBody.innerHTML = '';

  const arr = data.findings || data.forms || [];
  const total = arr.length;
  const scanFindings = (data.findings_count !== undefined) ? data.findings_count : total;
  summary.textContent = `Count: ${total}   Scan findings: ${scanFindings}`;

  // отфильтруем очевидные мусорные записи
  const filtered = arr.filter(it => {
    const p = extractPayloadText(it.payload);
    const e = extractEvidenceText(it.evidence);
    if (p === '-' || e === '-') return false;
    if (e === '[object]') return false;
    return true;
  });

  if (filtered.length === 0) {
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.colSpan = 3;
    td.textContent = 'Нет подходящих записей для отображения.';
    tr.appendChild(td);
    resultsBody.appendChild(tr);
    return;
  }

  filtered.forEach((it, idx) => {
    const tr = document.createElement('tr');

    const td0 = document.createElement('td');
    td0.textContent = idx + 1;

    const payloadTextFull = extractPayloadText(it.payload);
    const td1 = document.createElement('td');
    td1.textContent = shortForTable(payloadTextFull, 140);
    td1.title = payloadTextFull; // тултип с полным содержимым

    const evidenceTextFull = extractEvidenceText(it.evidence);
    const td2 = document.createElement('td');
    td2.textContent = shortForTable(evidenceTextFull, 180);
    td2.title = evidenceTextFull;

    tr.append(td0, td1, td2);

    // клик — показать полную запись в raw JSON
    tr.addEventListener('click', () => {
      try { rawJson.textContent = JSON.stringify(it, null, 2); }
      catch (e) { rawJson.textContent = String(it); }
      showResultArea();
    });

    resultsBody.appendChild(tr);
  });
}

/* --- общая функция вызова API --- */
async function callApi(path, targetUrl) {
  setBusy(true, 'Запрос к серверу...');
  try {
    const full = `${path}?url=${encodeURIComponent(targetUrl)}`;
    const r = await fetch(full, { method: 'GET' });
    const txt = await r.text();

    if (!r.ok) {
      setBusy(false);
      hideResultArea();
      rawJson.textContent = `Ошибка ${r.status}\n\n${txt}`;
      return null;
    }

    try {
      const json = JSON.parse(txt);
      setBusy(false);
      showResultArea();
      return json;
    } catch (e) {
      setBusy(false);
      hideResultArea();
      rawJson.textContent = txt;
      return null;
    }
  } catch (e) {
    setBusy(false);
    hideResultArea();
    rawJson.textContent = String(e);
    return null;
  }
}

/* --- обработчики кнопок --- */
btnParse.addEventListener('click', async () => {
  const url = urlInput.value.trim();
  if (!url) {
    setBusy(false);
    statusEl.classList.remove('hidden');
    statusEl.textContent = 'Введите URL';
    return;
  }
  hideResultArea();
  const data = await callApi('/api/parse', url);
  if (!data) return;
  renderFindings(data);
  rawJson.textContent = JSON.stringify(data, null, 2);
});

btnScan.addEventListener('click', async () => {
  const url = urlInput.value.trim();
  if (!url) {
    setBusy(false);
    statusEl.classList.remove('hidden');
    statusEl.textContent = 'Введите URL';
    return;
  }
  hideResultArea();
  const data = await callApi('/api/scan', url);
  if (!data) return;
  renderFindings(data);
  rawJson.textContent = JSON.stringify(data, null, 2);
});

btnClear.addEventListener('click', () => {
  resultsBody.innerHTML = '';
  rawJson.textContent = '';
  summary.textContent = '';
  hideResultArea();
  setBusy(false);
});

/* начальное состояние */
hideResultArea();
urlInput.value = "";
setBusy(false);