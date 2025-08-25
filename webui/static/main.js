// Connect to Socket.IO if available, else fallback to HTTP requests
let socket = null;
if (typeof io === 'function') {
  try {
    socket = io({ transports: ["websocket", "polling"] });
  } catch (e) { socket = null; }
}

// UI controls (sliders and readouts)
const lin = document.getElementById('lin');
const ang = document.getElementById('ang');
const linVal = document.getElementById('linVal');
const angVal = document.getElementById('angVal');

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

// Button handlers set the current command; stop resets to zero
document.getElementById('btnUp').addEventListener('click', () => { curLin = +lin.value; curAng = 0; });
document.getElementById('btnDown').addEventListener('click', () => { curLin = -lin.value; curAng = 0; });
document.getElementById('btnLeft').addEventListener('click', () => { curLin = 0; curAng = +ang.value; });
document.getElementById('btnRight').addEventListener('click', () => { curLin = 0; curAng = -ang.value; });
document.getElementById('btnStop').addEventListener('click', () => { curLin = 0; curAng = 0; });

// Keyboard shortcuts for driving (arrows) and stop (space)
window.addEventListener('keydown', (e) => {
  const key = e.key;
  if (key === 'ArrowUp') { e.preventDefault(); curLin = +lin.value; curAng = 0; }
  else if (key === 'ArrowDown') { e.preventDefault(); curLin = -lin.value; curAng = 0; }
  else if (key === 'ArrowLeft') { e.preventDefault(); curLin = 0; curAng = +ang.value; }
  else if (key === 'ArrowRight') { e.preventDefault(); curLin = 0; curAng = -ang.value; }
  else if (key === ' ') { e.preventDefault(); curLin = 0; curAng = 0; }
});
