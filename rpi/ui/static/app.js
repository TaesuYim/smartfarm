// --- Configuration ---
const API_BASE = '/api';
let uiRefreshInterval = 5000;
let refreshTimer = null;
let envChartObj = null;
let soilChartObj = null;

// --- Tab Switching ---
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        e.target.classList.add('active');
        document.getElementById(e.target.dataset.target).classList.add('active');

        if(e.target.dataset.target === 'tab-graph' && !envChartObj) {
            loadGraphData();
        }
    });
});

// --- Time Update ---
setInterval(() => {
    const now = new Date();
    document.getElementById('current-time').innerText = now.toLocaleString('ko-KR');
}, 1000);

// --- Fetch Latest Data ---
async function fetchLatest() {
    try {
        const res = await fetch(`${API_BASE}/latest`);
        const data = await res.json();
        updateMonitoring(data);
        updateControlUI(data);
    } catch (e) {
        console.error('Failed to fetch latest data', e);
    }
}

function updateMonitoring(data) {
    const latest = data.latest || {};
    
    // Heartbeat
    const timeout = parseInt(data.settings?.heartbeat_timeout_sec || 10) * 1000;
    const now = new Date().getTime();
    
    ['arduino_node_1', 'arduino_node_2'].forEach((src, idx) => {
        const hb = data.heartbeat[src];
        const dot = document.querySelector(`#node${idx+1}-status .dot`);
        if(hb && hb.ts) {
            const last = new Date(hb.ts).getTime();
            if(now - last < timeout) {
                dot.classList.add('on');
            } else {
                dot.classList.remove('on');
            }
        } else {
            dot.classList.remove('on');
        }
    });

    // Env Sensors
    const envHtml = `
        <div class="metric-card"><div class="metric-icon">🌡️</div><div class="metric-label">온도(하부)</div><div class="metric-val">${latest.temp_pot_c !== null ? latest.temp_pot_c.toFixed(1)+'°C' : '—'}</div></div>
        <div class="metric-card"><div class="metric-icon">💧</div><div class="metric-label">습도(하부)</div><div class="metric-val">${latest.hum_pot_pct !== null ? latest.hum_pot_pct.toFixed(1)+'%' : '—'}</div></div>
        <div class="metric-card"><div class="metric-icon">🌡️</div><div class="metric-label">온도(상부)</div><div class="metric-val">${latest.temp_top_c !== null ? latest.temp_top_c.toFixed(1)+'°C' : '—'}</div></div>
        <div class="metric-card"><div class="metric-icon">💧</div><div class="metric-label">습도(상부)</div><div class="metric-val">${latest.hum_top_pct !== null ? latest.hum_top_pct.toFixed(1)+'%' : '—'}</div></div>
        <div class="metric-card"><div class="metric-icon">💨</div><div class="metric-label">CO₂</div><div class="metric-val">${latest.co2_ppm !== null ? latest.co2_ppm.toFixed(0)+'ppm' : '—'}</div></div>
        <div class="metric-card"><div class="metric-icon">☀️</div><div class="metric-label">PAR</div><div class="metric-val">${latest.par_w_m2 !== null ? latest.par_w_m2.toFixed(1)+'W/m²' : '—'}</div></div>
    `;
    document.getElementById('env-sensors').innerHTML = envHtml;

    // Soil Sensors
    let soilHtml = '';
    for(let i=1; i<=6; i++) {
        const val = latest[`soil_moisture_${i}_pct`];
        soilHtml += `<div class="metric-card"><div class="metric-icon">🌱</div><div class="metric-label">토양${i}</div><div class="metric-val">${val !== null && val !== undefined ? val.toFixed(1)+'%' : '—'}</div></div>`;
    }
    document.getElementById('soil-sensors').innerHTML = soilHtml;

    // Weather
    if(latest.weather_ts) {
        document.getElementById('weather-info').innerHTML = `
            🌡️ 외기온: <b>${latest.ta || '—'}°C</b> &nbsp; 💧 외습도: <b>${latest.hm || '—'}%</b><br>
            ☔ 강수: <b>${latest.rn || '—'}mm</b> &nbsp; 💨 풍속: <b>${latest.ws || '—'}m/s</b><br>
            ☀️ 일사: <b>${latest.icsr || '—'}MJ/m²</b> &nbsp; 🕐 일조: <b>${latest.ss || '—'}hr</b>
        `;
    }

    document.getElementById('last-update-monitor').innerText = `마지막 업데이트: ${latest.sensor_ts || '—'}`;

    // Settings sync
    if(data.settings) {
        if(!document.getElementById('s-ui-ref').dataset.userEdited) {
            document.getElementById('s-ui-ref').value = data.settings.ui_refresh_sec || 5;
            uiRefreshInterval = parseInt(data.settings.ui_refresh_sec || 5) * 1000;
        }
        if(!document.getElementById('s-meas').dataset.userEdited) document.getElementById('s-meas').value = data.settings.measurement_interval_sec || 1;
        if(!document.getElementById('s-hb').dataset.userEdited) document.getElementById('s-hb').value = data.settings.heartbeat_timeout_sec || 10;
    }
}

// --- Control Tab Logic ---
let isUpdatingUI = false;

function updateControlUI(data) {
    // Only update UI from DB if user isn't currently dragging sliders
    if(isUpdatingUI || document.querySelector('.tab-content.active').id !== 'tab-control') return;
    isUpdatingUI = true;
    const l = data.latest || {};
    
    const setVal = (id, val) => { const el = document.getElementById(id); if(el && !el.dataset.dragging) { el.value = val || 0; document.getElementById(id.replace('c-','v-')).innerText = (val||0)+'%'; }};
    const setCheck = (id, val) => { const el = document.getElementById(id); if(el) el.checked = !!val; };
    const setRadio = (name, val) => { const el = document.querySelector(`input[name="${name}"][value="${val || 'stop'}"]`); if(el) el.checked = true; };

    setVal('c-vent', l.vent_fan_pwm_pct);
    setVal('c-h1', l.heater_1_pwm_pct);
    setVal('c-h2', l.heater_2_pwm_pct);
    setVal('c-cf1', l.circ_fan_1_pwm_pct);
    setVal('c-cf2', l.circ_fan_2_pwm_pct);
    setVal('c-pump', l.pump_pwm_pct);
    setVal('c-br', l.led_brightness_pct);

    setCheck('c-mist', l.mist_on);
    setCheck('c-v1', l.valve_pot_1_on); setCheck('c-v2', l.valve_pot_2_on);
    setCheck('c-v3', l.valve_pot_3_on); setCheck('c-v4', l.valve_pot_4_on);
    setCheck('c-v5', l.valve_pot_5_on); setCheck('c-v6', l.valve_pot_6_on);
    setCheck('c-fog', l.valve_fog_on);

    setRadio('win1', l.window_1_cmd);
    setRadio('win2', l.window_2_cmd);
    setRadio('scr', l.shading_screen_cmd);

    if(l.led_r !== undefined) {
        const hex = "#" + (1 << 24 | l.led_r << 16 | l.led_g << 8 | l.led_b).toString(16).slice(1);
        document.getElementById('c-color').value = hex;
    }

    isUpdatingUI = false;
}

// Attach listeners for controls to send MQTT
let commandTimeout = null;

function gatherCommands() {
    const hex = document.getElementById('c-color').value;
    return {
        vent_fan_pwm_pct: parseInt(document.getElementById('c-vent').value),
        heater_1_pwm_pct: parseInt(document.getElementById('c-h1').value),
        heater_2_pwm_pct: parseInt(document.getElementById('c-h2').value),
        circ_fan_1_pwm_pct: parseInt(document.getElementById('c-cf1').value),
        circ_fan_2_pwm_pct: parseInt(document.getElementById('c-cf2').value),
        pump_pwm_pct: parseInt(document.getElementById('c-pump').value),
        led_brightness_pct: parseInt(document.getElementById('c-br').value),
        mist_on: document.getElementById('c-mist').checked ? 1 : 0,
        valve_pot_1_on: document.getElementById('c-v1').checked ? 1 : 0,
        valve_pot_2_on: document.getElementById('c-v2').checked ? 1 : 0,
        valve_pot_3_on: document.getElementById('c-v3').checked ? 1 : 0,
        valve_pot_4_on: document.getElementById('c-v4').checked ? 1 : 0,
        valve_pot_5_on: document.getElementById('c-v5').checked ? 1 : 0,
        valve_pot_6_on: document.getElementById('c-v6').checked ? 1 : 0,
        valve_fog_on: document.getElementById('c-fog').checked ? 1 : 0,
        window_1_cmd: document.querySelector('input[name="win1"]:checked').value,
        window_2_cmd: document.querySelector('input[name="win2"]:checked').value,
        shading_screen_cmd: document.querySelector('input[name="scr"]:checked').value,
        led_r: parseInt(hex.slice(1,3), 16),
        led_g: parseInt(hex.slice(3,5), 16),
        led_b: parseInt(hex.slice(5,7), 16),
    };
}

function showToast(id) {
    const t = document.getElementById(id);
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 3000);
}

async function sendCommand() {
    const cmds = gatherCommands();
    try {
        await fetch(`${API_BASE}/command`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({cmds})
        });
        showToast('cmd-toast');
    } catch(e) { console.error(e); }
}

function debounceCommand() {
    clearTimeout(commandTimeout);
    commandTimeout = setTimeout(sendCommand, 300);
}

// Bind Sliders
document.querySelectorAll('input[type="range"]').forEach(el => {
    el.addEventListener('input', (e) => {
        e.target.dataset.dragging = true;
        document.getElementById(e.target.id.replace('c-', 'v-')).innerText = e.target.value + '%';
    });
    el.addEventListener('change', (e) => {
        delete e.target.dataset.dragging;
        debounceCommand();
    });
});

// Bind Toggles & Radios & Color
document.querySelectorAll('input[type="checkbox"], input[type="radio"], input[type="color"]').forEach(el => {
    el.addEventListener('change', sendCommand);
});

// --- Graph Tab ---
document.getElementById('btn-load-graph').addEventListener('click', loadGraphData);

async function loadGraphData() {
    const minutes = document.getElementById('g-minutes').value || 60;
    const res = await fetch(`${API_BASE}/history?minutes=${minutes}`);
    const data = await res.json();

    const labels = data.map(d => new Date(d.ts).toLocaleTimeString('ko-KR'));
    
    const envDatasets = [
        { label: '온도(하부)', data: data.map(d=>d.temp_pot_c), borderColor: '#ef4444', tension: 0.2 },
        { label: '습도(하부)', data: data.map(d=>d.hum_pot_pct), borderColor: '#0ea5e9', tension: 0.2 },
        { label: 'CO2', data: data.map(d=>d.co2_ppm), borderColor: '#8b5cf6', yAxisID: 'y1', tension: 0.2 }
    ];

    const soilDatasets = [1,2,3,4,5,6].map(i => ({
        label: `토양${i}`, data: data.map(d=>d[`soil_moisture_${i}_pct`]),
        borderColor: `hsl(${i*40}, 70%, 50%)`, tension: 0.2
    }));

    if(envChartObj) envChartObj.destroy();
    if(soilChartObj) soilChartObj.destroy();

    Chart.defaults.color = '#94a3b8';
    const commonOpt = { responsive: true, maintainAspectRatio: false, animation: {duration: 0} };

    envChartObj = new Chart(document.getElementById('envChart'), {
        type: 'line', data: { labels, datasets: envDatasets },
        options: { ...commonOpt, scales: {
            y: { type: 'linear', position: 'left' },
            y1: { type: 'linear', position: 'right', grid: {drawOnChartArea: false} }
        }}
    });

    soilChartObj = new Chart(document.getElementById('soilChart'), {
        type: 'line', data: { labels, datasets: soilDatasets },
        options: commonOpt
    });
}

// --- Settings & Reset ---
['s-ui-ref', 's-meas', 's-hb'].forEach(id => {
    document.getElementById(id).addEventListener('input', e => e.target.dataset.userEdited = true);
});

document.getElementById('btn-save-settings').addEventListener('click', async () => {
    const payload = {
        ui_refresh_sec: document.getElementById('s-ui-ref').value,
        measurement_interval_sec: document.getElementById('s-meas').value,
        heartbeat_timeout_sec: document.getElementById('s-hb').value
    };
    await fetch(`${API_BASE}/settings`, {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    });
    uiRefreshInterval = parseInt(payload.ui_refresh_sec) * 1000;
    resetLoop();
    showToast('settings-toast');
    ['s-ui-ref', 's-meas', 's-hb'].forEach(id => delete document.getElementById(id).dataset.userEdited);
});

document.getElementById('btn-reset-arduino').addEventListener('click', async () => {
    if(!confirm("아두이노 전원을 리셋하시겠습니까?")) return;
    const stat = document.getElementById('reset-status');
    stat.innerText = '리셋 중...';
    try {
        await fetch(`${API_BASE}/arduino/reset`, {method: 'POST'});
        stat.innerText = '리셋 완료!';
    } catch(e) { stat.innerText = '리셋 실패'; }
    setTimeout(() => stat.innerText='', 3000);
});

// --- Loop ---
function resetLoop() {
    if(refreshTimer) clearInterval(refreshTimer);
    fetchLatest();
    refreshTimer = setInterval(fetchLatest, uiRefreshInterval);
}
resetLoop();
