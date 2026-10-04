const FUEL_FIELDS = {
  gasolina95: "Precio Gasolina 95 E5",
  gasolina98: "Precio Gasolina 98 E5",
  diesel: "Precio Gasoleo A",
};

export function parseEsNumber(value) {
  const text = String(value ?? "").trim().replace(",", ".");
  if (!text) return null;
  const number = Number(text);
  return Number.isFinite(number) ? number : null;
}

export function haversineKm(lat1, lon1, lat2, lon2) {
  const radius = 6371;
  const rad = (degrees) => (degrees * Math.PI) / 180;
  const phi1 = rad(lat1);
  const phi2 = rad(lat2);
  const dphi = rad(lat2 - lat1);
  const dlambda = rad(lon2 - lon1);
  const a = Math.sin(dphi / 2) ** 2 + Math.cos(phi1) * Math.cos(phi2) * Math.sin(dlambda / 2) ** 2;
  return 2 * radius * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function round1(value) {
  const scaled = value * 10;
  const base = Math.trunc(scaled);
  const fraction = Math.abs(scaled - base);
  if (Math.abs(fraction - 0.5) > 1e-9) return Math.round(scaled) / 10;
  const even = base % 2 === 0 ? base : base + Math.sign(scaled);
  return even / 10;
}

export function findNearest(list, lat, lon, fuel, radiusKm = 10, limit = 5) {
  const priceKey = FUEL_FIELDS[fuel];
  const found = [];
  for (const station of list) {
    const slat = parseEsNumber(station.Latitud || "");
    const slon = parseEsNumber(station["Longitud (WGS84)"] || "");
    const price = parseEsNumber(station[priceKey] || "");
    if (slat === null || slon === null || price === null) continue;
    const distance = haversineKm(lat, lon, slat, slon);
    if (distance > radiusKm) continue;
    found.push({
      distance,
      station: {
        id: station.IDEESS,
        name: station["Rótulo"],
        address: station["Dirección"],
        town: station.Municipio,
        hours: station.Horario,
        lat: slat,
        lon: slon,
        price,
        distance_km: round1(distance),
      },
    });
  }
  found.sort((a, b) => a.distance - b.distance);
  return found.slice(0, limit).map((item) => item.station);
}

export function cheapestId(results) {
  if (!results.length) return null;
  return results.reduce((best, item) => (item.price < best.price ? item : best)).id;
}
