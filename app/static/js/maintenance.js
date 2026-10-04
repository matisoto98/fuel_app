import { formatLongDate, formatRemainingKm } from "./format.js";
import { clearErrors, placeApiError, postJson, readNumber, request, showError, withBusy } from "./api.js";

const STATUS = {
  vencido: "Vencido",
  pronto: "Pronto",
  ok: "Al día",
  sin_datos: "Falta dato",
};

const list = document.getElementById("lista-mantenimiento");

function optionalNumber(value) {
  const raw = value.trim().replace(",", ".");
  if (raw === "") return undefined;
  const number = Number(raw);
  return Number.isFinite(number) ? Math.trunc(number) : undefined;
}

function maintenanceBody() {
  const items = {};
  document.querySelectorAll(".maint-item").forEach((block) => {
    const entry = {};
    const lastDate = block.querySelector("[data-last-date]").value;
    const lastKm = optionalNumber(block.querySelector("[data-last-km]").value);
    const intervalKm = optionalNumber(block.querySelector("[data-interval-km]").value);
    const intervalMonths = optionalNumber(block.querySelector("[data-interval-months]").value);
    if (lastDate) entry.last_date = lastDate;
    if (lastKm !== undefined) entry.last_km = lastKm;
    if (intervalKm !== undefined) entry.interval_km = intervalKm;
    if (intervalMonths !== undefined) entry.interval_months = intervalMonths;
    if (Object.keys(entry).length) items[block.dataset.key] = entry;
  });
  return {
    brand: document.getElementById("brand").value.trim(),
    model: document.getElementById("model").value.trim(),
    year: Math.trunc(readNumber(document.getElementById("year"))),
    registration_date: document.getElementById("registration").value,
    current_km: Math.trunc(readNumber(document.getElementById("current-km"))),
    km_per_day: readNumber(document.getElementById("km-day")),
    items,
  };
}

function renderMaintenance(items) {
  list.replaceChildren();
  for (const item of items) {
    const row = document.createElement("article");
    row.className = "maint-row";
    const title = document.createElement("h3");
    title.textContent = item.label;
    const badge = document.createElement("span");
    badge.className = `badge badge-${item.status}`;
    badge.textContent = STATUS[item.status] || item.status;
    row.append(title, badge);
    if (item.due_date) {
      const when = document.createElement("p");
      when.textContent = formatLongDate(item.due_date);
      row.append(when);
    }
    if (item.km_remaining !== null && item.km_remaining !== undefined) {
      const remain = document.createElement("p");
      remain.textContent = formatRemainingKm(item.km_remaining);
      row.append(remain);
    }
    if (item.note) {
      const note = document.createElement("p");
      note.className = "hint";
      note.textContent = item.note;
      row.append(note);
    }
    list.append(row);
  }
}

function ready() {
  if (document.getElementById("registration").value) return true;
  showError("err-registration", "Indica la fecha de matriculación.");
  return false;
}

export function initMaintenance() {
  document.getElementById("ver-mantenimiento").addEventListener("click", () => {
    clearErrors();
    if (!ready()) return;
    withBusy(document.getElementById("ver-mantenimiento"), "Buscando…", async () => {
      try {
        renderMaintenance(await postJson("/api/mantenimiento", maintenanceBody()));
      } catch (error) {
        placeApiError(error.message);
      }
    });
  });

  document.getElementById("calendario").addEventListener("click", () => {
    clearErrors();
    if (!ready()) return;
    withBusy(document.getElementById("calendario"), "Buscando…", async () => {
      try {
        const response = await request("/api/mantenimiento/calendario", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(maintenanceBody()),
        });
        const url = URL.createObjectURL(await response.blob());
        const link = document.createElement("a");
        link.href = url;
        link.download = "mantenimiento.ics";
        document.body.append(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
      } catch (error) {
        placeApiError(error.message);
      }
    });
  });
}

export function clearMaintenanceList() {
  list.replaceChildren();
}
