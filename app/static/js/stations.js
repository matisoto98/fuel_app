import { formatKm, formatMoney } from "./format.js";
import { getJson, showError, withBusy } from "./api.js";

const address = document.getElementById("direccion");
const price = document.getElementById("precio");
const stationsEl = document.getElementById("estaciones");
const stationsNote = document.getElementById("estaciones-nota");
const updatedEl = document.getElementById("actualizado");

let coords = null;
let priceFromStation = false;

function fuel() {
  return document.querySelector('input[name="combustible"]:checked').value;
}

function showSearchError(message) {
  stationsNote.textContent = "";
  if (message.toLowerCase().includes("dirección")) showError("err-address", message);
  else stationsNote.textContent = message;
}

function stationCard(station, cheapest) {
  const article = document.createElement("article");
  article.className = "station";

  const button = document.createElement("button");
  button.type = "button";
  button.className = "station-pick";
  button.setAttribute("aria-pressed", "false");

  const name = document.createElement("span");
  name.className = "station-name";
  name.textContent = station.name;
  const where = document.createElement("span");
  where.textContent = station.address;
  const cost = document.createElement("span");
  cost.className = "station-price";
  cost.textContent = formatMoney(station.price);
  const distance = document.createElement("span");
  distance.className = "hint";
  distance.textContent = formatKm(station.distance_km);
  button.append(name, where, cost, distance);
  if (cheapest) {
    const badge = document.createElement("span");
    badge.className = "badge badge-cheap";
    badge.textContent = "Más barata";
    button.append(badge);
  }
  button.addEventListener("click", () => {
    document.querySelectorAll(".station").forEach((el) => {
      const selected = el === article;
      el.classList.toggle("is-selected", selected);
      el.querySelector("button").setAttribute("aria-pressed", selected ? "true" : "false");
    });
    price.value = String(station.price);
    priceFromStation = true;
    showError("err-price", "");
  });

  const link = document.createElement("a");
  link.href = `https://www.google.com/maps/dir/?api=1&destination=${station.lat},${station.lon}`;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.textContent = "Cómo llegar";
  link.setAttribute("aria-label", `Cómo llegar a ${station.name}`);
  article.append(button, link);
  return article;
}

function renderStations(data) {
  stationsEl.replaceChildren();
  updatedEl.textContent = data.actualizado ? `Precios actualizados: ${data.actualizado}` : "";
  const list = data.gasolineras || [];
  if (!list.length) {
    stationsNote.textContent = "No hay gasolineras en 10 km. Prueba con otra dirección o escribe el precio.";
    return;
  }
  stationsNote.textContent = "";
  for (const station of list) stationsEl.append(stationCard(station, station.id === data.mas_barata_id));
}

async function searchStations() {
  const params = new URLSearchParams({
    lat: String(coords.lat),
    lon: String(coords.lon),
    combustible: fuel(),
    limite: "5",
  });
  renderStations(await getJson(`/api/gasolineras?${params}`));
}

async function searchAddress() {
  showError("err-address", "");
  stationsNote.textContent = "";
  const found = await getJson(`/api/ubicacion?${new URLSearchParams({ direccion: address.value.trim() })}`);
  coords = { lat: found.lat, lon: found.lon };
  await searchStations();
}

function useLocation(button) {
  if (!navigator.geolocation) {
    showSearchError("Este navegador no puede compartir la ubicación. Escribe una dirección.");
    return;
  }
  button.disabled = true;
  button.textContent = "Buscando…";
  showError("err-address", "");
  const restore = () => {
    button.disabled = false;
    button.textContent = "📍 Usar mi ubicación";
  };
  navigator.geolocation.getCurrentPosition(
    async (position) => {
      coords = { lat: position.coords.latitude, lon: position.coords.longitude };
      try {
        await searchStations();
      } catch (error) {
        showSearchError(error.message);
      } finally {
        restore();
      }
    },
    () => {
      restore();
      showSearchError("No pudimos usar tu ubicación. Escribe una dirección.");
    },
    { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 },
  );
}

export function initStations() {
  document.getElementById("form-direccion").addEventListener("submit", (event) => {
    event.preventDefault();
    withBusy(document.getElementById("buscar"), "Buscando…", async () => {
      try {
        await searchAddress();
      } catch (error) {
        showSearchError(error.message);
      }
    });
  });

  document.getElementById("gps").addEventListener("click", () => {
    useLocation(document.getElementById("gps"));
  });

  for (const input of document.querySelectorAll('input[name="combustible"]')) {
    input.addEventListener("change", () => {
      if (priceFromStation) {
        price.value = "";
        priceFromStation = false;
      }
      if (!coords) return;
      stationsNote.textContent = "Buscando…";
      searchStations().catch((error) => showSearchError(error.message));
    });
  }

  price.addEventListener("input", () => {
    priceFromStation = false;
  });
}
