(() => {
  const keys = [
    "full_screen_hide_right_bar",
    "full_screen_hide_search_bar",
    "full_screen_hide_top_bar",
    "full_screen_hide_app_header",
    "full_screen_hide_status_bar",
  ];
  let lastSettings = null;
  const findBookComponents = () => {
    const out = new Set();
    for (const el of document.querySelectorAll(".bookAreaContainer,.outer-book-area,.book-gutter-container,.sideLeft")) {
      let c = el.__vue__, n = 0;
      while (c && n++ < 10) {
        if (typeof c.toggleDockable === "function") out.add(c);
        c = c.$parent;
      }
    }
    return [...out];
  };
  const apply = () => {
    const vue = document.getElementById("app")?.__vue__;
    const store = vue?.$store;
    const settings = store?.state?.user?.settings;
    if (!vue || !store || !settings) return;
    let changed = settings !== lastSettings;
    lastSettings = settings;
    for (const key of keys) {
      if (String(settings[key] ?? "") !== "1") {
        if (typeof vue.$set === "function") vue.$set(settings, key, "1");
        else settings[key] = "1";
        changed = true;
      }
    }
    if (changed && store.state.tabsManager?.fullScreen) {
      requestAnimationFrame(() => {
        for (const c of findBookComponents()) {
          try { c.toggleDockable(false, false, false); } catch (_) {}
        }
        try { store.dispatch("tabsManager/toggleSplitter"); } catch (_) {}
      });
    }
  };
  setInterval(apply, 120);
  window.__AAG_FULLSCREEN_GLOBAL_V1__ = { apply };
})();
