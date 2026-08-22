(() => {
  "use strict";

  const STORAGE_KEY = "xyka-mix-lab:v1";
  const DIRECTION_LABELS = {
    dessert: { short: "Десерт", long: "Десертное" },
    fruit: { short: "Тропики", long: "Фруктово-тропическое" },
    berry: { short: "Ягоды", long: "Ягодное" },
    citrus: { short: "Цитрус", long: "Цитрусово-кислое" },
    tea: { short: "Чай", long: "Чайное" },
    drink: { short: "Напитки", long: "Напиточное" },
    floral: { short: "Цветы", long: "Цветочно-парфюмерное" },
    unusual: { short: "Необычное", long: "Хвойно-травяное / необычное" },
  };
  const ORIGIN_LABELS = {
    exact: "Точный рецепт",
    adapted: "Адаптированный",
    authored: "Авторский",
    experimental: "Экспериментальный",
  };
  const ICONS = {
    heart: '<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/></svg>',
    check: '<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M5 13l4 4L19 7"/></svg>',
  };

  const parseData = (id) => JSON.parse(document.getElementById(id).textContent);
  const inventory = parseData("inventory-data");
  const analogs = parseData("analogs-data");
  const recipes = parseData("recipes-data");
  const inventoryById = new Map(inventory.map((item) => [item.id, item]));
  const recipeById = new Map(recipes.map((recipe) => [recipe.id, recipe]));
  const analogBySource = new Map(analogs.map((analog) => [analog.sourceComponent, analog]));
  const catalogs = {
    inventoryIds: new Set(inventoryById.keys()),
    recipeIds: new Set(recipeById.keys()),
    directions: new Set(Object.keys(DIRECTION_LABELS)),
    strengths: new Set(recipes.map((recipe) => recipe.strengthLabel)),
  };

  let storageHealthy = true;
  let sessionState = null;
  let lastFocusedElement = null;

  function readStoredState() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? JSON.parse(stored) : null;
    } catch (error) {
      storageHealthy = false;
      return sessionState;
    }
  }

  let state = window.XykaCore.normalizeState(
    readStoredState() || { direction: "berry", strength: "Средняя" },
    catalogs,
  );

  const el = {
    storageNotice: document.getElementById("storage-notice"),
    pantryCount: document.getElementById("pantry-count"),
    directionOptions: document.getElementById("direction-options"),
    strengthOptions: document.getElementById("strength-options"),
    findButton: document.getElementById("find-button"),
    findCount: document.getElementById("find-count"),
    randomButton: document.getElementById("random-button"),
    searchInput: document.getElementById("search-input"),
    componentFilter: document.getElementById("component-filter"),
    confidenceFilter: document.getElementById("confidence-filter"),
    clearSearch: document.getElementById("clear-search"),
    resultsSummary: document.getElementById("results-summary"),
    exactResults: document.getElementById("exact-results"),
    nearestSection: document.getElementById("nearest-section"),
    nearestResults: document.getElementById("nearest-results"),
    pantryList: document.getElementById("pantry-list"),
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

  function announce(message) {
    el.live.textContent = "";
    window.setTimeout(() => { el.live.textContent = message; }, 20);
  }

  function saveState() {
    sessionState = { ...state };
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
      if (!storageHealthy) storageHealthy = true;
    } catch (error) {
      storageHealthy = false;
    }
    renderStorageNotice();
  }

  function renderStorageNotice() {
    el.storageNotice.hidden = storageHealthy;
    if (!storageHealthy) {
      el.storageNotice.textContent = "Safari не разрешил постоянное хранение для этого файла. Изменения сохранятся только до закрытия вкладки.";
    }
  }

  function availableSet() {
    return new Set(state.availableIds);
  }

  function exactRecipes() {
    const filtered = window.XykaCore.filterRecipes(recipes, {
      direction: state.direction,
      strength: state.strength,
      availableIds: availableSet(),
      componentCount: state.componentCount,
      confidence: state.confidence,
    });
    return window.XykaCore.searchRecipes(filtered, state.query);
  }

  function nearestRecipes() {
    const nearest = window.XykaCore.findNearestByStrength(recipes, {
      direction: state.direction,
      strength: state.strength,
      availableIds: availableSet(),
      componentCount: state.componentCount,
      confidence: state.confidence,
    });
    return window.XykaCore.searchRecipes(nearest, state.query).slice(0, 6);
  }

  function renderDirections() {
    el.directionOptions.innerHTML = Object.entries(DIRECTION_LABELS).map(([id, label]) => `
      <button type="button" class="direction-option${state.direction === id ? " active" : ""}" data-direction="${id}" aria-pressed="${state.direction === id}">
        <span class="short">${escapeHtml(label.short)}</span><span class="long">${escapeHtml(label.long)}</span>
      </button>
    `).join("");
  }

  function renderStrengths() {
    const labels = window.XykaCore.STRENGTH_ORDER.filter((label) =>
      recipes.some((recipe) => recipe.directions.includes(state.direction) && recipe.strengthLabel === label),
    );
    if (!labels.includes(state.strength)) state.strength = labels.includes("Средняя") ? "Средняя" : labels[0];
    el.strengthOptions.innerHTML = labels.map((label) => {
      const count = window.XykaCore.filterRecipes(recipes, {
        direction: state.direction,
        strength: label,
        availableIds: availableSet(),
        componentCount: "любое",
        confidence: "любая",
      }).length;
      return `<button type="button" class="strength-option${state.strength === label ? " active" : ""}" data-strength="${escapeHtml(label)}" aria-pressed="${state.strength === label}" aria-label="${escapeHtml(label)}, доступно рецептов: ${count}">${escapeHtml(label)}</button>`;
    }).join("");
  }

  function recipeCard(recipe) {
    const favorites = new Set(state.favoriteIds);
    const tried = new Set(state.triedIds);
    const components = recipe.components.map((component) => `
      <div class="component-row">
        <span>${escapeHtml(component.brand)} · ${escapeHtml(component.name)}</span><strong>${component.percent}% · ${String(component.grams.toFixed(1)).replace(".", ",")} г</strong>
        <div class="component-track"><i style="width:${component.percent}%"></i></div>
      </div>
    `).join("");
    return `
      <article class="recipe-card" data-recipe-card="${escapeHtml(recipe.id)}">
        <button type="button" class="recipe-card-button" data-recipe-open="${escapeHtml(recipe.id)}" aria-label="Открыть рецепт ${escapeHtml(recipe.name)}">
          <div class="recipe-topline"><span class="origin-stamp">${escapeHtml(ORIGIN_LABELS[recipe.origin.type])}</span><span class="meta-chip">${escapeHtml(recipe.strengthLabel)}</span><span class="meta-chip">${escapeHtml(recipe.confidence)} уверенность</span></div>
          <h3 class="recipe-title">${escapeHtml(recipe.name)}</h3>
          <p class="recipe-notes">${escapeHtml(recipe.dominantNotes.join(" · "))}</p>
          <div class="component-bars">${components}</div>
        </button>
        <div class="card-actions">
          <button type="button" class="icon-button favorite${favorites.has(recipe.id) ? " active" : ""}" data-favorite="${escapeHtml(recipe.id)}" aria-pressed="${favorites.has(recipe.id)}" aria-label="${favorites.has(recipe.id) ? "Убрать из избранного" : "Добавить в избранное"}">${ICONS.heart}</button>
          <button type="button" class="icon-button${tried.has(recipe.id) ? " active" : ""}" data-tried="${escapeHtml(recipe.id)}" aria-pressed="${tried.has(recipe.id)}" aria-label="${tried.has(recipe.id) ? "Убрать отметку пробовал" : "Отметить как пробовал"}">${ICONS.check}</button>
        </div>
      </article>
    `;
  }

  function emptyState(title, text) {
    return `<div class="empty-state"><strong>${escapeHtml(title)}</strong><span>${escapeHtml(text)}</span></div>`;
  }

  function renderResults() {
    const exact = exactRecipes();
    const nearest = exact.length < 6 ? nearestRecipes() : [];
    el.findCount.textContent = exact.length ? `${exact.length} ${plural(exact.length, "рецепт", "рецепта", "рецептов")}` : "нет точных вариантов";
    el.resultsSummary.textContent = `${DIRECTION_LABELS[state.direction].long} · ${state.strength}. Найдено: ${exact.length}.`;
    el.clearSearch.hidden = !state.query;
    el.exactResults.innerHTML = exact.length
      ? exact.map(recipeCard).join("")
      : emptyState("Точного совпадения нет", "Верните ингредиенты на полку, ослабьте точные фильтры или посмотрите ближайшие по крепости.");
    el.nearestSection.hidden = !(exact.length < 6 && nearest.length);
    el.nearestResults.innerHTML = nearest.map(recipeCard).join("");
  }

  function plural(number, one, few, many) {
    const mod10 = number % 10;
    const mod100 = number % 100;
    if (mod10 === 1 && mod100 !== 11) return one;
    if (mod10 >= 2 && mod10 <= 4 && !(mod100 >= 12 && mod100 <= 14)) return few;
    return many;
  }

  function renderPantry() {
    const available = availableSet();
    const groups = new Map();
    inventory.forEach((item) => {
      if (!groups.has(item.brand)) groups.set(item.brand, []);
      groups.get(item.brand).push(item);
    });
    el.pantryList.innerHTML = [...groups.entries()].map(([brand, items]) => `
      <section class="pantry-group">
        <h2>${escapeHtml(brand)}</h2>
        <div class="pantry-items">${items.map((item) => {
          const rating = item.rating ? `HTReviews: ${String(item.rating.value).replace(".", ",")} · ${item.rating.votes} ${plural(item.rating.votes, "оценка", "оценки", "оценок")}` : "Оценка уточняется";
          return `<article class="pantry-item">
            <div><strong>${escapeHtml(item.name)}</strong><p>${escapeHtml(item.profile)}</p></div>
            <label class="switch"><input type="checkbox" data-pantry-id="${escapeHtml(item.id)}" ${available.has(item.id) ? "checked" : ""} aria-label="${available.has(item.id) ? "Есть на полке" : "Закончился"}: ${escapeHtml(item.name)}"><span></span></label>
            <div class="pantry-meta"><span>${escapeHtml(item.strengthLabel)}</span><span>${escapeHtml(rating)}</span></div>
          </article>`;
        }).join("")}</div>
      </section>
    `).join("");
    el.pantryCount.textContent = `${available.size} из ${inventory.length}`;
  }

  function renderSavedViews() {
    const available = availableSet();
    const favorites = state.favoriteIds.map((id) => recipeById.get(id)).filter(Boolean).filter((recipe) => recipe.components.every((c) => available.has(c.tobaccoId)));
    const tried = state.triedIds.map((id) => recipeById.get(id)).filter(Boolean).filter((recipe) => recipe.components.every((c) => available.has(c.tobaccoId)));
    el.favoriteResults.innerHTML = favorites.length ? favorites.map(recipeCard).join("") : emptyState("Пока пусто", "Нажмите сердечко на карточке подходящего рецепта.");
    el.triedResults.innerHTML = tried.length ? tried.map(recipeCard).join("") : emptyState("Записей пока нет", "После сессии отметьте рецепт галочкой «Пробовал».");
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
  }

  function renderAll() {
    renderStorageNotice();
    renderDirections();
    renderStrengths();
    renderResults();
    renderPantry();
    renderSavedViews();
    renderNavigation();
    el.searchInput.value = state.query;
    el.componentFilter.value = String(state.componentCount);
    el.confidenceFilter.value = state.confidence;
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
    announce(adding ? "Рецепт отмечен" : "Отметка снята");
  }

  function originDetails(recipe) {
    if (recipe.origin.type !== "adapted") return `<p>${escapeHtml(recipe.origin.adaptationNote)}</p>`;
    const original = recipe.origin.originalFormula.map((item) => `<li>${escapeHtml(item.component)} — ${item.percent}%</li>`).join("");
    const substitutions = recipe.origin.substitutions.map((substitution) => {
      const replacement = substitution.replacementIds.map((id) => inventoryById.get(id)?.name || id).join(" + ");
      return `<tr><td>${escapeHtml(substitution.originalName)}</td><td>${escapeHtml(replacement)}</td><td>${escapeHtml(substitution.explanation)}</td></tr>`;
    }).join("");
    return `
      <p>${escapeHtml(recipe.origin.adaptationNote)}</p>
      <h4>Исходная формула</h4><ul>${original}</ul>
      <div class="table-scroll"><table class="origin-table"><thead><tr><th>В источнике</th><th>На вашей полке</th><th>Почему замена допустима</th></tr></thead><tbody>${substitutions}</tbody></table></div>
    `;
  }

  function renderRecipeDetail(recipeId) {
    const recipe = recipeById.get(recipeId);
    if (!recipe) return;
    const favorites = new Set(state.favoriteIds);
    const tried = new Set(state.triedIds);
    const components = recipe.components.map((component) => `
      <div class="detail-component"><strong>${escapeHtml(component.brand)} · ${escapeHtml(component.name)}</strong><span>${component.percent}% · ${String(component.grams.toFixed(1)).replace(".", ",")} г</span><small>${escapeHtml(component.role)}</small></div>
    `).join("");
    const warnings = recipe.warnings.length
      ? `<ul class="warning-list">${recipe.warnings.map((warning) => `<li>${escapeHtml(warning)}</li>`).join("")}</ul>`
      : '<p class="detail-intro">Отдельных аллергенных или долевых предупреждений нет.</p>';
    const sources = recipe.sources.map((source) => `<a href="${escapeHtml(source.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(source.title)} ↗</a>`).join("");
    el.recipeDetail.innerHTML = `
      <header class="detail-header">
        <div class="recipe-topline"><span class="origin-stamp">${escapeHtml(ORIGIN_LABELS[recipe.origin.type])}</span><span class="meta-chip">${escapeHtml(recipe.directionLabel)}</span><span class="meta-chip">${escapeHtml(recipe.strengthLabel)}</span></div>
        <h2 id="drawer-title">${escapeHtml(recipe.name)}</h2>
        <p class="detail-intro">${escapeHtml(recipe.dominantNotes.join(" · "))} · ${escapeHtml(recipe.confidence)} уверенность</p>
      </header>
      <div class="detail-grid">
        <section class="detail-section"><h3>Состав на 10 г</h3><div class="detail-components">${components}</div></section>
        <section class="detail-section"><h3>Почему работает</h3><p>${escapeHtml(recipe.whyItWorks)}</p></section>
        <section class="detail-section wide"><h3>Как меняется вкус</h3><div class="taste-timeline">
          <div class="taste-step"><strong>Старт</strong><p>${escapeHtml(recipe.taste.start)}</p></div>
          <div class="taste-step"><strong>Середина</strong><p>${escapeHtml(recipe.taste.middle)}</p></div>
          <div class="taste-step"><strong>Послевкусие</strong><p>${escapeHtml(recipe.taste.aftertaste)}</p></div>
        </div></section>
        <section class="detail-section wide"><h3>Забивка · ${escapeHtml(recipe.packing.method)}</h3><div class="packing-card"><p>${escapeHtml(recipe.packing.instructions)}</p><strong>${escapeHtml(recipe.packing.airflowCheck)}</strong></div></section>
        <section class="detail-section"><h3>Нагрев XYKA PRO</h3><div class="temperature-row"><div class="temperature"><strong>${recipe.heat.startC} °C</strong><span>старт</span></div><div class="temperature"><strong>${recipe.heat.workC} °C</strong><span>рабочая</span></div></div><p>${escapeHtml(recipe.heat.warmup)}</p><p class="detail-intro">${escapeHtml(recipe.heat.adjustment)}</p></section>
        <section class="detail-section"><h3>Ограничения и аллергены</h3>${warnings}<p class="detail-intro">${escapeHtml(recipe.limits)}</p></section>
        <section class="detail-section wide"><h3>Происхождение</h3>${originDetails(recipe)}</section>
        <section class="detail-section wide"><h3>Источники</h3><div class="source-list">${sources}</div></section>
      </div>
      <div class="detail-actions">
        <button type="button" class="secondary-action" data-favorite="${escapeHtml(recipe.id)}">${ICONS.heart}<span>${favorites.has(recipe.id) ? "В избранном" : "В избранное"}</span></button>
        <button type="button" class="secondary-action" data-tried="${escapeHtml(recipe.id)}">${ICONS.check}<span>${tried.has(recipe.id) ? "Пробовал" : "Отметить пробу"}</span></button>
      </div>
    `;
  }

  function openDrawer(recipeId, trigger) {
    lastFocusedElement = trigger || document.activeElement;
    renderRecipeDetail(recipeId);
    el.drawer.hidden = false;
    document.body.classList.add("drawer-open");
    el.drawer.querySelector(".drawer-close").focus();
  }

  function closeDrawer() {
    el.drawer.hidden = true;
    document.body.classList.remove("drawer-open");
    if (lastFocusedElement && typeof lastFocusedElement.focus === "function") lastFocusedElement.focus();
  }

  document.addEventListener("click", (event) => {
    const viewButton = event.target.closest("[data-view]");
    if (viewButton) { setView(viewButton.dataset.view); return; }
    const direction = event.target.closest("[data-direction]");
    if (direction) { state.direction = direction.dataset.direction; saveState(); renderStrengths(); renderDirections(); renderResults(); return; }
    const strength = event.target.closest("[data-strength]");
    if (strength) { state.strength = strength.dataset.strength; saveState(); renderStrengths(); renderResults(); return; }
    const favorite = event.target.closest("[data-favorite]");
    if (favorite) { toggleSaved("favoriteIds", favorite.dataset.favorite); return; }
    const tried = event.target.closest("[data-tried]");
    if (tried) { toggleSaved("triedIds", tried.dataset.tried); return; }
    const open = event.target.closest("[data-recipe-open]");
    if (open) { openDrawer(open.dataset.recipeOpen, open); return; }
    if (event.target.closest("[data-close-drawer]")) closeDrawer();
  });

  document.addEventListener("change", (event) => {
    const pantryToggle = event.target.closest("[data-pantry-id]");
    if (pantryToggle) {
      const ids = availableSet();
      if (pantryToggle.checked) ids.add(pantryToggle.dataset.pantryId); else ids.delete(pantryToggle.dataset.pantryId);
      state.availableIds = [...ids];
      saveState();
      el.pantryCount.textContent = `${ids.size} из ${inventory.length}`;
      renderStrengths(); renderResults(); renderSavedViews();
      announce(`На полке ${ids.size} из ${inventory.length}`);
    }
  });

  el.findButton.addEventListener("click", () => {
    renderResults();
    document.querySelector(".results-panel").scrollIntoView({ behavior: "smooth", block: "start" });
    announce(`Найдено ${exactRecipes().length} рецептов`);
  });

  el.randomButton.addEventListener("click", () => {
    let pool = exactRecipes();
    if (!pool.length) pool = window.XykaCore.filterRecipes(recipes, { availableIds: availableSet() });
    const recipe = window.XykaCore.selectRandomRecipe(pool);
    if (recipe) openDrawer(recipe.id, el.randomButton); else announce("На текущей полке нет доступных рецептов");
  });

  el.searchInput.addEventListener("input", () => {
    state.query = el.searchInput.value;
    saveState(); renderResults();
  });
  el.componentFilter.addEventListener("change", () => { state.componentCount = el.componentFilter.value === "любое" ? "любое" : Number(el.componentFilter.value); saveState(); renderResults(); });
  el.confidenceFilter.addEventListener("change", () => { state.confidence = el.confidenceFilter.value; saveState(); renderResults(); });
  el.clearSearch.addEventListener("click", () => { state.query = ""; el.searchInput.value = ""; saveState(); renderResults(); el.searchInput.focus(); });
  el.restorePantry.addEventListener("click", () => { state.availableIds = [...catalogs.inventoryIds]; saveState(); renderAll(); announce("Все 26 табаков возвращены на полку"); });
  document.addEventListener("keydown", (event) => { if (event.key === "Escape" && !el.drawer.hidden) closeDrawer(); });

  renderAll();
})();
