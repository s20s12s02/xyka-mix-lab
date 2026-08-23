# Design QA — MixLab

## Visual target and implementation

- Source visual: `/Users/ssshevtsov/.codex/generated_images/01a02b62-d7f9-7053-8d88-80f3ec0172a4/exec-b60eaa6a-0600-48a5-8e4b-ccff75a1fcd5.png`, 853×1844 px. For like-for-like review it was normalized to 427×922 px.
- Implementation: `qa/mixlab-427-visual-target.png`, 427×922 px, light theme, direction `Ягоды`, strength `любая`, shelf 26/26.
- Combined comparison input: `qa/design-comparison-427.png`.
- Dark-theme evidence: `qa/mixlab-427-dark.png`, 427×922 px, same selected state.
- Additional viewport evidence: `qa/mixlab-final-preview.png`, `qa/mixlab-375-selection.png`, `qa/mixlab-390-initial.png`, `qa/mixlab-390-selection.png`, `qa/mixlab-390-detail.png`, `qa/mixlab-390-packing.png`, `qa/mixlab-1440-selection.png`.

## Comparison

- Visual language matches the selected calm editorial/laboratory direction: warm paper, condensed display face, plum action color, hairline dividers and engraving assets.
- The implementation intentionally gives the sequential flow more vertical space than the concept image: after direction selection, strength remains the primary task; results stay below and the `Подобрать` action scrolls to them.
- The selected direction stays visible, `Не важно` is selected by default, and strength uses real smoke assets plus semantic color.
- Result cards retain the reference signature of a composition ring around ingredient artwork, while adding exact percentage segments, stable ingredient colors and the required component legend.
- Dark theme preserves the same hierarchy and puts engraved direction, ingredient and smoke imagery on light neutral plates.

## Findings and correction history

| Severity | Finding | Correction | Recheck |
|---|---|---|---|
| P1 | The hidden drawer was visible on first load because a later `.drawer { display: grid }` rule overrode `[hidden]`. | Raised hidden-selector specificity to `[hidden][hidden]`; added a regression test. | Passed at 390×844 and after reload. |
| P2 | At 375 px the primary CTA split `Подобрать` into three lines. | Preserved words at 390 px and stacked actions below 380 px; added a regression test. | Passed at 375×844 with zero horizontal overflow. |
| P2 | Generated titles used repetitive long fillers such as `с нотой` and `в оттенках`. | Added 32 curated thematic names per internal direction while deriving IDs from the legacy title; compositions and IDs remain unchanged. | 216 unique titles, max 42 characters; stable fingerprint passed. |
| P2 | Smoke engravings had insufficient dark-theme contrast. | Added a neutral light plate only in dark mode; added a regression test. | Computed plate `rgb(255, 250, 243)` and visual check passed. |

No open P0, P1 or P2 findings remain.

## Interaction and accessibility evidence

- Sequential direction → strength → results flow, `Не важно`, individual strength counts and `Подобрать` were exercised in the in-app browser.
- Search was exercised against a recipe title, a tobacco description/hook and note-pyramid text with AND-token normalization.
- Drawer Escape, inert background, scroll lock, restored trigger focus, detailed packing content, favorites, tried log and pantry rendering were exercised.
- Visible interactive controls measured at least 44 px at 390 px; no horizontal overflow was found at 375, 390, 427 or 1440 px.
- Browser console warnings/errors: none. External DOM URLs: none.
- Strict premium UI audit: 0 findings. Design.md lint: 0 errors and 0 warnings.
- The in-app browser security policy blocks direct `file://` navigation, so that runtime check could not be executed through the selected browser. The autonomous artifact is covered by build tests, embedded-data/asset checks, absence-of-network checks and byte identity between `index.html` and the versioned `dist` file.

## Final result

Visual and interaction QA passed for the approved redesign, with the single documented `file://` tool limitation above.
