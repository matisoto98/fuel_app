export function readNumber(input) {
  const raw = input.value.trim().replace(/\s/g, "").replace(",", ".");
  if (raw === "") return 0;
  const value = Number(raw);
  return Number.isFinite(value) ? value : 0;
}

export function showError(id, message) {
  const el = document.getElementById(id);
  if (!el) return;
  el.hidden = !message;
  el.textContent = message || "";
}

export function clearErrors() {
  document.querySelectorAll(".field-error").forEach((el) => {
    el.hidden = true;
    el.textContent = "";
  });
}

export function placeApiError(message) {
  const text = message.toLowerCase();
  const rules = [
    ["tanque", "err-tank"],
    ["consumo", "err-consumption"],
    ["kilómetros por día", "err-km-day"],
    ["precio", "err-price"],
    ["año", "err-year"],
    ["matriculación", "err-registration"],
    ["kilómetros actuales", "err-current-km"],
    ["último mantenimiento", "err-maintenance"],
    ["fecha del último", "err-maintenance"],
  ];
  const match = rules.find(([hint]) => text.includes(hint));
  showError(match ? match[1] : "err-maintenance", message);
}

async function request(url, options) {
  let response;
  try {
    response = await fetch(url, options);
  } catch {
    throw new Error("No pudimos conectar. Comprueba tu conexión e inténtalo de nuevo.");
  }
  if (response.ok) return response;
  let message = "No pudimos completar la petición. Inténtalo de nuevo.";
  try {
    const data = await response.json();
    if (typeof data.detail === "string") message = data.detail;
  } catch {
    /* La respuesta no era JSON. */
  }
  throw new Error(message);
}

export async function getJson(url) {
  return (await request(url)).json();
}

export async function postJson(url, body) {
  const response = await request(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return response.json();
}

export { request };

export async function withBusy(button, label, action) {
  const previous = button.textContent;
  button.disabled = true;
  button.textContent = label;
  try {
    await action();
  } finally {
    button.disabled = false;
    button.textContent = previous;
  }
}
