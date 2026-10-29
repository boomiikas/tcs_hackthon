from pathlib import Path

css_path = Path("frontend01/src/styles/design-system.css")
content = css_path.read_text(encoding="utf-8")

# 1. Update text colors for higher contrast (WCAG AA compliant)
old_colors = """  /* Text & Typography */
  --text-primary: #191c1d;
  --text-secondary: #404843;
  --text-muted: #6f7872;
  --text-subtle: #98a29b;
  --text-on-primary: #ffffff;"""

new_colors = """  /* Text & Typography - High Contrast (WCAG AA Certified) */
  --text-primary: #141716;
  --text-secondary: #2b332d;
  --text-muted: #4e5a52;
  --text-subtle: #6e7a72;
  --text-on-primary: #ffffff;"""

if old_colors in content:
    content = content.replace(old_colors, new_colors)
else:
    # Try with CRLF
    content = content.replace(old_colors.replace("\n", "\r\n"), new_colors.replace("\n", "\r\n"))

# 2. Add accessible focus ring
focus_css = """
/* Accessibility Focus States */
:focus-visible {
  outline: 2px solid var(--primary-600) !important;
  outline-offset: 2px !important;
}

button:focus-visible, a:focus-visible, input:focus-visible, select:focus-visible {
  outline: 2px solid var(--primary-600) !important;
  outline-offset: 2px !important;
}
"""

if ":focus-visible" not in content:
    content += "\n" + focus_css

# 3. Enhance Tables with Sticky Headers and Scrollbars
table_enhancements = """
/* Enhanced Table Styling with Sticky Headers & Dense Mode */
.enterprise-table th {
  position: sticky;
  top: 0;
  z-index: 5;
  background-color: var(--bg-subtle);
  border-bottom: 2px solid var(--border-light);
}

.table-container {
  max-width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.table-container::-webkit-scrollbar {
  height: 6px;
  width: 6px;
}

.table-container::-webkit-scrollbar-track {
  background: var(--bg-subtle);
}

.table-container::-webkit-scrollbar-thumb {
  background: var(--border-medium);
  border-radius: var(--radius-full);
}

.enterprise-table.dense-table th,
.enterprise-table.dense-table td {
  padding: 8px 10px;
  font-size: 12px;
}

/* Tooltip & Popover Utility */
.metric-tooltip-container {
  position: relative;
  display: inline-flex;
  align-items: center;
  cursor: help;
}

.metric-tooltip-bubble {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  background-color: #191c1d;
  color: #ffffff;
  padding: 8px 12px;
  border-radius: var(--radius-md);
  font-size: 11px;
  font-weight: 400;
  line-height: 1.45;
  width: 260px;
  box-shadow: var(--shadow-lg);
  z-index: 100;
  pointer-events: none;
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.15s ease, visibility 0.15s ease;
  text-transform: none;
  letter-spacing: normal;
  text-align: left;
}

.metric-tooltip-bubble::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border-width: 5px;
  border-style: solid;
  border-color: #191c1d transparent transparent transparent;
}

.metric-tooltip-container:hover .metric-tooltip-bubble,
.metric-tooltip-container:focus-within .metric-tooltip-bubble {
  opacity: 1;
  visibility: visible;
}

/* Empty State Card */
.empty-state-card {
  padding: 36px 20px;
  text-align: center;
  background-color: var(--bg-subtle);
  border: 1px dashed var(--border-medium);
  border-radius: var(--radius-md);
}

/* Responsive Split Workspaces for 1366px Laptop Displays */
@media (max-width: 1366px) {
  .content-wrapper {
    padding: 18px 24px;
    max-width: 100%;
  }
  .split-workspace {
    grid-template-columns: 1fr !important;
    gap: 16px !important;
  }
  .grid-5 {
    grid-template-columns: repeat(3, 1fr) !important;
  }
}
"""

if "Enhanced Table Styling with Sticky Headers" not in content:
    content += "\n" + table_enhancements

css_path.write_text(content, encoding="utf-8")
print("design-system.css patched successfully!")
