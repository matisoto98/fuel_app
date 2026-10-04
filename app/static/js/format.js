const num = new Intl.NumberFormat("es-ES", { maximumFractionDigits: 1, useGrouping: "always" });
const whole = new Intl.NumberFormat("es-ES", { maximumFractionDigits: 0, useGrouping: "always" });
const money = new Intl.NumberFormat("es-ES", { style: "currency", currency: "EUR" });
const refuelDate = new Intl.DateTimeFormat("es-ES", {
  weekday: "long",
  day: "numeric",
  month: "long",
});
const longDate = new Intl.DateTimeFormat("es-ES", {
  day: "numeric",
  month: "long",
  year: "numeric",
});

function parseISODate(iso) {
  const [year, month, day] = iso.split("-").map(Number);
  return new Date(year, month - 1, day);
}

export function formatKm(value) {
  return `${num.format(value)} km`;
}

export function formatDays(value) {
  const text = num.format(value);
  return `${text} ${Number(value) === 1 ? "día" : "días"}`;
}

export function formatMoney(value) {
  return money.format(value);
}

export function formatRefuel(iso) {
  return refuelDate.format(parseISODate(iso));
}

export function formatLongDate(iso) {
  return longDate.format(parseISODate(iso));
}

export function formatRemainingKm(value) {
  const text = whole.format(Math.abs(value));
  return value < 0 ? `pasados ${text} km` : `quedan ${text} km`;
}
