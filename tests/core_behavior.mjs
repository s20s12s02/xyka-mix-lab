import assert from "node:assert/strict";
import {
  filterRecipes,
  findNearestByStrength,
  normalizeState,
  selectRandomRecipe,
} from "../src/core.mjs";

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
assert.equal(state.direction, "berry");
assert.equal(state.strength, "Средняя");

assert.equal(
  selectRandomRecipe([recipes[0]], () => 0.99).id,
  "berry-light",
  "random selection must handle a one-item result",
);
assert.equal(selectRandomRecipe([], () => 0), null, "empty result has no random recipe");

console.log("core behavior ok");
