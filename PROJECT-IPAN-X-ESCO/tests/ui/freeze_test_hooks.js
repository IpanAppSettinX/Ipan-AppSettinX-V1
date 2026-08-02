// Test-only stub: simulate a slow/unresponsive pywebview backend so the E2E
// suite can prove the startup progress never freezes. Uses the real
// window.pywebview.api channel that the production bridge already reads.
window.__startupFreezeTest = { samples: [] };

(function installSlowBackend() {
  function slow(ms) {
    return new Promise(function (resolve) {
      setTimeout(resolve, ms);
    });
  }
  function ok(data) {
    return { success: true, data: data, error: null, correlation_id: "freeze-test" };
  }
  window.pywebview = {
    api: {
      async list_tweak_catalog() {
        await slow(15000);
        return ok([]);
      },
      async list_advanced_tweaks() {
        await slow(15000);
        return ok([]);
      },
      async authenticate() {
        return {
          success: false,
          data: null,
          error: { user_message: "Login dinonaktifkan pada freeze test." },
        };
      },
    },
  };
})();

// The production app waits for the `pywebviewready` event before running
// initialize(). This hook is a plain (non-module) script, so it executes
// before the deferred app.js module; DOMContentLoaded fires after the module
// registers its listener, making this dispatch reliable.
window.addEventListener("DOMContentLoaded", function () {
  window.dispatchEvent(new Event("pywebviewready"));
});

setInterval(function () {
  let width = 0;
  const bar = document.querySelector("#startup-bar");
  if (bar) {
    const inline = parseFloat(bar.style.width) || 0;
    const parent = bar.parentElement;
    const parentWidth = parent ? parent.clientWidth : 1;
    const computed = parentWidth
      ? ((parseFloat(window.getComputedStyle(bar).width) || 0) / parentWidth) * 100
      : 0;
    width = Math.max(inline, computed);
  }
  const screen = document.querySelector("#startup-screen");
  const state = screen ? screen.dataset.state || "visible" : "gone";
  window.__startupFreezeTest.samples.push({ t: Date.now(), width: width, state: state });
}, 500);
