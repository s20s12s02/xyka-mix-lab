import assert from "node:assert/strict";
import * as Core from "../src/core.mjs";

const {
  filterRecipes,
  findNearestByStrength,
  migrateLegacyPantryState,
  normalizeState,
  searchRecipes,
  selectRandomRecipe,
} = Core;

const recipes = [
  {
    id: "berry-light",
    directions: ["berry"],
    strengthIndex: 3.2,
    strengthLabel: "Лёгкая",
    components: [
      { tobaccoId: "strawberry", percent: 60 },
      { tobaccoId: "melon", percent: 40 },
    ],
  },
  {
    id: "berry-medium",
    directions: ["berry"],
    strengthIndex: 5.4,
    strengthLabel: "Средняя",
    components: [
      { tobaccoId: "currant", percent: 50 },
      { tobaccoId: "strawberry", percent: 30 },
      { tobaccoId: "melon", percent: 20 },
    ],
  },
  {
    id: "tea-strong",
    directions: ["tea"],
    strengthIndex: 7.1,
    strengthLabel: "Крепкая",
    components: [
      { tobaccoId: "tea", percent: 50 },
      { tobaccoId: "currant", percent: 50 },
    ],
  },
];

assert.deepEqual(
  filterRecipes(recipes, {
    direction: "berry",
    strength: "Средняя",
    availableIds: new Set(["currant", "strawberry", "melon"]),
    componentCount: 3,
  }).map((recipe) => recipe.id),
  ["berry-medium"],
  "exact filters must keep only matching recipes",
);

assert.equal(
  filterRecipes(recipes, {
    direction: "berry",
    strength: "Средняя",
    availableIds: new Set(["strawberry", "melon"]),
    componentCount: "любое",
  }).length,
  0,
  "a recipe containing an unavailable tobacco must disappear",
);

assert.deepEqual(
  findNearestByStrength(recipes, {
    direction: "berry",
    strength: "Крепкая",
    availableIds: new Set(["currant", "strawberry", "melon"]),
  }).map((recipe) => recipe.id),
  ["berry-medium"],
  "nearest results must stay in the chosen direction",
);

const state = normalizeState(
  {
    availableIds: ["strawberry", "unknown"],
    favoriteIds: ["berry-light", "missing"],
    triedIds: ["berry-medium"],
    direction: "unknown",
    strength: "Очень крепкая",
  },
  {
    inventoryIds: new Set(["strawberry", "melon"]),
    recipeIds: new Set(["berry-light", "berry-medium"]),
    directions: new Set(["berry", "tea"]),
    strengths: new Set(["Лёгкая", "Средняя", "Крепкая"]),
  },
);
assert.deepEqual(state.availableIds, ["strawberry"]);
assert.deepEqual(state.favoriteIds, ["berry-light"]);
assert.deepEqual(state.triedIds, ["berry-medium"]);
assert.equal(state.direction, null);
assert.equal(state.strength, "любая");
assert.equal("confidence" in state, false, "confidence is not part of v2 state");

const migratedPantry = migrateLegacyPantryState(
  {
    availableIds: ["strawberry", "unknown"],
    favoriteIds: ["berry-light"],
    triedIds: ["berry-medium"],
    direction: "berry",
    strength: "Средняя",
  },
  {
    inventoryIds: new Set(["strawberry", "melon"]),
    recipeIds: new Set(["berry-light", "berry-medium"]),
    directions: new Set(["berry"]),
    strengths: new Set(["Лёгкая", "Средняя"]),
  },
);
assert.deepEqual(migratedPantry.availableIds, ["strawberry"]);
assert.deepEqual(migratedPantry.favoriteIds, [], "v1 favorites must reset during v2 migration");
assert.deepEqual(migratedPantry.triedIds, [], "v1 tried state must reset during v2 migration");
assert.equal(migratedPantry.direction, null, "v1 selection must not leak into the new session");
assert.equal(migratedPantry.strength, "любая");

const freshState = normalizeState(null, {
  inventoryIds: new Set(["strawberry", "melon"]),
  recipeIds: new Set(["berry-light", "berry-medium"]),
  directions: new Set(["berry", "drink", "unusual"]),
  strengths: new Set(["Лёгкая", "Средняя", "Крепкая"]),
});
assert.equal(freshState.direction, null, "a new session must wait for a direction choice");
assert.equal(freshState.strength, "любая", "a new session must default to all strengths");

const migratedTea = normalizeState({ direction: "tea", strength: "Лёгкая" }, {
  inventoryIds: new Set(["tea"]),
  recipeIds: new Set(),
  directions: new Set(["drink", "unusual"]),
  strengths: new Set(["Лёгкая", "Средняя", "Крепкая"]),
});
assert.equal(migratedTea.direction, "drink");
assert.equal(migratedTea.strength, "Лёгкая");

const migratedFloral = normalizeState({ direction: "floral", strength: "Средняя" }, {
  inventoryIds: new Set(["tea"]),
  recipeIds: new Set(),
  directions: new Set(["drink", "unusual"]),
  strengths: new Set(["Лёгкая", "Средняя", "Крепкая"]),
});
assert.equal(migratedFloral.direction, "unusual");

assert.deepEqual(
  filterRecipes(recipes, {
    direction: "berry",
    strength: "любая",
    availableIds: new Set(["currant", "strawberry", "melon"]),
  }).map((recipe) => recipe.id),
  ["berry-light", "berry-medium"],
  "Не важно must return every strength in the selected direction",
);

const searchableRecipes = [{
  id: "forest-tea",
  name: "Лесной настой",
  hook: { lead: "Лес заваривают вместо чая.", body: "Сухой чай с прозрачным можжевеловым шлейфом" },
  directionLabel: "Напитки",
  strengthLabel: "Средняя",
  whyItWorks: "Чай держит основу",
  dominantNotes: ["чай"],
  notePyramid: { top: ["цедра"], heart: ["белый чай"], base: ["сухая хвоя"] },
  taste: { start: "светлый лимон", middle: "чайный настой", aftertaste: "можжевельник" },
  components: [{ tobaccoId: "tea", brand: "Северный", name: "Белый чай" }],
}];
const inventoryById = new Map([["tea", {
  id: "tea",
  brand: "Северный",
  name: "Белый чай",
  hook: "Мягкий настой с курагой",
  profile: "Белый чай, фрукты и сухая курага",
  tags: ["настой", "курага"],
}]]);
for (const query of ["ЛЕСНОЙ", "цедра", "сухая хвоя", "КУРАГА", "можжевельник", "белый чай"] ) {
  assert.equal(searchRecipes(searchableRecipes, query, inventoryById).length, 1, `search must index ${query}`);
}
assert.equal(searchRecipes(searchableRecipes, "можжевеловым", inventoryById).length, 0, "deprecated recipe hook must not remain searchable");
assert.equal(searchRecipes(searchableRecipes, "лесной можжевельник", inventoryById).length, 1, "all words may come from different indexed fields");
assert.equal(searchRecipes(searchableRecipes, "лесной шоколад", inventoryById).length, 0, "all query words must match");

assert.equal(typeof Core.compositionSegments, "function", "composition ring segment builder is missing");
assert.deepEqual(
  Core.compositionSegments(
    [
      { tobaccoId: "currant", percent: 55 },
      { tobaccoId: "strawberry", percent: 30 },
      { tobaccoId: "melon", percent: 15 },
    ],
    new Map([
      ["currant", { visualColor: "#69506F" }],
      ["strawberry", { visualColor: "#D9676B" }],
      ["melon", { visualColor: "#D9A441" }],
    ]),
  ),
  [
    { tobaccoId: "currant", percent: 55, color: "#69506F", dasharray: "55 45", dashoffset: 0 },
    { tobaccoId: "strawberry", percent: 30, color: "#D9676B", dasharray: "30 70", dashoffset: -55 },
    { tobaccoId: "melon", percent: 15, color: "#D9A441", dasharray: "15 85", dashoffset: -85 },
  ],
  "ring segments must start at 12 o'clock, continue clockwise and preserve exact shares",
);

assert.equal(typeof Core.sectorGeometry, "function", "sector packing geometry builder is missing");
const sectors = Core.sectorGeometry([
  { tobaccoId: "currant", percent: 55 },
  { tobaccoId: "strawberry", percent: 30 },
  { tobaccoId: "melon", percent: 15 },
]);
assert.equal(sectors.reduce((sum, sector) => sum + sector.percent, 0), 100);
assert.deepEqual(sectors.map((sector) => sector.tobaccoId), ["currant", "strawberry", "melon"]);
assert.equal(sectors[0].startAngle, -90);
assert.equal(sectors.at(-1).endAngle, 270);
for (const sector of sectors) {
  const labelRadius = Math.hypot(sector.labelPoint.x - 150, sector.labelPoint.y - 150);
  const iconRadius = Math.hypot(sector.iconPoint.x - 150, sector.iconPoint.y - 150);
  assert.ok(labelRadius < 92, "percentage label must stay inside the capsule");
  assert.ok(iconRadius > 92, "ingredient icon must sit outside the filled capsule");
  assert.ok(sector.leaderStart && sector.leaderEnd, "outer icon needs a leader from its sector");
}

assert.equal(typeof Core.layerGeometry, "function", "layer packing geometry builder is missing");
const layers = Core.layerGeometry(
  {
    components: [
      { tobaccoId: "currant", percent: 40 },
      { tobaccoId: "strawberry", percent: 30 },
      { tobaccoId: "melon", percent: 30 },
    ],
    packing: {
      layout: {
        type: "layers",
        layers: [
          { order: 1, position: "у нагревателя", percent: 70, segments: [{ tobaccoId: "currant", percent: 40 }, { tobaccoId: "strawberry", percent: 30 }] },
          { order: 2, position: "дальше от нагревателя", percent: 30, segments: [{ tobaccoId: "melon", percent: 30 }] },
        ],
      },
    },
  },
);
assert.equal(layers.length, 2);
assert.equal(layers.reduce((sum, layer) => sum + layer.percent, 0), 100);
assert.deepEqual(layers[0].segments.map((segment) => segment.widthPercent), [40 / 70 * 100, 30 / 70 * 100]);

assert.equal(
  selectRandomRecipe([recipes[0]], () => 0.99).id,
  "berry-light",
  "random selection must handle a one-item result",
);
assert.equal(selectRandomRecipe([], () => 0), null, "empty result has no random recipe");

console.log("core behavior ok");
