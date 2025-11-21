// Connect to Socket.IO if available, else fallback to HTTP requests
let socket = null;
if (typeof io === 'function') {
  try {
    // Werkzeug (Flask dev server) can't speak WebSockets, so stick to HTTP polling in dev.
    socket = io({ transports: ["polling"], upgrade: false });
  } catch (e) { socket = null; }
}

// UI controls (sliders and readouts)
const lin = document.getElementById('lin');
const ang = document.getElementById('ang');
const linVal = document.getElementById('linVal');
const angVal = document.getElementById('angVal');
const LIN_DEFAULT = Math.abs(parseFloat(lin.value)) || 0.3;
const ANG_DEFAULT = Math.abs(parseFloat(ang.value)) || 1.0;
const EPS = 1e-3;

// Current commanded velocities (sent at 10 Hz)
let curLin = 0.0;
let curAng = 0.0;

// Format numbers and emit a cmd_vel payload to the server
function fmt(n) { return (+n).toFixed(2); }
function send(linear, angular) {
  // Prefer Socket.IO when connected; otherwise use HTTP fallback
  if (socket && socket.connected) {
    try { socket.emit('cmd_vel', { linear, angular }); } catch (e) {}
  } else {
    const params = new URLSearchParams({ linear, angular });
    fetch(`/api/cmd?${params.toString()}`).catch(() => {});
  }
}

// Update slider readouts
function updateLabels() {
  linVal.textContent = fmt(lin.value);
  angVal.textContent = fmt(ang.value);
}

updateLabels();
lin.addEventListener('input', () => { updateLabels(); /* keep cur values as set by buttons/keys */ });
ang.addEventListener('input', () => { updateLabels(); /* keep cur values as set by buttons/keys */ });

// Periodically send the current command to avoid cmd_vel timeout
setInterval(() => {
  send(curLin, curAng);
}, 100); // 10 Hz

function readMagnitude(input, fallback) {
  const val = Math.abs(parseFloat(input.value));
  return val > EPS ? val : fallback;
}

function applyLinear(sign, magnitude) {
  const mag = magnitude !== undefined ? Math.abs(magnitude) : readMagnitude(lin, LIN_DEFAULT);
  curLin = sign * mag;
  send(curLin, curAng);
}

function applyAngular(sign, magnitude) {
  const mag = magnitude !== undefined ? Math.abs(magnitude) : readMagnitude(ang, ANG_DEFAULT);
  curAng = sign * mag;
  send(curLin, curAng);
}

function turnCommand(sign, keepLinear = false) {
  if (!keepLinear) {
    curLin = 0;
  } else if (Math.abs(curLin) < EPS) {
    curLin = readMagnitude(lin, LIN_DEFAULT);
  }
  applyAngular(sign);
}

// Button handlers set the current command; stop resets to zero
document.getElementById('btnUp').addEventListener('click', () => { applyLinear(+1); });
document.getElementById('btnDown').addEventListener('click', () => { applyLinear(-1); });
document.getElementById('btnLeft').addEventListener('click', (e) => {
  const keepLinear = e.shiftKey;
  turnCommand(+1, keepLinear);
});
document.getElementById('btnRight').addEventListener('click', (e) => {
  const keepLinear = e.shiftKey;
  turnCommand(-1, keepLinear);
});
document.getElementById('btnStop').addEventListener('click', () => { curLin = 0; curAng = 0; send(curLin, curAng); });

// Keyboard shortcuts for driving (arrows) and stop (space)
window.addEventListener('keydown', (e) => {
  const key = e.key;
  if (key === 'ArrowUp') {
    e.preventDefault();
    applyLinear(e.shiftKey && curLin < 0 ? -1 : +1);
  } else if (key === 'ArrowDown') {
    e.preventDefault();
    applyLinear(-1);
  } else if (key === 'ArrowLeft') {
    e.preventDefault();
    turnCommand(+1, e.shiftKey);
  } else if (key === 'ArrowRight') {
    e.preventDefault();
    turnCommand(-1, e.shiftKey);
  } else if (key === ' ') {
    e.preventDefault();
    curLin = 0;
    curAng = 0;
    send(curLin, curAng);
  }
});
