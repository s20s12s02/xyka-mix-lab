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
  } = options;
  return recipes.filter((recipe) => {
    if (!recipeIsAvailable(recipe, availableIds)) return false;
    if (direction !== "любое" && !recipe.directions.includes(direction)) return false;
    if (strength !== "любая" && recipe.strengthLabel !== strength) return false;
    if (componentCount !== "любое" && recipe.components.length !== Number(componentCount)) return false;
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
  const migratedDirection = raw.direction === "tea"
    ? "drink"
    : (raw.direction === "floral" ? "unusual" : raw.direction);
  const availableIds = Array.isArray(raw.availableIds)
    ? filteredIds(raw.availableIds, catalogs.inventoryIds)
    : [...catalogs.inventoryIds];
  return {
    availableIds,
    favoriteIds: filteredIds(raw.favoriteIds, catalogs.recipeIds),
    triedIds: filteredIds(raw.triedIds, catalogs.recipeIds),
    direction: catalogs.directions.has(migratedDirection) ? migratedDirection : null,
    strength: raw.strength === "любая" || catalogs.strengths.has(raw.strength) ? (raw.strength || "любая") : "любая",
    componentCount: [2, 3, 4].includes(Number(raw.componentCount)) ? Number(raw.componentCount) : "любое",
    view: ["finder", "pantry", "favorites", "tried"].includes(raw.view) ? raw.view : "finder",
    query: typeof raw.query === "string" ? raw.query.slice(0, 80) : "",
  };
}

export function migrateLegacyPantryState(rawState, catalogs) {
  const fresh = normalizeState(null, catalogs);
  if (!rawState || typeof rawState !== "object" || !Array.isArray(rawState.availableIds)) return fresh;
  return {
    ...fresh,
    availableIds: filteredIds(rawState.availableIds, catalogs.inventoryIds),
  };
}

export function selectRandomRecipe(recipes, random = Math.random) {
  if (!recipes.length) return null;
  const index = Math.min(recipes.length - 1, Math.floor(random() * recipes.length));
  return recipes[index];
}

function normalizeSearchText(value) {
  return String(value || "")
    .toLocaleLowerCase("ru-RU")
    .replaceAll("ё", "е")
    .replace(/[^a-zа-я0-9]+/gi, " ")
    .trim();
}

function flattenText(value) {
  if (Array.isArray(value)) return value.flatMap(flattenText);
  if (value && typeof value === "object") return Object.values(value).flatMap(flattenText);
  return [value];
}

export function searchRecipes(recipes, query, inventoryById = new Map()) {
  const tokens = normalizeSearchText(query).split(/\s+/).filter(Boolean);
  if (!tokens.length) return recipes;
  return recipes.filter((recipe) => {
    const inventoryFields = recipe.components.flatMap((component) => {
      const item = inventoryById.get(component.tobaccoId) || {};
      return [item.brand, item.name, item.hook, item.profile, item.tags];
    });
    const haystack = [
      recipe.name,
      recipe.directionLabel,
      recipe.strengthLabel,
      recipe.whyItWorks,
      recipe.dominantNotes,
      recipe.notePyramid,
      recipe.taste,
      ...recipe.components.flatMap((component) => [component.brand, component.name]),
      ...inventoryFields,
    ];
    const normalizedHaystack = normalizeSearchText(flattenText(haystack).join(" "));
    return tokens.every((token) => normalizedHaystack.includes(token));
  });
}

export function availableStrengths(recipes, direction, availableIds) {
  const labels = new Set(
    filterRecipes(recipes, { direction, strength: "любая", availableIds }).map((recipe) => recipe.strengthLabel),
  );
  return STRENGTH_ORDER.filter((label) => labels.has(label));
}

export function compositionSegments(components, inventoryById) {
  let cumulative = 0;
  return [...components]
    .sort((first, second) => second.percent - first.percent)
    .map((component) => {
      const segment = {
        tobaccoId: component.tobaccoId,
        percent: component.percent,
        color: inventoryById.get(component.tobaccoId)?.visualColor || "#777777",
        dasharray: `${component.percent} ${100 - component.percent}`,
        dashoffset: cumulative === 0 ? 0 : -cumulative,
      };
      cumulative += component.percent;
      return segment;
    });
}

export function sectorGeometry(components) {
  const pointOnCircle = (radius, angle) => {
    const radians = angle * Math.PI / 180;
    return {
      x: 150 + radius * Math.cos(radians),
      y: 150 + radius * Math.sin(radians),
    };
  };
  let angle = -90;
  return components.map((component) => {
    const startAngle = angle;
    const endAngle = startAngle + component.percent * 3.6;
    const middleAngle = startAngle + (endAngle - startAngle) / 2;
    angle = endAngle;
    return {
      tobaccoId: component.tobaccoId,
      percent: component.percent,
      startAngle,
      endAngle,
      middleAngle,
      labelPoint: pointOnCircle(54, middleAngle),
      iconPoint: pointOnCircle(127, middleAngle),
      leaderStart: pointOnCircle(95, middleAngle),
      leaderEnd: pointOnCircle(108, middleAngle),
    };
  });
}

export function layerGeometry(recipe) {
  const layers = recipe?.packing?.layout?.type === "layers" ? recipe.packing.layout.layers : [];
  return layers.map((layer) => ({
    order: layer.order,
    position: layer.position,
    percent: layer.percent,
    heightPercent: layer.percent,
    segments: layer.segments.map((segment) => ({
      ...segment,
      widthPercent: layer.percent ? segment.percent / layer.percent * 100 : 0,
    })),
  }));
}

export { STRENGTH_ORDER };
