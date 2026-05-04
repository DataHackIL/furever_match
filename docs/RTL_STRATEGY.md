# Frontend RTL Strategy for Antigravity

Since Antigravity displays Hebrew dog profiles (Right-to-Left text) and potentially English components (like code or breed names in LTR), it's crucial to implement a robust RTL strategy for the React + Vite frontend.

## 1. Global Direction

Set the `dir` attribute on the root HTML element or the main React container.

```html
<!-- index.html -->
<html lang="he" dir="rtl">
```

By setting this globally, the browser natively handles text alignment and element flow for right-to-left content.

## 2. Logical CSS Properties (Vanilla CSS)

Instead of using physical directions (`left`, `right`), use logical properties. This ensures that if you ever support LTR languages, the layout flips automatically without needing new stylesheets.

**Instead of:**
```css
.card {
  margin-left: 20px;
  padding-right: 15px;
  border-left: 2px solid #ccc;
}
```

**Use:**
```css
.card {
  margin-inline-start: 20px; /* Applies to the right in RTL */
  padding-inline-end: 15px;  /* Applies to the left in RTL */
  border-inline-start: 2px solid #ccc;
}
```

## 3. Typography Selection

Hebrew typography requires fonts specifically designed for the character set to look premium. 
Recommend using Google Fonts such as:
- **Assistant** (Modern, clean, great for UI)
- **Heebo** (Bold, excellent for headings)
- **Rubik** (Soft, friendly, good for a dog adoption app)

```css
@import url('https://fonts.googleapis.com/css2?family=Assistant:wght@400;600;700&display=swap');

body {
  font-family: 'Assistant', sans-serif;
}
```

## 4. Handling Bi-Directional Text (Bidi)

When mixing Hebrew descriptions with English words (e.g., "לברדור Retriever"), the text flow can break, causing punctuation to appear on the wrong side.

Use the HTML `<bdi>` (Bi-Directional Isolation) element or `dir="auto"` / `dir="ltr"` on spans for English words.

```jsx
<p>
  סוג הכלב הוא <bdi>Golden Retriever</bdi> והוא מתוק מאוד!
</p>
```

## 5. UI Component Reversal

Ensure interactive elements flow correctly:
- **Carousels/Sliders:** The "Next" arrow should point Left, and "Previous" should point Right.
- **Progress Bars:** For compatibility scores, bars should fill from Right to Left.
- **Icons:** Icons indicating direction (like arrows or chevrons) should be mirrored.

## 6. CSS Reset for RTL

If using CSS resets or utility classes, ensure they don't force `text-align: left`. Rely on the inherited `start` alignment provided by `dir="rtl"`.
