(() => {
  "use strict";

  const STORAGE_KEY = "xyka-mix-lab:v2";
  const LEGACY_STORAGE_KEY = "xyka-mix-lab:v1";
  const inventory = JSON.parse(document.getElementById("inventory-data").textContent);
  const recipes = JSON.parse(document.getElementById("recipes-data").textContent);
  const assets = JSON.parse(document.getElementById("asset-data").textContent);
  const inventoryById = new Map(inventory.map((item) => [item.id, item]));
  const recipeById = new Map(recipes.map((recipe) => [recipe.id, recipe]));

  const DIRECTION_LABELS = {
    dessert: "Десерты",
    fruit: "Фрукты",
    berry: "Ягоды",
    citrus: "Цитрус",
    drink: "Напитки",
    unusual: "Необычное",
  };
  const STRENGTH_META = {
    любая: { label: "Не важно", asset: "strength:any", tone: "any" },
    "Лёгкая": { label: "Лёгкая", asset: "strength:light", tone: "light" },
    "Средне-лёгкая": { label: "Средне-лёгкая", asset: "strength:medium-light", tone: "medium-light" },
    "Средняя": { label: "Средняя", asset: "strength:medium", tone: "medium" },
    "Крепкая": { label: "Крепкая", asset: "strength:strong", tone: "strong" },
  };
  const VIEW_TITLES = {
    finder: "MixLab — миксы для XYKA PRO",
    pantry: "Моя полка — MixLab",
    favorites: "Избранное — MixLab",
    tried: "Пробовал — MixLab",
  };
  const ICONS = {
    heart: '<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/></svg>',
    check: '<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M5 13l4 4L19 7"/></svg>',
  };

  const catalogs = {
    inventoryIds: new Set(inventory.map((item) => item.id)),
    recipeIds: new Set(recipes.map((recipe) => recipe.id)),
    directions: new Set(Object.keys(DIRECTION_LABELS)),
    strengths: new Set(recipes.map((recipe) => recipe.strengthLabel)),
  };
  let storageHealthy = true;
  let lastFocusedElement = null;
  let composingSearch = false;

  function readStoredState() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) return { state: JSON.parse(saved), legacy: false };
      const legacy = localStorage.getItem(LEGACY_STORAGE_KEY);
      return legacy ? { state: JSON.parse(legacy), legacy: true } : { state: null, legacy: false };
    } catch (error) {
      storageHealthy = false;
      return { state: null, legacy: false };
    }
  }

  const stored = readStoredState();
  let state = stored.legacy
    ? window.XykaCore.migrateLegacyPantryState(stored.state, catalogs)
    : window.XykaCore.normalizeState(stored.state, catalogs);
  if (stored.legacy && storageHealthy) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (error) {
      storageHealthy = false;
    }
  }

  const el = {
    storageNotice: document.getElementById("storage-notice"),
    directionStep: document.getElementById("direction-step"),
    directionOptions: document.getElementById("direction-options"),
    chosenDirection: document.getElementById("chosen-direction"),
    chosenDirectionIcon: document.getElementById("chosen-direction-icon"),
    chosenDirectionLabel: document.getElementById("chosen-direction-label"),
    changeDirection: document.getElementById("change-direction"),
    strengthStep: document.getElementById("strength-step"),
    strengthOptions: document.getElementById("strength-options"),
    randomButton: document.getElementById("random-button"),
    searchInput: document.getElementById("search-input"),
    clearSearch: document.getElementById("clear-search"),
    componentFilter: document.getElementById("component-filter"),
    resultsPanel: document.getElementById("results-panel"),
    resultsSummary: document.getElementById("results-summary"),
    exactResults: document.getElementById("exact-results"),
    pantryList: document.getElementById("pantry-list"),
    pantryCount: document.getElementById("pantry-count"),
    restorePantry: document.getElementById("restore-pantry"),
    favoriteResults: document.getElementById("favorite-results"),
    triedResults: document.getElementById("tried-results"),
    favoriteCount: document.getElementById("favorite-count"),
    triedCount: document.getElementById("tried-count"),
    drawer: document.getElementById("recipe-drawer"),
    recipeDetail: document.getElementById("recipe-detail"),
    live: document.getElementById("live-region"),
  };

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
  }

  function replaceTrustedMarkup(target, markup) {
    // Every data-derived text value is escaped before reaching this internal template renderer.
    const range = document.createRange();
    range.selectNode(target);
    target.replaceChildren(range.createContextualFragment(markup));
  }

  function announce(message) {
    el.live.textContent = "";
    window.setTimeout(() => { el.live.textContent = message; }, 20);
  }

  function saveState() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
      storageHealthy = true;
    } catch (error) {
      storageHealthy = false;
    }
    renderStorageNotice();
  }

  function renderStorageNotice() {
    el.storageNotice.hidden = storageHealthy;
    if (!storageHealthy) el.storageNotice.textContent = "Изменения сохранятся только до закрытия вкладки.";
  }

  function availableSet() {
    return new Set(state.availableIds);
  }

  function exactRecipes() {
    if (!state.direction) return [];
    const filtered = window.XykaCore.filterRecipes(recipes, {
      direction: state.direction,
      strength: state.strength,
      availableIds: availableSet(),
      componentCount: state.componentCount,
    });
    return window.XykaCore.searchRecipes(filtered, state.query, inventoryById);
  }

  function renderSelection() {
    const hasDirection = Boolean(state.direction);
    el.directionStep.hidden = hasDirection;
    el.chosenDirection.hidden = !hasDirection;
    el.strengthStep.hidden = !hasDirection;
    el.resultsPanel.hidden = !hasDirection;
    if (!hasDirection) return;
    el.chosenDirectionLabel.textContent = DIRECTION_LABELS[state.direction];
    el.chosenDirectionIcon.src = assets[`direction:${state.direction}`];
  }

  function renderDirections() {
    replaceTrustedMarkup(el.directionOptions, Object.entries(DIRECTION_LABELS).map(([id, label]) => `
      <button type="button" class="direction-option" data-direction="${id}">
        <span class="direction-art"><img src="${assets[`direction:${id}`]}" alt=""></span>
        <strong>${escapeHtml(label)}</strong><span>Выбрать</span>
      </button>
    `).join(""));
  }

  function renderStrengths() {
    if (!state.direction) return;
    const availableLabels = window.XykaCore.availableStrengths(recipes, state.direction, availableSet());
    const labels = ["любая", ...availableLabels.filter((label) => STRENGTH_META[label])];
    if (!labels.includes(state.strength)) state.strength = "любая";
    replaceTrustedMarkup(el.strengthOptions, labels.map((label) => {
      const meta = STRENGTH_META[label];
      const count = window.XykaCore.filterRecipes(recipes, {
        direction: state.direction,
        strength: label,
        availableIds: availableSet(),
        componentCount: "любое",
      }).length;
      return `<button type="button" class="strength-option tone-${meta.tone}${state.strength === label ? " active" : ""}" data-strength="${escapeHtml(label)}" aria-pressed="${state.strength === label}" aria-label="${escapeHtml(meta.label)}, ${count} ${plural(count, "микс", "микса", "миксов")}">
        <img src="${assets[meta.asset]}" alt=""><strong>${escapeHtml(meta.label)}</strong><small>${count}</small>
      </button>`;
    }).join(""));
  }

  function compositionVisual(recipe, size = "card") {
    const segments = window.XykaCore.compositionSegments(recipe.components, inventoryById);
    const circles = segments.map((segment) => `<circle cx="50" cy="50" r="44" pathLength="100" fill="none" stroke="${segment.color}" stroke-width="7" stroke-dasharray="${segment.dasharray}" stroke-dashoffset="${segment.dashoffset}" transform="rotate(-90 50 50)"/>`).join("");
    const count = recipe.components.length;
    const icons = recipe.components.map((component, index) => `<img class="mix-ingredient mix-${count}-${index + 1}" src="${assets[inventoryById.get(component.tobaccoId).iconKey]}" alt="">`).join("");
    return `<div class="composition-visual ${size}">
      <svg class="composition-ring" viewBox="0 0 100 100" aria-hidden="true"><circle cx="50" cy="50" r="44" fill="none" stroke="var(--ring-track)" stroke-width="7"/>${circles}</svg>
      <div class="mix-collage" aria-hidden="true">${icons}</div>
    </div>`;
  }

  function strengthBadge(recipe) {
    const meta = STRENGTH_META[recipe.strengthLabel] || STRENGTH_META["Средняя"];
    return `<span class="strength-badge tone-${meta.tone}"><img src="${assets[meta.asset]}" alt=""><span>${escapeHtml(recipe.strengthLabel)}</span></span>`;
  }

  function componentRows(recipe, detailed = false) {
    return recipe.components.map((component) => {
      const item = inventoryById.get(component.tobaccoId);
      return `<div class="component-row${detailed ? " detailed" : ""}" style="--ingredient:${item.visualColor}">
        <img src="${assets[item.iconKey]}" alt=""><div class="component-copy"><span><b>${escapeHtml(item.brand)}</b> — ${escapeHtml(item.name)}</span>${detailed ? `<small>${escapeHtml(item.hook)}</small>` : ""}<i style="--share:${component.percent}%;--ingredient:${item.visualColor}"></i></div>
        <strong>${component.percent}%${detailed ? ` <small>${String(component.grams.toFixed(1)).replace(".", ",")} г</small>` : ""}</strong>
      </div>`;
    }).join("");
  }

  function recipeCard(recipe) {
    const favorites = new Set(state.favoriteIds);
    const tried = new Set(state.triedIds);
    return `<article class="recipe-card" data-recipe-card="${escapeHtml(recipe.id)}">
      <button type="button" class="recipe-card-button" data-recipe-open="${escapeHtml(recipe.id)}" aria-label="Открыть микс ${escapeHtml(recipe.name)}">
        <div class="card-visual">${compositionVisual(recipe)}</div>
        <div class="card-copy"><div class="recipe-topline">${strengthBadge(recipe)}</div>
          <h3 class="recipe-title">${escapeHtml(recipe.name)}</h3><div class="component-list">${componentRows(recipe)}</div>
        </div>
      </button>
      <div class="card-actions"><button type="button" class="icon-button favorite${favorites.has(recipe.id) ? " active" : ""}" data-favorite="${escapeHtml(recipe.id)}" aria-pressed="${favorites.has(recipe.id)}" aria-label="${favorites.has(recipe.id) ? "Убрать из избранного" : "Добавить в избранное"}">${ICONS.heart}</button>
      <button type="button" class="icon-button${tried.has(recipe.id) ? " active" : ""}" data-tried="${escapeHtml(recipe.id)}" aria-pressed="${tried.has(recipe.id)}" aria-label="${tried.has(recipe.id) ? "Убрать отметку пробовал" : "Отметить как пробовал"}">${ICONS.check}</button></div>
    </article>`;
  }

  function emptyState(title, text) {
    return `<div class="empty-state"><strong>${escapeHtml(title)}</strong><span>${escapeHtml(text)}</span></div>`;
  }

  function plural(number, one, few, many) {
    const mod10 = number % 10;
    const mod100 = number % 100;
    if (mod10 === 1 && mod100 !== 11) return one;
    if (mod10 >= 2 && mod10 <= 4 && !(mod100 >= 12 && mod100 <= 14)) return few;
    return many;
  }

  function renderResults() {
    if (!state.direction) return;
    const exact = exactRecipes();
    const strengthText = state.strength === "любая" ? "любая крепость" : state.strength.toLocaleLowerCase("ru-RU");
    el.resultsSummary.textContent = `${DIRECTION_LABELS[state.direction]}, ${strengthText}. Найдено ${exact.length}.`;
    el.clearSearch.hidden = !state.query;
    replaceTrustedMarkup(el.exactResults, exact.length ? exact.map(recipeCard).join("") : emptyState("Совпадений нет", "Очистите поиск, верните ингредиенты на полку или ослабьте точные фильтры."));
  }

  function renderPantry() {
    const available = availableSet();
    const groups = new Map();
    inventory.forEach((item) => {
      if (!groups.has(item.brand)) groups.set(item.brand, []);
      groups.get(item.brand).push(item);
    });
    replaceTrustedMarkup(el.pantryList, [...groups.entries()].map(([brand, items]) => `<section class="pantry-group"><h2>${escapeHtml(brand)}</h2><div class="pantry-items">${items.map((item) => `<article class="pantry-item">
      <img src="${assets[item.iconKey]}" alt=""><div><strong>${escapeHtml(item.name)}</strong><p>${escapeHtml(item.hook)}</p><span>${escapeHtml(item.strengthLabel)}</span></div>
      <label class="switch"><input type="checkbox" data-pantry-id="${escapeHtml(item.id)}" ${available.has(item.id) ? "checked" : ""} aria-label="${available.has(item.id) ? "Есть на полке" : "Закончился"}: ${escapeHtml(item.name)}"><span></span></label>
    </article>`).join("")}</div></section>`).join(""));
    el.pantryCount.textContent = `${available.size}/${inventory.length}`;
  }

  function renderSavedViews() {
    const available = availableSet();
    const activeRecipes = (ids) => ids.map((id) => recipeById.get(id)).filter(Boolean).filter((recipe) => recipe.components.every((component) => available.has(component.tobaccoId)));
    const favorites = activeRecipes(state.favoriteIds);
    const tried = activeRecipes(state.triedIds);
    replaceTrustedMarkup(el.favoriteResults, favorites.length ? favorites.map(recipeCard).join("") : emptyState("Пока пусто", "Добавьте понравившийся микс сердечком на карточке."));
    replaceTrustedMarkup(el.triedResults, tried.length ? tried.map(recipeCard).join("") : emptyState("Записей пока нет", "После сессии отметьте микс галочкой."));
    el.favoriteCount.textContent = state.favoriteIds.length;
    el.triedCount.textContent = state.triedIds.length;
  }

  function renderNavigation() {
    document.querySelectorAll("[data-view-panel]").forEach((panel) => { panel.hidden = panel.dataset.viewPanel !== state.view; });
    document.querySelectorAll(".bottom-nav [data-view]").forEach((button) => {
      const active = button.dataset.view === state.view;
      button.classList.toggle("active", active);
      if (active) button.setAttribute("aria-current", "page"); else button.removeAttribute("aria-current");
    });
    document.title = VIEW_TITLES[state.view];
  }

  function renderAll() {
    renderStorageNotice();
    renderDirections();
    renderSelection();
    renderStrengths();
    renderResults();
    renderPantry();
    renderSavedViews();
    renderNavigation();
    el.searchInput.value = state.query;
    el.componentFilter.value = String(state.componentCount);
  }

  function setView(view) {
    state.view = view;
    saveState();
    renderNavigation();
    if (view === "pantry") renderPantry();
    if (view === "favorites" || view === "tried") renderSavedViews();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function toggleSaved(key, recipeId) {
    const values = new Set(state[key]);
    const adding = !values.has(recipeId);
    if (adding) values.add(recipeId); else values.delete(recipeId);
    state[key] = [...values];
    saveState();
    renderResults();
    renderSavedViews();
    if (!el.drawer.hidden) renderRecipeDetail(recipeId);
    announce(adding ? "Микс отмечен" : "Отметка снята");
  }

  function polarPoint(radius, angle) {
    const radians = angle * Math.PI / 180;
    return { x: 150 + radius * Math.cos(radians), y: 150 + radius * Math.sin(radians) };
  }

  function sectorPath(sector) {
    const start = polarPoint(92, sector.startAngle);
    const end = polarPoint(92, sector.endAngle);
    const largeArc = sector.endAngle - sector.startAngle > 180 ? 1 : 0;
    return `M 150 150 L ${start.x.toFixed(3)} ${start.y.toFixed(3)} A 92 92 0 ${largeArc} 1 ${end.x.toFixed(3)} ${end.y.toFixed(3)} Z`;
  }

  function renderSectorPacking(recipe) {
    const sectors = window.XykaCore.sectorGeometry(recipe.packing.layout.sectors);
    const aria = sectors.map((sector) => {
      const item = inventoryById.get(sector.tobaccoId);
      return `${item.brand} — ${item.name}: ${sector.percent}%`;
    }).join("; ");
    const paths = sectors.map((sector) => {
      const item = inventoryById.get(sector.tobaccoId);
      return `<path class="packing-sector-slice" d="${sectorPath(sector)}" style="fill:${item.visualColor}"/>`;
    }).join("");
    const leaders = sectors.map((sector) => `<line class="packing-sector-leader" x1="${sector.leaderStart.x.toFixed(2)}" y1="${sector.leaderStart.y.toFixed(2)}" x2="${sector.leaderEnd.x.toFixed(2)}" y2="${sector.leaderEnd.y.toFixed(2)}"/>`).join("");
    const labels = sectors.map((sector) => {
      const item = inventoryById.get(sector.tobaccoId);
      const { labelPoint, iconPoint } = sector;
      return `<g class="packing-sector-label" transform="translate(${labelPoint.x.toFixed(2)} ${labelPoint.y.toFixed(2)})"><rect x="-21" y="-12" width="42" height="24" rx="12"/><text y="4" text-anchor="middle">${sector.percent}%</text></g>
        <g class="packing-sector-icon" transform="translate(${iconPoint.x.toFixed(2)} ${iconPoint.y.toFixed(2)})"><circle class="packing-sector-icon-plate" r="18"/><image href="${assets[item.iconKey]}" x="-14" y="-14" width="28" height="28" preserveAspectRatio="xMidYMid meet"/></g>`;
    }).join("");
    return `<div class="packing-sector-diagram" role="img" aria-label="Капсула сверху. ${escapeHtml(aria)}"><svg viewBox="0 0 300 300" aria-hidden="true">${paths}<circle class="packing-sector-outline" cx="150" cy="150" r="92"/>${leaders}${labels}</svg></div>`;
  }

  function renderLayerPacking(recipe) {
    const layers = window.XykaCore.layerGeometry(recipe);
    const aria = layers.map((layer) => `${layer.position}: ${layer.segments.map((segment) => {
      const item = inventoryById.get(segment.tobaccoId);
      return `${item.brand} — ${item.name} ${segment.percent}%`;
    }).join(", ")}`).join("; ");
    const rows = layers.map((layer) => `<div class="packing-layer" style="--layer-height:${layer.heightPercent}%" data-position="${escapeHtml(layer.position)}">${layer.segments.map((segment) => {
      const item = inventoryById.get(segment.tobaccoId);
      return `<div class="packing-layer-segment" style="--segment-width:${segment.widthPercent}%;--ingredient:${item.visualColor}"><img src="${assets[item.iconKey]}" alt=""><strong>${segment.percent}%</strong></div>`;
    }).join("")}</div>`).join("");
    return `<div class="packing-layer-diagram" role="img" aria-label="Капсула сбоку. ${escapeHtml(aria)}"><div class="packing-heater"><span>Нагреватель</span></div><div class="packing-capsule">${rows}</div><span class="packing-distance">Дальше от нагревателя</span></div>`;
  }

  function renderPacking(recipe) {
    const type = recipe.packing.layout.type;
    if (type === "sectors") return renderSectorPacking(recipe);
    if (type === "layers") return `<p class="packing-intro layer-explanation">${escapeHtml(recipe.packing.instructions)}</p>${renderLayerPacking(recipe)}`;
    return `<p class="packing-intro">${escapeHtml(recipe.packing.instructions)}</p>`;
  }

  function renderRecipeDetail(recipeId) {
    const recipe = recipeById.get(recipeId);
    if (!recipe) return;
    const favorites = new Set(state.favoriteIds);
    const tried = new Set(state.triedIds);
    replaceTrustedMarkup(el.recipeDetail, `<header class="detail-header"><div class="detail-hero">${compositionVisual(recipe, "detail")}<div><div class="recipe-topline">${strengthBadge(recipe)}</div><h2 id="drawer-title">${escapeHtml(recipe.name)}</h2></div></div></header>
      <div class="detail-grid">
        <section class="detail-section composition-section"><span class="section-kicker">На 10 граммов</span><h3>Состав</h3><div class="detail-components">${componentRows(recipe, true)}</div></section>
        <section class="detail-section"><span class="section-kicker">Вкус</span><h3>Как звучит микс</h3><p>${escapeHtml(recipe.whyItWorks)}</p><div class="taste-timeline"><div><strong>Старт</strong><p>${escapeHtml(recipe.taste.start)}</p></div><div><strong>Середина</strong><p>${escapeHtml(recipe.taste.middle)}</p></div><div><strong>Послевкусие</strong><p>${escapeHtml(recipe.taste.aftertaste)}</p></div></div></section>
        <section class="detail-section wide packing-section"><span class="section-kicker">Метод: ${escapeHtml(recipe.packing.method)}</span><h3>Как забить капсулу</h3>${renderPacking(recipe)}</section>
        <section class="detail-section wide"><span class="section-kicker">XYKA PRO</span><h3>Температура</h3><div class="temperature-row"><div><strong>${recipe.heat.startC} °C</strong><span>Старт</span></div><div><strong>${recipe.heat.workC} °C</strong><span>Рабочая</span></div></div><p>${escapeHtml(recipe.heat.warmup)}</p><small>${escapeHtml(recipe.heat.adjustment)}</small></section>
      </div>
      <div class="detail-actions"><button type="button" class="secondary-action" data-favorite="${escapeHtml(recipe.id)}">${ICONS.heart}<span>${favorites.has(recipe.id) ? "В избранном" : "В избранное"}</span></button><button type="button" class="secondary-action" data-tried="${escapeHtml(recipe.id)}">${ICONS.check}<span>${tried.has(recipe.id) ? "Пробовал" : "Отметить пробу"}</span></button></div>`);
  }

  function setAppInert(inert) {
    for (const selector of ["[data-app-shell]", "[data-app-nav]", "[data-app-footer]", ".masthead"]) {
      const node = document.querySelector(selector);
      if (node) node.inert = inert;
    }
  }

  function openDrawer(recipeId, trigger) {
    lastFocusedElement = trigger || document.activeElement;
    renderRecipeDetail(recipeId);
    el.drawer.hidden = false;
    document.body.classList.add("drawer-open");
    setAppInert(true);
    el.drawer.querySelector(".drawer-close").focus();
  }

  function closeDrawer() {
    el.drawer.hidden = true;
    document.body.classList.remove("drawer-open");
    setAppInert(false);
    if (lastFocusedElement && typeof lastFocusedElement.focus === "function") lastFocusedElement.focus();
  }

  function handleStaticAction(event) {
    event.stopPropagation();
    const target = event.currentTarget;
    const action = target.dataset.staticAction;
    if (action === "view") {
      setView(target.dataset.view);
      return;
    }
    if (action === "change-direction") {
      state.direction = null;
      state.strength = "любая";
      saveState(); renderSelection(); renderDirections();
      el.directionStep.querySelector("button")?.focus();
      return;
    }
    if (action === "random") {
      let pool = exactRecipes();
      if (!pool.length) pool = window.XykaCore.filterRecipes(recipes, { direction: state.direction || "любое", strength: "любая", availableIds: availableSet() });
      const recipe = window.XykaCore.selectRandomRecipe(pool);
      if (recipe) openDrawer(recipe.id, target); else announce("На текущей полке нет доступных миксов");
      return;
    }
    if (action === "clear-search") {
      state.query = "";
      el.searchInput.value = "";
      saveState(); renderResults(); el.searchInput.focus();
      return;
    }
    if (action === "restore-pantry") {
      state.availableIds = [...catalogs.inventoryIds];
      saveState(); renderAll(); announce("Все 26 табаков возвращены на полку");
      return;
    }
    if (action === "close-drawer") closeDrawer();
  }

  window.XykaStaticAction = handleStaticAction;

  document.addEventListener("click", (event) => {
    const direction = event.target.closest("[data-direction]");
    if (direction) {
      state.direction = direction.dataset.direction;
      state.strength = "любая";
      saveState(); renderSelection(); renderStrengths(); renderResults();
      el.strengthStep.scrollIntoView({ behavior: "smooth", block: "start" });
      announce(`Выбрано направление ${DIRECTION_LABELS[state.direction]}. Теперь выберите крепость.`);
      return;
    }
    const strength = event.target.closest("[data-strength]");
    if (strength) { state.strength = strength.dataset.strength; saveState(); renderStrengths(); renderResults(); return; }
    const favorite = event.target.closest("[data-favorite]");
    if (favorite) { toggleSaved("favoriteIds", favorite.dataset.favorite); return; }
    const tried = event.target.closest("[data-tried]");
    if (tried) { toggleSaved("triedIds", tried.dataset.tried); return; }
    const open = event.target.closest("[data-recipe-open]");
    if (open) { openDrawer(open.dataset.recipeOpen, open); return; }
  });

  document.addEventListener("change", (event) => {
    const pantryToggle = event.target.closest("[data-pantry-id]");
    if (!pantryToggle) return;
    const ids = availableSet();
    if (pantryToggle.checked) ids.add(pantryToggle.dataset.pantryId); else ids.delete(pantryToggle.dataset.pantryId);
    state.availableIds = [...ids];
    saveState(); el.pantryCount.textContent = `${ids.size}/${inventory.length}`; renderStrengths(); renderResults(); renderSavedViews();
    announce(`На полке ${ids.size} из ${inventory.length}`);
  });

  el.searchInput.addEventListener("compositionstart", () => { composingSearch = true; });
  el.searchInput.addEventListener("compositionend", () => { composingSearch = false; state.query = el.searchInput.value; saveState(); renderResults(); });
  el.searchInput.addEventListener("input", () => { if (composingSearch) return; state.query = el.searchInput.value; saveState(); renderResults(); });
  el.componentFilter.addEventListener("change", () => { state.componentCount = el.componentFilter.value === "любое" ? "любое" : Number(el.componentFilter.value); saveState(); renderResults(); });
  document.addEventListener("keydown", (event) => {
    if (el.drawer.hidden) return;
    if (event.key === "Escape") { closeDrawer(); return; }
    if (event.key !== "Tab") return;
    const focusable = [...el.drawer.querySelectorAll('.drawer-sheet button:not([disabled]), .drawer-sheet [href], .drawer-sheet input:not([disabled]), .drawer-sheet select:not([disabled]), .drawer-sheet [tabindex]:not([tabindex="-1"])')];
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  });

  renderAll();
})();
