import assert from "node:assert/strict";
import * as Core from "../src/core.mjs";

const {
  filterRecipes,
  findNearestByStrength,
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
    confidence: "высокая",
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
    confidence: "средняя",
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
    confidence: "высокая",
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
    confidence: "любая",
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
    confidence: "любая",
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
  hook: "Сухой чай с прозрачным можжевеловым шлейфом",
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
for (const query of ["ЛЕСНОЙ", "можжевеловым", "цедра", "сухая хвоя", "КУРАГА", "можжевельник", "белый чай"] ) {
  assert.equal(searchRecipes(searchableRecipes, query, inventoryById).length, 1, `search must index ${query}`);
}
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

assert.equal(
  selectRandomRecipe([recipes[0]], () => 0.99).id,
  "berry-light",
  "random selection must handle a one-item result",
);
assert.equal(selectRandomRecipe([], () => 0), null, "empty result has no random recipe");

console.log("core behavior ok");
