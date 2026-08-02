export function navigate(route) {
  const target = document.querySelector(`[data-view="${CSS.escape(route)}"]`);
  if (!target) {
    throw new Error(`Route tidak dikenal: ${route}`);
  }
  document.querySelectorAll("[data-view]").forEach((view) => {
    view.hidden = view !== target;
  });
  document.querySelectorAll("[data-route]").forEach((control) => {
    if (control.closest(".sidebar")) {
      control.setAttribute("aria-current", control.dataset.route === route ? "page" : "false");
    }
  });
  target.querySelector("h1")?.setAttribute("tabindex", "-1");
  target.querySelector("h1")?.focus();
}

