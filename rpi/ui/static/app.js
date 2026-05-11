// ═══════════════════════════════════════════════════════
//  SFES Lab — Frontend Application
//  FastAPI backend + vanilla JS  |  1280×800 kiosk
// ═══════════════════════════════════════════════════════

const API = '/api';
let refreshMs = 2000;
let refreshTimer = null;
let chartEnv = null, chartSoil = null, chartPar = null;

// ─── Clock ───
function tickClock() {
    const d = new Date();
    const pad = n => String(n).padStart(2, '0');
    document.getElementById('clock').textContent =
        `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}
setInterval(tickClock, 1000);
tickClock();

// ─── Tab Switching ───
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
    });
});

// ─── Helpers ───
const fmt = (v, d = 1, u = '') => (v !== null && v !== undefined) ? Number(v).toFixed(d) + u : '—';
function showToast(id) {
    const t = document.getElementById(id);
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 2500);
}

async function fetchJson(url, options = {}) {
    const res = await fetch(url, options);
    if (!res.ok) {
        let message = `${res.status} ${res.statusText}`;
        try {
            const body = await res.json();
            message = body.detail || body.error || message;
        } catch (_) {
            // Keep the HTTP status message when the response is not JSON.
        }
        throw new Error(message);
    }
    return res.json();
}
const formatTime = (ts) => {
    if (!ts) return '—';
    const d = new Date(ts);
    if (isNaN(d)) return ts;
    const pad = n => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
};

// ═══════════════════════════════════════════════════════
//  MONITORING TAB
// ═══════════════════════════════════════════════════════

function renderMonitoring(data) {
    const L = data.latest || {};

    // ── Heartbeat dots ──
    const timeout = parseInt(data.settings?.heartbeat_timeout_sec || 10) * 1000;
    const now = Date.now();
    ['arduino_node_1', 'arduino_node_2'].forEach((src, i) => {
        const hb = data.heartbeat?.[src];
        const dot = document.getElementById('dot-node' + (i + 1));
        if (hb && hb.ts) {
            const age = now - new Date(hb.ts).getTime();
            dot.classList.toggle('online', age < timeout);
        } else {
            dot.classList.remove('online');
        }
    });

    // ── Environment sensors ──
    const envItems = [
        { icon: '🌡️', name: '온도(하부)', val: fmt(L.temp_pot_c, 1, '°C') },
        { icon: '💧', name: '습도(하부)', val: fmt(L.hum_pot_pct, 1, '%') },
        { icon: '🌡️', name: '온도(상부)', val: fmt(L.temp_top_c, 1, '°C') },
        { icon: '💧', name: '습도(상부)', val: fmt(L.hum_top_pct, 1, '%') },
        { icon: '💨', name: 'CO₂', val: fmt(L.co2_ppm, 0, ' ppm') },
        { icon: '☀️', name: 'PAR', val: fmt(L.par_w_m2, 1, ' W/m²') },
    ];
    document.getElementById('env-metrics').innerHTML = envItems.map(m =>
        `<div class="metric"><div class="metric-icon">${m.icon}</div><div class="metric-name">${m.name}</div><div class="metric-value">${m.val}</div></div>`
    ).join('');

    // ── Soil sensors ──
    let soilHtml = '';
    for (let i = 1; i <= 6; i++) {
        const v = L['soil_moisture_' + i + '_pct'];
        soilHtml += `<div class="metric"><div class="metric-icon">🌱</div><div class="metric-name">토양 ${i}</div><div class="metric-value">${fmt(v, 1, '%')}</div></div>`;
    }
    document.getElementById('soil-metrics').innerHTML = soilHtml;

    // ── Weather ──
    const wItems = [
        { label: '🌡️ 외기온', val: fmt(L.ta, 1, '°C') },
        { label: '💧 외습도', val: fmt(L.hm, 1, '%') },
        { label: '☔ 강수', val: fmt(L.rn, 1, ' mm') },
        { label: '💨 풍속', val: fmt(L.ws, 1, ' m/s') },
        { label: '☀️ 일사', val: fmt(L.icsr, 2, ' MJ') },
        { label: '🕐 일조', val: fmt(L.ss, 1, ' hr') },
    ];
    document.getElementById('weather-grid').innerHTML = wItems.map(w =>
        `<div class="weather-item"><span class="wi-label">${w.label}</span><span class="wi-val">${w.val}</span></div>`
    ).join('');
    document.getElementById('weather-time').textContent =
        L.weather_ts ? `날씨 업데이트: ${formatTime(L.weather_ts)}` : '';

    // ── Last update ──
    document.getElementById('last-update').textContent =
        '마지막 업데이트: ' + formatTime(L.sensor_ts);

    // ── Sync settings inputs (if user hasn't edited) ──
    const S = data.settings || {};
    syncSetting('s-refresh', S.ui_refresh_sec, 5);
    syncSetting('s-measure', S.measurement_interval_sec, 1);
    syncSetting('s-hb-timeout', S.heartbeat_timeout_sec, 10);
}

function syncSetting(id, val, fallback) {
    const el = document.getElementById(id);
    if (!el.dataset.edited) el.value = val || fallback;
}

// ═══════════════════════════════════════════════════════
//  CONTROL TAB
// ═══════════════════════════════════════════════════════

let updatingCtrl = false;

function renderControls(data) {
    if (updatingCtrl) return;

    updatingCtrl = true;
    const L = data.latest || {};

    const setToggle = (id, val) => { const el = document.getElementById(id); if (el) el.checked = !!val; };
    const setRadio = (name, val) => { const el = document.querySelector(`input[name="${name}"][value="${val || 'stop'}"]`); if (el) el.checked = true; };
    const setVal = (id, val) => {
        const slider = document.getElementById('c-' + id);
        const num = document.getElementById('v-' + id);
        // 사용자가 수정 중(dirty)이거나 드래그 중이면 서버 값으로 덮어쓰지 않음
        if (slider && !slider.dataset.dragging && !slider.dataset.dirty) slider.value = val || 0;
        if (num && !num.dataset.dirty) num.value = val || 0;
    };

    setVal('vent', L.vent_fan_pwm_pct);
    setVal('h1', L.heater_1_pwm_pct);
    setVal('h2', L.heater_2_pwm_pct);
    setVal('cf1', L.circ_fan_1_pwm_pct);
    setVal('cf2', L.circ_fan_2_pwm_pct);
    setVal('pump', L.pump_pwm_pct);
    setVal('br', L.led_brightness_pct);

    setToggle('c-mist', L.mist_on);
    for (let i = 1; i <= 6; i++) setToggle('c-v' + i, L['valve_pot_' + i + '_on']);
    setToggle('c-fog', L.valve_fog_on);

    setRadio('win1', L.window_1_cmd);
    setRadio('win2', L.window_2_cmd);
    setRadio('scr', L.shading_screen_cmd);

    if (L.led_r !== undefined && L.led_r !== null) {
        const hex = '#' + ((1 << 24) | (L.led_r << 16) | (L.led_g << 8) | L.led_b).toString(16).slice(1);
        document.getElementById('c-color').value = hex;
    }

    updatingCtrl = false;
}

// ── Gather all control values ──
function gatherCmds() {
    const hex = document.getElementById('c-color').value;
    return {
        vent_fan_pwm_pct: +document.getElementById('c-vent').value,
        heater_1_pwm_pct: +document.getElementById('c-h1').value,
        heater_2_pwm_pct: +document.getElementById('c-h2').value,
        circ_fan_1_pwm_pct: +document.getElementById('c-cf1').value,
        circ_fan_2_pwm_pct: +document.getElementById('c-cf2').value,
        pump_pwm_pct: +document.getElementById('c-pump').value,
        led_brightness_pct: +document.getElementById('c-br').value,
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
        led_r: parseInt(hex.slice(1, 3), 16),
        led_g: parseInt(hex.slice(3, 5), 16),
        led_b: parseInt(hex.slice(5, 7), 16),
    };
}

async function sendCommand() {
    try {
        await fetchJson(API + '/command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cmds: gatherCmds() })
        });
        showToast('cmd-toast');
        // 전송 성공 시 모든 dirty 플래그 해제 (이제 서버 값이 최신이므로 덮어써도 됨)
        document.querySelectorAll('#tab-control input').forEach(el => delete el.dataset.dirty);
    } catch (e) {
        console.error('Command send failed', e);
    }
}

let cmdTimer = null;
function debounceCmd() {
    clearTimeout(cmdTimer);
    cmdTimer = setTimeout(sendCommand, 300);
}

// Bind sliders and numeric inputs
document.querySelectorAll('#tab-control input[type="range"]').forEach(el => {
    el.addEventListener('input', e => {
        e.target.dataset.dragging = '1';
        e.target.dataset.dirty = '1';
        const numEl = document.getElementById(e.target.id.replace('c-', 'v-'));
        if (numEl) {
            numEl.value = e.target.value;
            numEl.dataset.dirty = '1';
        }
    });
    el.addEventListener('change', e => {
        delete e.target.dataset.dragging;
    });
});

document.querySelectorAll('.ctrl-num-input').forEach(el => {
    el.addEventListener('input', e => {
        e.target.dataset.dirty = '1';
        const sliderEl = document.getElementById(e.target.id.replace('v-', 'c-'));
        if (sliderEl) {
            sliderEl.value = e.target.value;
            sliderEl.dataset.dirty = '1';
        }
    });
});

// Bind toggles, radios, color (이것들은 누르자마자 즉시 전송되게 복구)
document.querySelectorAll('#tab-control input[type="checkbox"], #tab-control input[type="radio"], #tab-control input[type="color"]').forEach(el => {
    el.addEventListener('change', e => {
        // 즉시 전송되는 항목들도 dirty 플래그를 일시적으로 주어 렌더링 충돌 방지
        e.target.dataset.dirty = '1';
        sendCommand();
    });
});

// Bind send buttons (모든 전송 버튼들에 연결)
document.querySelectorAll('#btn-send-cmd, .btn-send-group').forEach(btn => {
    btn.addEventListener('click', sendCommand);
});

// ═══════════════════════════════════════════════════════
//  GRAPH TAB
// ═══════════════════════════════════════════════════════

// Default range: last 60 minutes
(function initGraphDefaults() {
    const now = new Date();
    const ago = new Date(now.getTime() - 60 * 60 * 1000);
    const toLocal = d => {
        const off = d.getTimezoneOffset();
        return new Date(d.getTime() - off * 60000).toISOString().slice(0, 16);
    };
    document.getElementById('g-start').value = toLocal(ago);
    document.getElementById('g-end').value = toLocal(now);
})();

document.getElementById('btn-query').addEventListener('click', loadGraphs);

async function loadGraphs() {
    const btn = document.getElementById('btn-query');
    const originalText = btn.innerText;
    btn.disabled = true;
    btn.innerText = '조회 중...';

    const start = document.getElementById('g-start').value;
    const end = document.getElementById('g-end').value;
    if (!start || !end) {
        btn.disabled = false;
        btn.innerText = originalText;
        return;
    }

    // datetime-local gives "YYYY-MM-DDTHH:MM" without seconds or timezone.
    // Append seconds and KST offset (+09:00) to match DB timestamps.
    const startISO = `${start}:00+09:00`;
    const endISO = `${end}:00+09:00`;


    let sensorData = [], weatherData = [];
    try {
        const [sRes, wRes] = await Promise.all([
            fetch(`${API}/history/sensors?start=${encodeURIComponent(startISO)}&end=${encodeURIComponent(endISO)}`),
            fetch(`${API}/history/weather?start=${encodeURIComponent(startISO)}&end=${encodeURIComponent(endISO)}`)
        ]);
        sensorData = await sRes.json();
        weatherData = await wRes.json();
    } catch (e) { console.error('Graph data fetch failed', e); }
    finally {
        btn.disabled = false;
        btn.innerText = originalText;
    }

    Chart.defaults.color = '#64748b';
    Chart.defaults.borderColor = 'rgba(255,255,255,0.05)';

    // ── Environment + Weather chart (dual Y-axis) ──
    if (chartEnv) chartEnv.destroy();
    
    chartEnv = new Chart(document.getElementById('chart-env'), {
        type: 'line',
        data: {
            datasets: [
                { label: '내부 온도 (°C)', data: sensorData.map(d => ({ x: d.ts, y: d.temp_pot_c })), borderColor: '#ef4444', borderWidth: 1.5, pointRadius: 0, tension: 0.3, yAxisID: 'y' },
                { label: '내부 습도 (%)', data: sensorData.map(d => ({ x: d.ts, y: d.hum_pot_pct })), borderColor: '#3b82f6', borderWidth: 1.5, pointRadius: 0, tension: 0.3, yAxisID: 'y' },
                { label: '외기 온도 (°C)', data: weatherData.map(d => ({ x: d.ts, y: d.ta })), borderColor: '#f97316', borderWidth: 1.5, borderDash: [4, 3], pointRadius: 0, tension: 0.3, yAxisID: 'y' },
                { label: '외기 습도 (%)', data: weatherData.map(d => ({ x: d.ts, y: d.hm })), borderColor: '#06b6d4', borderWidth: 1.5, borderDash: [4, 3], pointRadius: 0, tension: 0.3, yAxisID: 'y' },
                { label: 'CO₂ (ppm)', data: sensorData.map(d => ({ x: d.ts, y: d.co2_ppm })), borderColor: '#a855f7', borderWidth: 1.5, pointRadius: 0, tension: 0.3, yAxisID: 'y1' },
            ]
        },
        options: {
            animation: false,
            responsive: true, maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        tooltipFormat: 'yyyy-MM-dd HH:mm:ss',
                        displayFormats: {
                            minute: 'HH:mm',
                            hour: 'HH:mm',
                            day: 'MM/dd'
                        }
                    },
                    ticks: {
                        autoSkip: true,
                        maxRotation: 0,
                        font: { size: 10 }
                    }
                },
                y: { type: 'linear', position: 'left', title: { display: true, text: '온도(°C) / 습도(%)' } },
                y1: { type: 'linear', position: 'right', title: { display: true, text: 'CO₂ (ppm)' }, grid: { drawOnChartArea: false } }
            },
            plugins: { legend: { labels: { boxWidth: 12, font: { size: 11 } } } }
        }
    });

    // ── Soil moisture chart ──
    if (chartSoil) chartSoil.destroy();
    const soilColors = ['#22c55e', '#14b8a6', '#06b6d4', '#3b82f6', '#8b5cf6', '#ec4899'];
    chartSoil = new Chart(document.getElementById('chart-soil'), {
        type: 'line',
        data: {
            datasets: [1, 2, 3, 4, 5, 6].map((i, idx) => ({
                label: `토양 ${i}`,
                data: sensorData.map(d => ({ x: d.ts, y: d['soil_moisture_' + i + '_pct'] })),
                borderColor: soilColors[idx], borderWidth: 1.5, pointRadius: 0, tension: 0.3
            }))
        },
        options: {
            animation: false,
            responsive: true, maintainAspectRatio: false,
            scales: {
                x: {
                    type: 'time',
                    time: {
                        tooltipFormat: 'yyyy-MM-dd HH:mm:ss',
                        displayFormats: { minute: 'HH:mm', hour: 'HH:mm' }
                    }
                },
                y: { title: { display: true, text: '토양수분 (%)' } }
            },
            plugins: { legend: { labels: { boxWidth: 12, font: { size: 11 } } } }
        }
    });

    // ── PAR chart ──
    if (chartPar) chartPar.destroy();
    chartPar = new Chart(document.getElementById('chart-par'), {
        type: 'line',
        data: {
            datasets: [{
                label: 'PAR (W/m²)',
                data: sensorData.map(d => ({ x: d.ts, y: d.par_w_m2 })),
                borderColor: '#eab308', backgroundColor: 'rgba(234,179,8,0.08)',
                borderWidth: 1.5, pointRadius: 0, tension: 0.3, fill: true
            }]
        },
        options: {
            animation: false,
            responsive: true, maintainAspectRatio: false,
            scales: {
                x: {
                    type: 'time',
                    time: {
                        tooltipFormat: 'yyyy-MM-dd HH:mm:ss',
                        displayFormats: { minute: 'HH:mm', hour: 'HH:mm' }
                    }
                },
                y: { title: { display: true, text: 'PAR (W/m²)' } }
            },
            plugins: { legend: { labels: { boxWidth: 12, font: { size: 11 } } } }
        }
    });
}

// ═══════════════════════════════════════════════════════
//  SETTINGS TAB
// ═══════════════════════════════════════════════════════

['s-refresh', 's-measure', 's-hb-timeout'].forEach(id => {
    document.getElementById(id).addEventListener('input', e => { e.target.dataset.edited = '1'; });
});

document.getElementById('btn-save-settings').addEventListener('click', async () => {
    const payload = {
        ui_refresh_sec: document.getElementById('s-refresh').value,
        measurement_interval_sec: document.getElementById('s-measure').value,
        heartbeat_timeout_sec: document.getElementById('s-hb-timeout').value
    };
    try {
        await fetchJson(API + '/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        refreshMs = parseInt(payload.ui_refresh_sec) * 1000;
        startLoop();
        showToast('settings-toast');
        ['s-refresh', 's-measure', 's-hb-timeout'].forEach(id => delete document.getElementById(id).dataset.edited);
    } catch (e) { console.error('Settings save failed', e); }
});

// ═══════════════════════════════════════════════════════
//  ARDUINO POWER
// ═══════════════════════════════════════════════════════

document.getElementById('c-arduino-power').addEventListener('change', async (e) => {
    const isON = e.target.checked;
    if (!isON) {
        if (!confirm('아두이노 전원을 정말로 끄시겠습니까? 시스템이 작동을 멈춥니다.')) {
            e.target.checked = true; // 취소 시 토글 복구
            return;
        }
    }
    const msg = document.getElementById('reset-msg');
    msg.textContent = isON ? '전원 켜는 중...' : '전원 끄는 중...';
    try {
        const res = await fetch(API + '/arduino/power', { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ state: isON ? "on" : "off" })
        });
        msg.textContent = res.ok ? (isON ? '전원 켜짐' : '전원 꺼짐') : '명령 실패';
    } catch (err) { 
        msg.textContent = '명령 실패'; 
        e.target.checked = !isON; // 실패 시 토글 복구
    }
    setTimeout(() => { msg.textContent = ''; }, 3000);
});

// ═══════════════════════════════════════════════════════
//  DATA FETCH LOOP
// ═══════════════════════════════════════════════════════

async function fetchLatest() {
    try {
        const res = await fetch(API + '/latest');
        const data = await res.json();
        renderMonitoring(data);
        renderControls(data);

        // Update refresh interval from server
        if (data.settings?.ui_refresh_sec) {
            const newMs = parseInt(data.settings.ui_refresh_sec) * 1000;
            if (newMs !== refreshMs) {
                refreshMs = newMs;
                startLoop();
            }
        }
    } catch (e) { console.error('Fetch latest failed', e); }
}

function startLoop() {
    if (refreshTimer) clearInterval(refreshTimer);
    fetchLatest();
    refreshTimer = setInterval(fetchLatest, refreshMs);
}

// Start everything
startLoop(); // 데이터 루프부터 즉시 시작
