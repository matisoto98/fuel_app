const KEY = "calculadora-combustible";

export function loadState() {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function saveState(state) {
  try {
    localStorage.setItem(KEY, JSON.stringify(state));
  } catch {
    /* El navegador puede bloquear el almacenamiento. La página sigue funcionando. */
  }
}

export function clearState() {
  try {
    localStorage.removeItem(KEY);
  } catch {
    /* Igual que al guardar: si falla, no rompemos la página. */
  }
}
