/* ── script.js — IPL Predictor Frontend Logic ─────────────────── */

// ─── Team metadata ────────────────────────────────────────────────
const TEAM_META = {
  "Chennai Super Kings":        { key:"csk", short:"CSK",  color:"#fbbf04" },
  "Mumbai Indians":             { key:"mi",  short:"MI",   color:"#004c97" },
  "Royal Challengers Bangalore":{ key:"rcb", short:"RCB",  color:"#c8102e" },
  "Royal Challengers Bengaluru":{ key:"rcb", short:"RCB",  color:"#c8102e" },
  "Kolkata Knight Riders":      { key:"kkr", short:"KKR",  color:"#8b5cf6" },
  "Rajasthan Royals":           { key:"rr",  short:"RR",   color:"#ea4063" },
  "Sunrisers Hyderabad":        { key:"srh", short:"SRH",  color:"#ff6600" },
  "Delhi Capitals":             { key:"dc",  short:"DC",   color:"#003da5" },
  "Delhi Daredevils":           { key:"dc",  short:"DD",   color:"#003da5" },
  "Punjab Kings":               { key:"pk",  short:"PBKS", color:"#aa0000" },
  "Kings XI Punjab":            { key:"pk",  short:"KXIP", color:"#aa0000" },
  "Gujarat Titans":             { key:"gt",  short:"GT",   color:"#1c3f77" },
  "Lucknow Super Giants":       { key:"lsg", short:"LSG",  color:"#a2e85d" },
  "Deccan Chargers":            { key:"srh", short:"DC",   color:"#ff6600" },
  "Kochi Tuskers Kerala":       { key:"dc",  short:"KTK",  color:"#228b22" },
  "Rising Pune Supergiants":    { key:"rr",  short:"RPS",  color:"#8b5cf6" },
  "Rising Pune Supergiant":     { key:"rr",  short:"RPS",  color:"#8b5cf6" },
  "Pune Warriors":              { key:"dc",  short:"PW",   color:"#2563eb" },
};

function getMeta(team) {
  return TEAM_META[team] || { key:"dc", short: team.slice(0,3).toUpperCase(), color:"#7c3aed" };
}

// ─── DOM refs ─────────────────────────────────────────────────────
const team1Select     = document.getElementById("team1Select");
const team2Select     = document.getElementById("team2Select");
const venueSelect     = document.getElementById("venueSelect");
const tossWinnerSel   = document.getElementById("tossWinnerSelect");
const tossDecisionSel = document.getElementById("tossDecisionSelect");
const badge1          = document.getElementById("badge1");
const badge2          = document.getElementById("badge2");
const panel1          = document.getElementById("panel1");
const panel2          = document.getElementById("panel2");
const predictBtn      = document.getElementById("predictBtn");
const resultSection   = document.getElementById("resultSection");

let winRateChart  = null;
let avgScoreChart = null;

// ─── Load meta from API ───────────────────────────────────────────
async function loadMeta() {
  try {
    const res  = await fetch("/api/meta");
    const data = await res.json();
    populateTeams(data.teams);
    populateVenues(data.venues);
    document.getElementById("modelAccText").textContent =
      `Model Accuracy: ${data.accuracy}%`;
  } catch (e) {
    console.error("Meta load failed", e);
  }
}

function populateTeams(teams) {
  [team1Select, team2Select].forEach(sel => {
    sel.innerHTML = '<option value="">-- Select Team --</option>';
    teams.forEach(t => {
      const opt = document.createElement("option");
      opt.value = t;
      opt.textContent = t;
      sel.appendChild(opt);
    });
  });
}

function populateVenues(venues) {
  venues.slice(0, 60).forEach(v => {
    const opt = document.createElement("option");
    opt.value = v;
    opt.textContent = v.length > 50 ? v.slice(0, 50) + "…" : v;
    venueSelect.appendChild(opt);
  });
}

// ─── Team selection handlers ──────────────────────────────────────
function updateBadge(badge, team, panel) {
  const meta = getMeta(team);
  badge.textContent = meta.short;
  badge.style.background = `${meta.color}22`;
  badge.style.borderColor = meta.color;
  badge.style.boxShadow   = `0 0 20px ${meta.color}44`;
  panel.setAttribute("data-team", meta.key);
}

function resetBadge(badge, panel) {
  badge.textContent = "?";
  badge.style.background = "";
  badge.style.borderColor = "";
  badge.style.boxShadow   = "";
  panel.removeAttribute("data-team");
}

team1Select.addEventListener("change", () => {
  const t = team1Select.value;
  if (t) { updateBadge(badge1, t, panel1); } else { resetBadge(badge1, panel1); }
  updateTossOptions();
  checkReady();
});

team2Select.addEventListener("change", () => {
  const t = team2Select.value;
  if (t) { updateBadge(badge2, t, panel2); } else { resetBadge(badge2, panel2); }
  updateTossOptions();
  checkReady();
});

function updateTossOptions() {
  const t1 = team1Select.value;
  const t2 = team2Select.value;
  tossWinnerSel.innerHTML = '<option value="">Not decided</option>';
  if (t1) {
    const o = document.createElement("option"); o.value = t1; o.textContent = t1;
    tossWinnerSel.appendChild(o);
  }
  if (t2) {
    const o = document.createElement("option"); o.value = t2; o.textContent = t2;
    tossWinnerSel.appendChild(o);
  }
}

function checkReady() {
  const t1 = team1Select.value;
  const t2 = team2Select.value;
  predictBtn.disabled = !(t1 && t2 && t1 !== t2);
}

// ─── Predict ──────────────────────────────────────────────────────
predictBtn.addEventListener("click", async () => {
  const t1 = team1Select.value;
  const t2 = team2Select.value;
  if (!t1 || !t2 || t1 === t2) return;

  // Loading state
  predictBtn.classList.add("loading");
  predictBtn.disabled = true;

  try {
    const payload = {
      team1:          t1,
      team2:          t2,
      venue:          venueSelect.value,
      toss_winner:    tossWinnerSel.value || t1,
      toss_decision:  tossDecisionSel.value,
    };

    const res  = await fetch("/api/predict", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(payload),
    });
    const data = await res.json();

    if (data.error) { alert("Error: " + data.error); return; }

    renderResult(data);
  } catch (e) {
    console.error("Predict failed", e);
    alert("Prediction failed. Is the Flask server running?");
  } finally {
    predictBtn.classList.remove("loading");
    predictBtn.disabled = false;
  }
});

// ─── Render result ────────────────────────────────────────────────
function renderResult(data) {
  const { team1, team2, winner, team1_prob, team2_prob, h2h, team1_stats, team2_stats } = data;

  // Show section
  resultSection.style.display = "flex";
  resultSection.scrollIntoView({ behavior: "smooth", block: "start" });

  // Winner banner
  document.getElementById("winnerName").textContent   = winner;
  const winProb = winner === team1 ? team1_prob : team2_prob;
  document.getElementById("winnerProb").textContent   = `${winProb}% confidence`;
  spawnConfetti();

  // Probability bars
  document.getElementById("pt1Name").textContent = team1;
  document.getElementById("pt2Name").textContent = team2;
  document.getElementById("pt1Pct").textContent  = `${team1_prob}%`;
  document.getElementById("pt2Pct").textContent  = `${team2_prob}%`;

  // Animate bars after brief delay
  setTimeout(() => {
    document.getElementById("bar1").style.width = `${team1_prob}%`;
    document.getElementById("bar2").style.width = `${team2_prob}%`;
  }, 200);

  // H2H
  document.getElementById("h2hT1Name").textContent  = team1;
  document.getElementById("h2hT2Name").textContent  = team2;
  document.getElementById("h2hT1Wins").textContent  = h2h.team1_wins;
  document.getElementById("h2hT2Wins").textContent  = h2h.team2_wins;
  document.getElementById("h2hTotal").textContent   = h2h.total;

  // Team analysis cards
  renderAnalysisCard("analysis1", team1, team1_stats, "bar-t1");
  renderAnalysisCard("analysis2", team2, team2_stats, "bar-t2");

  // Charts
  renderCharts(team1, team2, team1_stats, team2_stats);
}

function renderAnalysisCard(containerId, teamName, stats, barClass) {
  const el   = document.getElementById(containerId);
  const meta = getMeta(teamName);

  const winPct    = stats.win_rate ? (stats.win_rate * 100).toFixed(1) : "—";
  const avgScore  = stats.avg_score ? stats.avg_score.toFixed(1) : "—";
  const matches   = stats.matches  ?? "—";
  const wins      = stats.wins     ?? "—";
  const seasons   = stats.seasons  ? `${stats.seasons[0]} – ${stats.seasons[stats.seasons.length-1]}` : "—";

  const batters   = (stats.top_batters || []).slice(0, 4);
  const bowlers   = (stats.top_bowlers || []).slice(0, 4);

  el.innerHTML = `
    <div class="tac-header">
      <div class="tac-badge" style="background:${meta.color}22;border:2px solid ${meta.color};">
        ${meta.short}
      </div>
      <div>
        <div class="tac-name">${teamName}</div>
        <div class="tac-seasons">${seasons}</div>
      </div>
    </div>

    <div class="stats-grid">
      <div class="stat-chip"><div class="val">${matches}</div><div class="lbl">Matches Played</div></div>
      <div class="stat-chip"><div class="val">${wins}</div><div class="lbl">Total Wins</div></div>
      <div class="stat-chip"><div class="val">${winPct}%</div><div class="lbl">Win Rate</div></div>
      <div class="stat-chip"><div class="val">${avgScore}</div><div class="lbl">Avg Score</div></div>
    </div>

    ${batters.length ? `
    <div class="players-section">
      <div class="players-title">Top Batters</div>
      ${batters.map(b => `
        <div class="player-row">
          <span class="player-name">${b.name}</span>
          <span class="player-stat">${b.runs.toLocaleString()} runs</span>
        </div>`).join("")}
    </div>` : ""}

    ${bowlers.length ? `
    <div class="players-section">
      <div class="players-title">Top Bowlers</div>
      ${bowlers.map(b => `
        <div class="player-row">
          <span class="player-name">${b.name}</span>
          <span class="player-stat">${b.wickets} wkts</span>
        </div>`).join("")}
    </div>` : ""}
  `;
}

// ─── Charts ───────────────────────────────────────────────────────
function renderCharts(t1, t2, s1, s2) {
  const chartDefaults = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: "#8892b0", font: { family: "Outfit", size: 12 } } },
    },
    scales: {
      x: { ticks: { color: "#8892b0", font: { family: "Outfit" } },
           grid: { color: "rgba(255,255,255,0.05)" } },
      y: { ticks: { color: "#8892b0", font: { family: "Outfit" } },
           grid: { color: "rgba(255,255,255,0.05)" } },
    },
  };

  // Destroy old
  if (winRateChart)  { winRateChart.destroy(); }
  if (avgScoreChart) { avgScoreChart.destroy(); }

  const m1 = getMeta(t1);
  const m2 = getMeta(t2);

  // Win rate horizontal bar chart
  winRateChart = new Chart(document.getElementById("winRateChart"), {
    type: "bar",
    data: {
      labels: [m1.short, m2.short],
      datasets: [{
        label: "Win Rate (%)",
        data: [
          (s1.win_rate * 100).toFixed(1),
          (s2.win_rate * 100).toFixed(1),
        ],
        backgroundColor: [`${m1.color}88`, `${m2.color}88`],
        borderColor:     [m1.color, m2.color],
        borderWidth: 2,
        borderRadius: 8,
      }],
    },
    options: {
      ...chartDefaults,
      indexAxis: 'y',
      plugins: { ...chartDefaults.plugins },
      scales: {
        x: { ...chartDefaults.scales.x, min: 0, max: 100 },
        y: { ...chartDefaults.scales.y },
      },
    },
  });

  // Avg score horizontal bar chart
  avgScoreChart = new Chart(document.getElementById("avgScoreChart"), {
    type: "bar",
    data: {
      labels: [m1.short, m2.short],
      datasets: [{
        label: "Average Score",
        data: [
          (s1.avg_score || 0).toFixed(1),
          (s2.avg_score || 0).toFixed(1),
        ],
        backgroundColor: [`${m1.color}88`, `${m2.color}88`],
        borderColor:     [m1.color, m2.color],
        borderWidth: 2,
        borderRadius: 8,
      }],
    },
    options: {
      ...chartDefaults,
      indexAxis: 'y',
      plugins: { ...chartDefaults.plugins },
      scales: {
        x: { ...chartDefaults.scales.x },
        y: { ...chartDefaults.scales.y },
      },
    },
  });
}

// ─── Confetti ─────────────────────────────────────────────────────
function spawnConfetti() {
  const container = document.getElementById("confetti");
  container.innerHTML = "";
  const colors = ["#f5a623","#7c3aed","#06b6d4","#22c55e","#f472b6","#fff"];
  for (let i = 0; i < 60; i++) {
    const p = document.createElement("div");
    p.className = "confetti-piece";
    p.style.cssText = `
      left:${Math.random()*100}%;
      background:${colors[Math.floor(Math.random()*colors.length)]};
      animation-duration:${1.2 + Math.random()*2}s;
      animation-delay:${Math.random()*0.8}s;
      width:${6+Math.random()*6}px;
      height:${8+Math.random()*8}px;
    `;
    container.appendChild(p);
  }
  setTimeout(() => { container.innerHTML = ""; }, 4000);
}

// ─── Init ─────────────────────────────────────────────────────────
loadMeta();
