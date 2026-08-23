---
version: alpha
name: "MixLab"
description: "Спокойный журнально-лабораторный интерфейс для подбора миксов XYKA PRO."
colors:
  paper: "#f4f1eb"
  sheet: "#fffdf8"
  sheet-soft: "#f8f5ef"
  ink: "#292b2a"
  ink-soft: "#67635d"
  hairline: "#d8d1c7"
  primary: "#6d2446"
  plum-dark: "#571a36"
  sage: "#718063"
  strength-light: "#b8c9a4"
  strength-medium: "#c48b3d"
  strength-strong: "#a94444"
  focus: "#ad7a39"
typography:
  display:
    fontFamily: "Oswald Local, Arial Narrow, sans-serif"
    fontSize: "4.2rem"
    lineHeight: 1
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "1rem"
    lineHeight: 1.48
  label:
    fontFamily: "-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "0.75rem"
    lineHeight: 1.2
rounded:
  sheet: "14px"
  control: "9px"
  drawer: "20px"
spacing:
  xs: "5px"
  sm: "8px"
  md: "14px"
  lg: "22px"
  xl: "32px"
components:
  primary-action:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.sheet}"
    height: "54px"
    rounded: "{rounded.control}"
  primary-action-hover:
    backgroundColor: "{colors.plum-dark}"
  recipe-card:
    backgroundColor: "{colors.sheet}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sheet}"
    padding: "18px"
  direction-option:
    backgroundColor: "{colors.sheet-soft}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "12px"
  app-surface:
    backgroundColor: "{colors.paper}"
  muted-copy:
    textColor: "{colors.ink-soft}"
  divider:
    backgroundColor: "{colors.hairline}"
    height: "1px"
  strength-light:
    backgroundColor: "{colors.strength-light}"
  strength-medium-light:
    backgroundColor: "{colors.sage}"
  strength-medium:
    backgroundColor: "{colors.strength-medium}"
  strength-strong:
    backgroundColor: "{colors.strength-strong}"
  focus-indicator:
    textColor: "{colors.focus}"
---

# Design System: MixLab

## Overview

**North Star: лабораторный журнал ароматиста.** MixLab выглядит как личная рабочая тетрадь, где гравюра объясняет вкус, а не украшает пустое место. Интерфейс должен быть тихим, точным и хорошо читаемым с iPhone. Он не похож на магазин, кальянный клуб, барное меню или сетку одинаковых SaaS-карточек.

Главная подпись системы — точное кольцо состава вокруг динамического коллажа ингредиентов. Цвет сегмента, мини-иконка, легенда и полоса компонента всегда относятся к одному табаку. Второй узнаваемый элемент — дымовая шкала крепости.

Runtime CSS в `src/styles.css` является каноническим владельцем токенов; этот файл зеркалит принятые значения и объясняет их применение. Изменение системного значения выполняется в CSS и `DESIGN.md` одним changeset.

## Colors

Светлая тема строится на нейтральной бумаге и чернилах. Слива обозначает выбор и действие. Крепость имеет отдельную семантическую шкалу: светло-зелёный, шалфейный, охристый, приглушённый красный. На тёмной теме значения семантических ролей светлеют, но порядок и смысл не меняются.

У каждого табака есть собственный `visualColor` из `inventory.json`. Этот цвет нельзя заменять экранным локальным значением: он повторяется во всех диаграммах и легендах.

## Typography

Oswald Local используется для MixLab, названий миксов и ориентиров. Системный sans используется для описаний, поиска и технологической карты. Крупный display не применяется к длинным абзацам. Проценты и температура используют табличные цифры.

## Layout

На первом мобильном экране показаны только шесть направлений. После выбора направление сворачивается в постоянную строку, а крепость открывается вторым шагом. До 979 px страница прокручивается как один документ. С 980 px выбор становится липкой левой колонкой, выдача — правой. Основной breakpoints: 620 и 980 px; минимальная поддерживаемая ширина — 320 px.

Все важные касания не меньше 44 px. Drawer ограничен визуальным viewport и safe-area; его тело прокручивается, а действия остаются доступными. Глобальный scrollbar наследуется всеми owned scroll surfaces.

## Elevation & Depth

Тень означает отдельный лист: она допустима у selection panel, карточки и drawer. Внутри листа используются тонкие линии, а не вложенные тени. Гравюрные изображения на тёмной теме остаются на спокойной светлой подложке.

## Shapes

Рабочие листы имеют радиус 14 px, управляющие элементы — 9–11 px. Круг используется для номера шага, мини-иконки или короткого статуса. Primary action сохраняет небольшой бумажный срез углов; декоративные срезы не распространяются на остальные кнопки.

## Components

- **Направление:** реальная WebP-гравюра, название и подпись действия. Выбор подтверждается следующим состоянием, а не цветом карточки.
- **Крепость:** дымовая WebP-иконка, слово, количество и цветовая рамка; выбранное состояние имеет дополнительную внутреннюю обводку и знак.
- **Карточка микса:** название, hook, кольцо/коллаж, компоненты, словесная крепость и уверенность. Происхождение, источники, ограничения, аллергены и теги не выводятся.
- **Кольцо:** SVG начинается на 12 часах, идёт по часовой стрелке; `pathLength=100`, длина сегмента равна проценту.
- **Поиск:** нативное поле с отдельной доступной кнопкой очистки. Поиск локальный, поэтому сетевые loading/race состояния неприменимы; IME composition сохраняется.
- **Select:** нативный select выбран осознанно для автономного iPhone-интерфейса; popup остаётся под управлением ОС, authored geometry не обещается.
- **Drawer:** app-owned modal с Escape, ловушкой фокуса, inert background и возвратом фокуса к карточке.

## Do's and Don'ts

### Do

- Использовать 37 зафиксированных WebP и manifest вместо emoji, CSS-art или временных заглушек.
- Сохранять процентный порядок от основы к оттенкам.
- Держать визуальный акцент на диаграмме и гравюрах, оставляя остальные поверхности спокойными.
- Проверять светлую/тёмную темы, reduced motion, клавиатуру и safe-area.

### Don't

- Не показывать внутреннюю числовую крепость, источники, происхождение, ограничения, аллергены или служебную классификацию рецепта.
- Не использовать неон, стекло, чёрно-золотую клубную эстетику, градиентный текст и случайные декоративные карточки.
- Не заменять ингредиентные цвета локальными цветами карточки.
- Не скрывать выбранное направление при переходе к крепости.
