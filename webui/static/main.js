// Connect to Socket.IO server using websockets (fallback to polling)
const socket = io({ transports: ["websocket", "polling"] });

// UI controls (sliders and readouts)
const lin = document.getElementById('lin');
const ang = document.getElementById('ang');
const linVal = document.getElementById('linVal');
const angVal = document.getElementById('angVal');

// Format numbers and emit a cmd_vel payload to the server
function fmt(n) { return (+n).toFixed(2); }
function send(linear, angular) {
  socket.emit('cmd_vel', { linear, angular });
}

// Update slider readouts
function updateLabels() {
  linVal.textContent = fmt(lin.value);
  angVal.textContent = fmt(ang.value);
}

updateLabels();
lin.addEventListener('input', updateLabels);
ang.addEventListener('input', updateLabels);

// Button handlers for movement and stop
document.getElementById('btnUp').addEventListener('click', () => send(lin.value, 0));
document.getElementById('btnDown').addEventListener('click', () => send(-lin.value, 0));
document.getElementById('btnLeft').addEventListener('click', () => send(0, +ang.value));
document.getElementById('btnRight').addEventListener('click', () => send(0, -ang.value));
document.getElementById('btnStop').addEventListener('click', () => send(0, 0));

// Keyboard shortcuts for driving (arrows) and stop (space)
window.addEventListener('keydown', (e) => {
  const key = e.key;
  if (key === 'ArrowUp') { e.preventDefault(); send(lin.value, 0); }
  else if (key === 'ArrowDown') { e.preventDefault(); send(-lin.value, 0); }
  else if (key === 'ArrowLeft') { e.preventDefault(); send(0, +ang.value); }
  else if (key === 'ArrowRight') { e.preventDefault(); send(0, -ang.value); }
  else if (key === ' ') { e.preventDefault(); send(0, 0); }
});
