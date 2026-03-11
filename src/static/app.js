const $ = id => document.getElementById(id)

const urlInput = $('urlInput')
const btnParse = $('btnParse')
const btnScan = $('btnScan')
const btnClear = $('btnClear')

const resultArea = $('resultArea')
const status = $('status')

const aggArea = $('aggArea')
const detailedArea = $('detailedArea')

const resultsBody = document.querySelector('#resultsTable tbody')

const rawJson = $('rawJson')
const summary = $('summary')

const btnBackSummary = $('btnBackSummary')
const btnShowAll = $('btnShowAll')

const leftTitle = $('leftTitle')

let lastData = null


function escapeHtml(s) {
  if (!s) return ""
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
}

function short(s, n = 140) {
  if (!s) return "-"
  s = String(s)
  return s.length > n ? s.slice(0, n) + "…" : s
}

function pretty(o) {
  return JSON.stringify(o, null, 2)
}

function setBusy(v) {
  if (v) {
    status.textContent = "Выполняется...";
    status.classList.remove("hidden");
    resultArea.classList.add("hidden");
  } else {
    status.classList.add("hidden");
  }
}

function showResults() {
  resultArea.classList.remove("hidden")
}

async function callApi(path, url) {
  setBusy(true);

  const r = await fetch(`${path}?url=${encodeURIComponent(url)}`);
  const text = await r.text();

  setBusy(false); 

  if (!r.ok) {
    rawJson.textContent = text;                
    showResults();                            
    status.textContent = `Ошибка ${r.status}: ${r.statusText}`;
    status.classList.remove("hidden");          
    return null;
  }

  try {
    return JSON.parse(text);
  } catch {
    rawJson.textContent = text;
    showResults();
    status.textContent = "Ошибка: ответ сервера не является JSON";
    status.classList.remove("hidden");
    return null;
  }
}

function renderClusters(data) {

  const agg = data.aggregated_findings || data
  const clusters = agg.clusters || []

  aggArea.innerHTML = ""

  summary.textContent = `Clusters: ${clusters.length}`

  clusters.forEach(c => {

    const card = document.createElement("div")
    card.className = "cluster-card"

    const payload = escapeHtml(c.representative_payload || "")
    const evidence = escapeHtml(c.representative_evidence || "")

    card.innerHTML = `
      <div class="cluster-top">
        <div class="cluster-title">Cluster ${c.cluster_label}</div>
        <div class="cluster-meta">
          <span class="cluster-stat">${c.findings_count}</span>
        </div>
      </div>

      <div class="cluster-body">
        <b>Payload:</b><br>
        ${payload}
      </div>

      <div class="cluster-body">
        <b>Evidence:</b><br>
        ${evidence}
      </div>
    `

    aggArea.appendChild(card)
  })

  btnShowAll.classList.remove("hidden")
  btnBackSummary.classList.add("hidden")
  leftTitle.textContent = "Краткая сводка"
}

function renderAllFindings(data) {

  const findings = data.findings || []

  aggArea.innerHTML = ""
  detailedArea.classList.remove("hidden")

  leftTitle.textContent = `Все findings (${findings.length})`

  btnBackSummary.classList.remove("hidden")
  btnShowAll.classList.add("hidden")

  summary.textContent = `Всего findings: ${findings.length}`

  resultsBody.innerHTML = ""

  findings.forEach((f,i)=>{

    const payload =
      escapeHtml(
        f.payload?.payload ||
        f.payload ||
        ""
      )

    const evidence =
      escapeHtml(
        f.evidence ||
        ""
      )


    const tr = document.createElement("tr")

    tr.innerHTML = `
      <td>${i+1}</td>
      <td>${short(payload,120)}</td>
      <td>${short(evidence,200)}</td>
    `

    tr.onclick = () => {
      rawJson.textContent = pretty(f)
    }

    resultsBody.appendChild(tr)

  })

}


btnParse.onclick = async ()=>{

  const url = urlInput.value.trim()
  if(!url) return

  const data = await callApi("/api/parse",url)
  if(!data) return

  lastData = data

  rawJson.textContent = pretty(data)

  renderClusters(data)

  showResults()
}

btnScan.onclick = async ()=>{

  const url = urlInput.value.trim()
  if(!url) return

  const data = await callApi("/api/scan",url)
  if(!data) return

  lastData = data

  rawJson.textContent = pretty(data)

  renderClusters(data)

  showResults()
}



btnShowAll.onclick = ()=>{
  if(!lastData) return
  renderAllFindings(lastData)
}



btnBackSummary.onclick = ()=>{
  if(!lastData) return

  detailedArea.classList.add("hidden")
  renderClusters(lastData)
}



btnClear.onclick = ()=>{

  aggArea.innerHTML = ""
  resultsBody.innerHTML = ""
  rawJson.textContent = ""
  summary.textContent = ""

  resultArea.classList.add("hidden")

  btnShowAll.classList.add("hidden")
  btnBackSummary.classList.add("hidden")
}




resultArea.classList.add("hidden")
btnShowAll.classList.add("hidden")
btnBackSummary.classList.add("hidden")
urlInput.value = "http://127.0.0.1:4280/vulnerabilities/xss_r/"