import { formatDays, formatKm, formatMoney, formatRefuel } from "./format.js";
import { clearErrors, placeApiError, postJson, readNumber, withBusy } from "./api.js";
import { clearMaintenanceList, initMaintenance } from "./maintenance.js";
import { initStations } from "./stations.js";
import { clearState, loadState, saveState } from "./storage.js";

const tank = document.getElementById("tank");
const consumption = document.getElementById("consumption");
const kmDay = document.getElementById("km-day");
const tiles = document.getElementById("tiles");
const resultsHint = document.getElementById("resultados-hint");

function collectState() {
  const items = {};
  document.querySelectorAll(".maint-item").forEach((block) => {
    items[block.dataset.key] = {
      lastDate: block.querySelector("[data-last-date]").value,
      lastKm: block.querySelector("[data-last-km]").value,
      intervalKm: block.querySelector("[data-interval-km]").value,
      intervalMonths: block.querySelector("[data-interval-months]").value,
    };
  });
  return {
    tank: tank.value,
    consumption: consumption.value,
    kmPerDay: kmDay.value,
    brand: document.getElementById("brand").value,
    model: document.getElementById("model").value,
    year: document.getElementById("year").value,
    registration: document.getElementById("registration").value,
    currentKm: document.getElementById("current-km").value,
    items,
  };
}

function applyState(state) {
  if (!state) return;
  tank.value = state.tank || "";
  consumption.value = state.consumption || "";
  kmDay.value = state.kmPerDay || "";
  document.getElementById("brand").value = state.brand || "";
  document.getElementById("model").value = state.model || "";
  document.getElementById("year").value = state.year || "";
  document.getElementById("registration").value = state.registration || "";
  document.getElementById("current-km").value = state.currentKm || "";
  document.querySelectorAll(".maint-item").forEach((block) => {
    const saved = state.items?.[block.dataset.key];
    if (!saved) return;
    block.querySelector("[data-last-date]").value = saved.lastDate || "";
    block.querySelector("[data-last-km]").value = saved.lastKm || "";
    block.querySelector("[data-interval-km]").value = saved.intervalKm || "";
    block.querySelector("[data-interval-months]").value = saved.intervalMonths || "";
  });
}

function showResults(data) {
  resultsHint.hidden = true;
  tiles.hidden = false;
  document.getElementById("out-range").textContent = formatKm(data.range_km);
  document.getElementById("out-days").textContent = formatDays(data.days_lasting);
  document.getElementById("out-cost").textContent = formatMoney(data.full_tank_cost);
  document.getElementById("out-date").textContent = formatRefuel(data.next_refuel_date);
}

applyState(loadState());
initStations();
initMaintenance();

for (const section of [document.getElementById("coche"), document.getElementById("mantenimiento")]) {
  section.addEventListener("input", () => saveState(collectState()));
  section.addEventListener("change", () => saveState(collectState()));
}

document.getElementById("calcular").addEventListener("click", () => {
  clearErrors();
  withBusy(document.getElementById("calcular"), "Calculando…", async () => {
    try {
      showResults(await postJson("/api/calcular", {
        tank_capacity_l: readNumber(tank),
        consumption_l_per_100km: readNumber(consumption),
        km_per_day: readNumber(kmDay),
        price_per_l: readNumber(document.getElementById("precio")),
      }));
    } catch (error) {
      placeApiError(error.message);
    }
  });
});

document.getElementById("borrar").addEventListener("click", () => {
  clearState();
  for (const input of document.querySelectorAll("#coche input, #mantenimiento input")) input.value = "";
  clearMaintenanceList();
  clearErrors();
});
