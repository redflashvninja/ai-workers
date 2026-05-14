/* ── AI Workers Frontend ─────────────────────────────────────────────── */

const API = '';  // same origin
// Polymarket APIs called directly from the browser (their server blocks datacenter IPs)
const GAMMA = 'https://gamma-api.polymarket.com';
const CLOB  = 'https://clob.polymarket.com';
let ws = null;
let wsReady = false;

// ── Navigation ────────────────────────────────────────────────────────
document.querySelectorAll('.nav-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    btn.classList.add('active');
    const sec = document.getElementById(`section-${btn.dataset.section}`);
    if (sec) sec.classList.add('active');
    if (btn.dataset.section === 'email') loadInbox();
    if (btn.dataset.section === 'calendar') loadEvents();
    if (btn.dataset.section === 'polymarket') loadTrending();
    if (btn.dataset.section === 'outreach') loadCalls();
  });
});

// ── Status ────────────────────────────────────────────────────────────
async function checkStatus() {
  try {
    const r = await fetch(`${API}/api/status`);
    const d = await r.json();
    const dot = document.getElementById('status-dot');
    const txt = document.getElementById('status-text');
    dot.className = 'status-dot ok';
    txt.textContent = d.model;
  } catch {
    document.getElementById('status-dot').className = 'status-dot err';
    document.getElementById('status-text').textContent = 'Server offline';
  }
}

// ── WebSocket chat ────────────────────────────────────────────────────
function connectWS() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  ws = new WebSocket(`${proto}://${location.host}/ws/chat`);

  ws.onopen = () => { wsReady = true; };
  ws.onclose = () => { wsReady = false; setTimeout(connectWS, 3000); };
  ws.onerror = () => { wsReady = false; };

  ws.onmessage = e => {
    const msg = JSON.parse(e.data);
    const msgs = document.getElementById('chat-messages');

    // Remove thinking indicator
    const thinking = msgs.querySelector('.thinking');
    if (thinking) thinking.remove();

    if (msg.type === 'thinking') {
      appendMsg(msgs, 'assistant thinking', '⏳ Thinking…');
    } else if (msg.type === 'response') {
      appendMsg(msgs, 'assistant', msg.content);
      document.getElementById('chat-send').disabled = false;
    } else if (msg.type === 'error') {
      appendMsg(msgs, 'assistant', `❌ Error: ${msg.content}`);
      document.getElementById('chat-send').disabled = false;
    }
    msgs.scrollTop = msgs.scrollHeight;
  };
}

function appendMsg(container, role, text) {
  const div = document.createElement('div');
  div.className = `chat-msg ${role}`;
  const bubble = document.createElement('div');
  bubble.className = 'chat-bubble';
  bubble.textContent = text;
  div.appendChild(bubble);
  container.appendChild(div);
}

function sendChat(msg) {
  if (!msg.trim() || !wsReady) return;
  const msgs = document.getElementById('chat-messages');
  appendMsg(msgs, 'user', msg);
  msgs.scrollTop = msgs.scrollHeight;
  document.getElementById('chat-input').value = '';
  document.getElementById('chat-send').disabled = true;
  ws.send(JSON.stringify({ message: msg }));
}

document.getElementById('chat-send').addEventListener('click', () => {
  sendChat(document.getElementById('chat-input').value);
});

document.getElementById('chat-input').addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(e.target.value); }
});

document.querySelectorAll('.example-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelector('[data-section="chat"]').click();
    setTimeout(() => sendChat(btn.dataset.prompt), 100);
  });
});

// ── Email ─────────────────────────────────────────────────────────────
async function loadInbox(query = 'in:inbox') {
  const el = document.getElementById('email-list');
  el.innerHTML = '<div class="list-placeholder">Loading…</div>';
  try {
    const r = await fetch(`${API}/api/email/inbox?q=${encodeURIComponent(query)}&n=30`);
    const emails = await r.json();
    if (!Array.isArray(emails) || emails.length === 0) {
      el.innerHTML = '<div class="empty-state">No emails found.</div>'; return;
    }
    el.innerHTML = '';
    emails.forEach(em => {
      const d = document.createElement('div');
      d.className = `email-item ${em.labelIds?.includes('UNREAD') ? 'unread' : ''}`;
      d.innerHTML = `
        <div class="email-from">${esc(em.from?.replace(/<.*>/, '').trim() || em.from)}</div>
        <div class="email-subject">${esc(em.subject)} <span class="email-snippet">— ${esc(em.snippet)}</span></div>
        <div class="email-date">${fmtDate(em.date)}</div>`;
      d.addEventListener('click', () => openThread(em.threadId, em.subject));
      el.appendChild(d);
    });
  } catch (e) { el.innerHTML = `<div class="empty-state">Error: ${e.message}</div>`; }
}

async function openThread(threadId, subject) {
  document.getElementById('thread-subject').textContent = subject;
  document.getElementById('thread-body').innerHTML = '<div class="list-placeholder">Loading…</div>';
  document.getElementById('thread-modal').style.display = 'flex';
  try {
    const r = await fetch(`${API}/api/email/message/${threadId}`);
    const msg = await r.json();
    const body = document.getElementById('thread-body');
    body.innerHTML = `<div class="thread-msg">
      <div class="thread-msg-header">From: ${esc(msg.from)} &nbsp;·&nbsp; ${esc(msg.date)}</div>
      <div class="thread-msg-body">${esc(msg.body || '(no body)')}</div>
    </div>`;
  } catch (e) {
    document.getElementById('thread-body').innerHTML = `<div class="empty-state">Error: ${e.message}</div>`;
  }
}

document.getElementById('email-search-btn').addEventListener('click', () => {
  loadInbox(document.getElementById('email-search-input').value || 'in:inbox');
});
document.getElementById('email-search-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') loadInbox(e.target.value || 'in:inbox');
});

document.getElementById('compose-btn').addEventListener('click', () => {
  document.getElementById('compose-modal').style.display = 'flex';
});
document.getElementById('compose-close').addEventListener('click', () => {
  document.getElementById('compose-modal').style.display = 'none';
});
document.getElementById('thread-close').addEventListener('click', () => {
  document.getElementById('thread-modal').style.display = 'none';
});

document.getElementById('compose-draft').addEventListener('click', async () => {
  await postEmail('/api/email/draft', 'Draft saved.');
});
document.getElementById('compose-send').addEventListener('click', async () => {
  await postEmail('/api/email/send', 'Email sent!');
});

async function postEmail(endpoint, successMsg) {
  const body = {
    to: document.getElementById('compose-to').value,
    subject: document.getElementById('compose-subject').value,
    body: document.getElementById('compose-body').value,
  };
  try {
    const r = await fetch(API + endpoint, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) });
    const d = await r.json();
    if (r.ok) { alert(successMsg); document.getElementById('compose-modal').style.display = 'none'; }
    else alert(`Error: ${JSON.stringify(d)}`);
  } catch (e) { alert(`Error: ${e.message}`); }
}

// ── Calendar ──────────────────────────────────────────────────────────
async function loadEvents() {
  const days = document.getElementById('cal-days').value;
  const el = document.getElementById('event-list');
  el.innerHTML = '<div class="list-placeholder">Loading…</div>';
  try {
    const r = await fetch(`${API}/api/calendar/events?days=${days}`);
    const events = await r.json();
    if (!Array.isArray(events) || events.length === 0) {
      el.innerHTML = '<div class="empty-state">No events in this range.</div>'; return;
    }
    el.innerHTML = '';
    events.forEach(ev => {
      const d = document.createElement('div');
      d.className = 'event-item';
      const start = ev.start ? new Date(ev.start) : null;
      const end = ev.end ? new Date(ev.end) : null;
      d.innerHTML = `
        <div class="event-time">
          ${start ? start.toLocaleDateString('en-US', {weekday:'short', month:'short', day:'numeric'}) : ''}
          <br>${start ? start.toLocaleTimeString('en-US', {hour:'2-digit', minute:'2-digit'}) : ''}
          ${end ? '– ' + end.toLocaleTimeString('en-US', {hour:'2-digit', minute:'2-digit'}) : ''}
        </div>
        <div class="event-info">
          <div class="event-title">${esc(ev.summary)}</div>
          <div class="event-meta">${ev.location ? '📍 ' + esc(ev.location) : ''}</div>
          ${ev.attendees?.length ? `<div class="event-attendees">👥 ${ev.attendees.map(a => esc(a.email)).join(', ')}</div>` : ''}
        </div>`;
      el.appendChild(d);
    });
  } catch (e) { el.innerHTML = `<div class="empty-state">Error: ${e.message}</div>`; }
}

document.getElementById('cal-days').addEventListener('change', loadEvents);

document.getElementById('new-event-btn').addEventListener('click', () => {
  document.getElementById('event-modal').style.display = 'flex';
});
document.getElementById('event-close').addEventListener('click', () => {
  document.getElementById('event-modal').style.display = 'none';
});

document.getElementById('event-create').addEventListener('click', async () => {
  const body = {
    summary: document.getElementById('ev-summary').value,
    start: document.getElementById('ev-start').value ? new Date(document.getElementById('ev-start').value).toISOString() : '',
    end: document.getElementById('ev-end').value ? new Date(document.getElementById('ev-end').value).toISOString() : '',
    location: document.getElementById('ev-location').value,
    description: document.getElementById('ev-desc').value,
    attendees: document.getElementById('ev-attendees').value.split(',').map(s => s.trim()).filter(Boolean),
  };
  try {
    const r = await fetch(`${API}/api/calendar/events`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) });
    const d = await r.json();
    if (r.ok) { alert('Event created!'); document.getElementById('event-modal').style.display = 'none'; loadEvents(); }
    else alert(`Error: ${JSON.stringify(d)}`);
  } catch (e) { alert(`Error: ${e.message}`); }
});

// ── Polymarket ────────────────────────────────────────────────────────
async function loadTrending() {
  await loadMarkets(`${GAMMA}/markets?active=true&closed=false&_sort=volume24hr&_order=DESC&limit=12`);
}

async function searchMarkets(q) {
  await loadMarkets(`${GAMMA}/markets?active=true&closed=false&_q=${encodeURIComponent(q)}&limit=24`);
}

async function loadMarkets(url) {
  const el = document.getElementById('market-grid');
  el.innerHTML = '<div class="list-placeholder">Loading…</div>';
  try {
    const r = await fetch(url);
    const raw = await r.json();
    // Gamma returns array directly; server proxy returns formatted objects
    const markets = Array.isArray(raw) ? raw : (raw.markets || raw.data || []);
    if (!markets.length) {
      el.innerHTML = '<div class="empty-state">No markets found.</div>'; return;
    }
    el.innerHTML = '';
    markets.forEach(m => {
      // Gamma field names differ from our server-formatted objects
      const question = m.question || m.title || '';
      const prices = m.outcomePrices || [];
      const rawYes = m.yes_price ?? (prices[0] != null ? prices[0] : null);
      const rawNo  = m.no_price  ?? (prices[1] != null ? prices[1] : null);
      const yp = rawYes != null ? (parseFloat(rawYes) * (parseFloat(rawYes) > 1 ? 1 : 100)).toFixed(0) + '%' : '—';
      const np = rawNo  != null ? (parseFloat(rawNo)  * (parseFloat(rawNo)  > 1 ? 1 : 100)).toFixed(0) + '%' : '—';
      const volRaw = m.volume24hr ?? m.volume_24hr ?? m.volume ?? 0;
      const vol = volRaw ? '$' + Number(volRaw).toLocaleString('en-US', {maximumFractionDigits:0}) : '';
      const endDate = m.endDate || m.end_date || m.endDateIso || '';
      const slug = m.slug || m.market_slug || '';
      const href = slug ? `https://polymarket.com/event/${slug}` : (m.url || '#');

      const card = document.createElement('a');
      card.className = 'market-card';
      card.href = href;
      card.target = '_blank';
      card.innerHTML = `
        <div class="market-q">${esc(question)}</div>
        <div class="market-prices">
          <span class="price-pill price-yes">YES ${yp}</span>
          <span class="price-pill price-no">NO ${np}</span>
        </div>
        <div class="market-meta">
          ${vol ? `<span class="market-vol">Vol: ${vol}</span>` : ''}
          ${endDate ? `<span>Ends ${fmtDate(endDate)}</span>` : ''}
        </div>`;
      el.appendChild(card);
    });
  } catch (e) { el.innerHTML = `<div class="empty-state">Error: ${e.message}</div>`; }
}

document.getElementById('market-search-btn').addEventListener('click', () => {
  const q = document.getElementById('market-search-input').value.trim();
  if (q) searchMarkets(q);
});
document.getElementById('market-search-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') { const q = e.target.value.trim(); if (q) searchMarkets(q); }
});
document.getElementById('market-trending-btn').addEventListener('click', loadTrending);

// ── Outreach ──────────────────────────────────────────────────────────
async function loadCalls() {
  const el = document.getElementById('calls-list');
  el.innerHTML = '<div class="list-placeholder">Loading…</div>';
  try {
    const r = await fetch(`${API}/api/outreach/calls`);
    const calls = await r.json();
    if (!Array.isArray(calls) || calls.length === 0) {
      el.innerHTML = '<div class="empty-state">No calls yet. Twilio may not be configured.</div>'; return;
    }
    el.innerHTML = '';
    calls.forEach(c => {
      const d = document.createElement('div');
      d.className = 'call-item';
      d.innerHTML = `
        <span class="call-status ${c.status}">${c.status}</span>
        <span>${esc(c.to)}</span>
        <span style="color:var(--text2)">${c.duration ? c.duration + 's' : ''}</span>
        <span style="color:var(--text3);margin-left:auto">${fmtDate(c.start_time)}</span>`;
      el.appendChild(d);
    });
  } catch (e) { el.innerHTML = `<div class="empty-state">Error: ${e.message}</div>`; }
}

document.getElementById('call-btn').addEventListener('click', async () => {
  const to = document.getElementById('call-to').value.trim();
  const message = document.getElementById('call-msg').value.trim();
  const res = document.getElementById('call-result');
  if (!to || !message) { alert('Enter a phone number and message.'); return; }
  res.className = 'result-box show';
  res.textContent = 'Initiating call…';
  try {
    const r = await fetch(`${API}/api/outreach/call`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({to, message}) });
    const d = await r.json();
    res.textContent = r.ok ? `✅ Call initiated — SID: ${d.sid}` : `❌ ${JSON.stringify(d)}`;
    if (r.ok) loadCalls();
  } catch (e) { res.textContent = `❌ ${e.message}`; }
});

document.getElementById('sms-btn').addEventListener('click', async () => {
  const to = document.getElementById('sms-to').value.trim();
  const body = document.getElementById('sms-body').value.trim();
  const res = document.getElementById('sms-result');
  if (!to || !body) { alert('Enter a phone number and message.'); return; }
  res.className = 'result-box show';
  res.textContent = 'Sending SMS…';
  try {
    const r = await fetch(`${API}/api/outreach/sms`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({to, body}) });
    const d = await r.json();
    res.textContent = r.ok ? `✅ SMS sent — SID: ${d.sid}` : `❌ ${JSON.stringify(d)}`;
  } catch (e) { res.textContent = `❌ ${e.message}`; }
});

// ── Dashboard ─────────────────────────────────────────────────────────
async function loadDashboard() {
  document.getElementById('dash-time').textContent = new Date().toLocaleString();

  // Emails
  try {
    const r = await fetch(`${API}/api/email/inbox?q=is:unread&n=5`);
    const emails = await r.json();
    const count = Array.isArray(emails) ? emails.length : 0;
    document.getElementById('stat-email').textContent = count + (count === 5 ? '+' : '');
    const el = document.getElementById('dash-emails');
    if (!Array.isArray(emails) || emails.length === 0) { el.innerHTML = '<div class="empty-state">Inbox clear.</div>'; }
    else {
      el.innerHTML = emails.slice(0, 5).map(em =>
        `<div style="padding:8px 0;border-bottom:1px solid var(--border);font-size:12px">
          <div style="font-weight:600">${esc(em.from?.replace(/<.*>/, '').trim() || em.from)}</div>
          <div style="color:var(--text2)">${esc(em.subject)}</div>
        </div>`
      ).join('');
    }
  } catch { document.getElementById('stat-email').textContent = '—'; }

  // Calendar
  try {
    const r = await fetch(`${API}/api/calendar/events?days=1`);
    const events = await r.json();
    const count = Array.isArray(events) ? events.length : 0;
    document.getElementById('stat-cal').textContent = count;
    const el = document.getElementById('dash-events');
    if (!Array.isArray(events) || events.length === 0) { el.innerHTML = '<div class="empty-state">No events today.</div>'; }
    else {
      el.innerHTML = events.slice(0, 5).map(ev => {
        const t = ev.start ? new Date(ev.start).toLocaleTimeString('en-US',{hour:'2-digit',minute:'2-digit'}) : '';
        return `<div style="padding:8px 0;border-bottom:1px solid var(--border);font-size:12px">
          <div style="font-weight:600">${esc(ev.summary)}</div>
          <div style="color:var(--text2)">${t}</div>
        </div>`;
      }).join('');
    }
  } catch { document.getElementById('stat-cal').textContent = '—'; }

  // Markets
  try {
    const r = await fetch(`${GAMMA}/markets?active=true&closed=false&_sort=volume24hr&_order=DESC&limit=5`);
    const raw = await r.json();
    const markets = Array.isArray(raw) ? raw : (raw.markets || raw.data || []);
    document.getElementById('stat-markets').textContent = markets.length;
    const el = document.getElementById('dash-markets');
    if (!markets.length) { el.innerHTML = '<div class="empty-state">No markets.</div>'; }
    else {
      el.innerHTML = markets.slice(0, 5).map(m => {
        const prices = m.outcomePrices || [];
        const rawYes = m.yes_price ?? (prices[0] != null ? prices[0] : null);
        const yp = rawYes != null ? (parseFloat(rawYes) * (parseFloat(rawYes) > 1 ? 1 : 100)).toFixed(0) + '%' : '—';
        const question = m.question || m.title || '';
        return `<div style="padding:8px 0;border-bottom:1px solid var(--border);font-size:12px;display:flex;justify-content:space-between;gap:8px">
          <div style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(question)}</div>
          <div style="color:var(--green);font-weight:700;white-space:nowrap">${yp}</div>
        </div>`;
      }).join('');
    }
  } catch { document.getElementById('stat-markets').textContent = '—'; }

  // Calls stat
  try {
    const r = await fetch(`${API}/api/outreach/calls?limit=20`);
    const calls = await r.json();
    document.getElementById('stat-calls').textContent = Array.isArray(calls) ? calls.filter(c => c.direction === 'outbound-api').length : '—';
  } catch { document.getElementById('stat-calls').textContent = '—'; }
}

// ── Nav card shortcuts ────────────────────────────────────────────────
document.getElementById('card-email').addEventListener('click', () => document.querySelector('[data-section="email"]').click());
document.getElementById('card-cal').addEventListener('click', () => document.querySelector('[data-section="calendar"]').click());

// ── Utilities ─────────────────────────────────────────────────────────
function esc(str) {
  if (!str) return '';
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function fmtDate(str) {
  if (!str) return '';
  try { return new Date(str).toLocaleDateString('en-US', {month:'short', day:'numeric'}); }
  catch { return str; }
}

// ── Init ──────────────────────────────────────────────────────────────
checkStatus();
connectWS();
loadDashboard();
setInterval(checkStatus, 30000);
