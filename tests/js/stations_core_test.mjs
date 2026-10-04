import assert from "node:assert/strict";
import test from "node:test";

import { cheapestId, findNearest, parseEsNumber } from "../../app/static/js/stations-core.js";

const SAMPLE = [
  {
    IDEESS: "1",
    Rótulo: "Cerca",
    Dirección: "CALLE MAYOR 1",
    Municipio: "Madrid",
    Horario: "L-D: 24H",
    Latitud: "40,42",
    "Longitud (WGS84)": "-3,70",
    "Precio Gasolina 95 E5": "1,599",
    "Precio Gasoleo A": "1,499",
  },
  {
    IDEESS: "2",
    Rótulo: "Barata",
    Dirección: "CALLE BARATA 2",
    Municipio: "Madrid",
    Horario: "L-D: 24H",
    Latitud: "40,43",
    "Longitud (WGS84)": "-3,70",
    "Precio Gasolina 95 E5": "1,449",
    "Precio Gasoleo A": "",
  },
  {
    IDEESS: "3",
    Rótulo: "Media",
    Dirección: "CALLE MEDIA 3",
    Municipio: "Madrid",
    Horario: "",
    Latitud: "40,45",
    "Longitud (WGS84)": "-3,70",
    "Precio Gasolina 95 E5": "1,709",
    "Precio Gasoleo A": "1,399",
  },
  {
    IDEESS: "4",
    Rótulo: "Sin sitio",
    Dirección: "",
    Municipio: "Madrid",
    Horario: "",
    Latitud: "",
    "Longitud (WGS84)": "",
    "Precio Gasolina 95 E5": "1,000",
    "Precio Gasoleo A": "1,000",
  },
  {
    IDEESS: "5",
    Rótulo: "Lejos",
    Dirección: "BARCELONA",
    Municipio: "Barcelona",
    Horario: "",
    Latitud: "41,3874",
    "Longitud (WGS84)": "2,1686",
    "Precio Gasolina 95 E5": "1,200",
    "Precio Gasoleo A": "1,100",
  },
];

test("parseEsNumber", () => {
  assert.equal(parseEsNumber("1,589"), 1.589);
  assert.equal(parseEsNumber(""), null);
  assert.equal(parseEsNumber("no-es-numero"), null);
});

test("findNearest sorts inside the radius and skips gaps", () => {
  const near = findNearest(SAMPLE, 40.42, -3.7, "gasolina95", 2, 5);
  assert.deepEqual(near.map((item) => item.id), ["1", "2"]);
  assert.deepEqual(near.map((item) => item.distance_km), [0, 1.1]);

  const wide = findNearest(SAMPLE, 40.42, -3.7, "gasolina95", 10, 5);
  assert.deepEqual(wide.map((item) => item.id), ["1", "2", "3"]);
  assert.equal(cheapestId(wide), "2");
  assert.equal(cheapestId([]), null);

  const diesel = findNearest(SAMPLE, 40.42, -3.7, "diesel", 10, 5);
  assert.deepEqual(diesel.map((item) => item.id), ["1", "3"]);
});
