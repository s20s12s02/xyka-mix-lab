const STRENGTH_ORDER = ["Лёгкая", "Средне-лёгкая", "Средняя", "Крепкая", "Очень крепкая"];

function asSet(value) {
  return value instanceof Set ? value : new Set(value || []);
}

function recipeIsAvailable(recipe, availableIds) {
  const available = asSet(availableIds);
  return recipe.components.every((component) => available.has(component.tobaccoId));
}

export function filterRecipes(recipes, options = {}) {
  const {
    direction = "любое",
    strength = "любая",
    availableIds = new Set(),
    componentCount = "любое",
    confidence = "любая",
  } = options;
  return recipes.filter((recipe) => {
    if (!recipeIsAvailable(recipe, availableIds)) return false;
    if (direction !== "любое" && !recipe.directions.includes(direction)) return false;
    if (strength !== "любая" && recipe.strengthLabel !== strength) return false;
    if (componentCount !== "любое" && recipe.components.length !== Number(componentCount)) return false;
    if (confidence !== "любая" && recipe.confidence !== confidence) return false;
    return true;
  });
}

export function findNearestByStrength(recipes, options = {}) {
  const targetIndex = STRENGTH_ORDER.indexOf(options.strength);
  if (targetIndex < 0) return [];
  const candidates = filterRecipes(recipes, { ...options, strength: "любая" });
  if (!candidates.length) return [];
  const distances = candidates.map((recipe) => Math.abs(STRENGTH_ORDER.indexOf(recipe.strengthLabel) - targetIndex));
  const minimum = Math.min(...distances);
  return candidates.filter((_, index) => distances[index] === minimum);
}

function filteredIds(value, allowed) {
  if (!Array.isArray(value)) return [];
  return [...new Set(value.filter((id) => allowed.has(id)))];
}

export function normalizeState(rawState, catalogs) {
  const raw = rawState && typeof rawState === "object" ? rawState : {};
  const directions = [...catalogs.directions];
  const strengths = [...catalogs.strengths];
  const availableIds = Array.isArray(raw.availableIds)
    ? filteredIds(raw.availableIds, catalogs.inventoryIds)
    : [...catalogs.inventoryIds];
  return {
    availableIds,
    favoriteIds: filteredIds(raw.favoriteIds, catalogs.recipeIds),
    triedIds: filteredIds(raw.triedIds, catalogs.recipeIds),
    direction: catalogs.directions.has(raw.direction) ? raw.direction : directions[0],
    strength: catalogs.strengths.has(raw.strength) ? raw.strength : (catalogs.strengths.has("Средняя") ? "Средняя" : strengths[0]),
    componentCount: [2, 3, 4].includes(Number(raw.componentCount)) ? Number(raw.componentCount) : "любое",
    confidence: ["высокая", "средняя"].includes(raw.confidence) ? raw.confidence : "любая",
    view: ["finder", "pantry", "favorites", "tried"].includes(raw.view) ? raw.view : "finder",
    query: typeof raw.query === "string" ? raw.query.slice(0, 80) : "",
  };
}

export function selectRandomRecipe(recipes, random = Math.random) {
  if (!recipes.length) return null;
  const index = Math.min(recipes.length - 1, Math.floor(random() * recipes.length));
  return recipes[index];
}

export function searchRecipes(recipes, query) {
  const normalized = String(query || "").trim().toLocaleLowerCase("ru-RU");
  if (!normalized) return recipes;
  return recipes.filter((recipe) => {
    const haystack = [
      recipe.name,
      recipe.directionLabel,
      recipe.strengthLabel,
      recipe.whyItWorks,
      ...recipe.dominantNotes,
      ...recipe.components.flatMap((component) => [component.brand, component.name]),
    ].join(" ").toLocaleLowerCase("ru-RU");
    return haystack.includes(normalized);
  });
}

export function availableStrengths(recipes, direction, availableIds) {
  const labels = new Set(
    filterRecipes(recipes, { direction, strength: "любая", availableIds }).map((recipe) => recipe.strengthLabel),
  );
  return STRENGTH_ORDER.filter((label) => labels.has(label));
}

export { STRENGTH_ORDER };
