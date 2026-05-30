# HTML Presentation Requirements for webpage-to-video

## Overview

The `make_video.py` script uses Playwright to record an HTML presentation as a video.
It advances slides by calling a JavaScript function (`advance()` by default) at timed intervals.
The HTML page must satisfy the following requirements.

---

## Required JavaScript Interface

The HTML page **must expose a global `advance()` function** that moves to the next step/slide.

### Minimal example

```js
let currentStep = 0;
const totalSteps = 10;

function advance() {
    if (currentStep < totalSteps - 1) {
        currentStep++;
        renderStep(currentStep);
    }
}
```

### Custom function name

If the function is named differently (e.g., `nextSlide()`), pass `--advance-fn nextSlide` to `make_video.py`.

---

## Slide Count Must Match Narration Count

The number of entries in `narrations.json` **must equal** the number of slides in the HTML.

- Step 0 → initial state (no `advance()` call before it)
- Step 1 → state after first `advance()`
- Step N-1 → state after (N-1) `advance()` calls

---

## Visual-Only Steps

Some slides may have no narration (animation-only transitions).
In `narrations.json`, use `null` for those steps:

```json
[
  "First slide narration",
  null,
  "Third slide narration"
]
```

The script will show the slide for `--visual-dur` seconds (default: 3.0s) without audio.

---

## CSS & Font Recommendations

- Use **web-safe fonts** or embed fonts inline (base64) to ensure they render in headless Chromium.
- Add a brief CSS animation on initial load, then use `advance()` to trigger further animations.
- Avoid animations that require user gesture to start (e.g., `:hover` effects won't trigger in headless mode).

---

## Page Load

The recorder waits **3 seconds** after `page.goto()` before starting to advance slides.
This is enough time for fonts and initial animations to load.

If your page needs more time (e.g., loading external assets), increase the initial wait time in `make_video.py`:

```python
page.wait_for_timeout(3000)  # Increase this value if needed
```

---

## Testing Your HTML

Before recording, test by opening the HTML in a normal browser and calling `advance()` in the browser console:

```js
advance()
advance()
advance()
```

Make sure each call produces the expected visual transition.

---

## Viewport

Default recording resolution is **1920 × 1080** (Full HD).
Pass `--width` and `--height` to override (e.g., `--width 1280 --height 720` for 720p).

The HTML should be designed for 16:9 aspect ratio for best results.
