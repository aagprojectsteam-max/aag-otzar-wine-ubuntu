// AAG_PRODUCTION_TAB_FALLBACK_20260915
(() => {
  const {
    app,
    webContents
  } = require("electron");

  const log = (tag, obj={}) => {
    try {
      console.log(
        "[AAG_TABS_FALLBACK] " +
        tag + " " +
        JSON.stringify(obj)
      );
    } catch (_) {}
  };

  const findToolbar = () => {
    for (
      const wc of
      webContents.getAllWebContents()
    ) {
      try {
        if (
          wc.getURL().includes(
            "/tabs_toolbar"
          )
        ) {
          return wc;
        }
      } catch (_) {}
    }

    return null;
  };

  const toolbarVisible = async () => {
    const toolbar = findToolbar();

    if (!toolbar)
      return false;

    try {
      return await toolbar.executeJavaScript(`
        (() => {
          const el =
            document.querySelector(
              ".mock-browser"
            );

          if (!el)
            return false;

          return (
            getComputedStyle(el)
              .visibility === "visible"
          );
        })()
      `);
    } catch (_) {
      return false;
    }
  };

  app.on(
    "web-contents-created",
    (event, wc) => {

      wc.on(
        "did-finish-load",
        () => {
          let url = "";

          try {
            url = wc.getURL();
          } catch (_) {}

          if (
            !url.includes(
              "/dist/index.html"
            ) ||
            url.includes(
              "/tabs_toolbar"
            )
          ) {
            return;
          }

          /*
           * Accepted Wine 11.17 behavior:
           * give the application's normal path
           * four full seconds first.
           */
          setTimeout(
            async () => {
              try {
                if (
                  await toolbarVisible()
                ) {
                  log(
                    "SKIP_ALREADY_VISIBLE",
                    {
                      rendererId: wc.id
                    }
                  );

                  return;
                }

                const state =
                  await wc.executeJavaScript(`
                    (() => ({
                      alreadyDone:
                        globalThis
                          .__AAG_PRODUCTION_TAB_FALLBACK_DONE
                          === true,

                      electronReady:
                        globalThis
                          .ELECTRON_READY_UI
                          === true,

                      triggerType:
                        typeof globalThis
                          .SET_TAB_DONE_LOADING_FOR_TOOLBAR,

                      managerType:
                        typeof globalThis
                          ._OTZAR_TOOLBAR,

                      tabIdType:
                        typeof globalThis
                          .GET_TOOLBAR_TABID
                    }))()
                  `);

                if (
                  !state ||
                  state.alreadyDone ||
                  state.electronReady !== true ||
                  state.triggerType !==
                    "function" ||
                  state.managerType !==
                    "object" ||
                  state.tabIdType !==
                    "function"
                ) {
                  log(
                    "SKIP_NOT_READY",
                    {
                      rendererId: wc.id,
                      state
                    }
                  );

                  return;
                }

                const result =
                  await wc.executeJavaScript(`
                    (() => {
                      if (
                        globalThis
                          .__AAG_PRODUCTION_TAB_FALLBACK_DONE
                      ) {
                        return {
                          called:false,
                          reason:
                            "already-done"
                        };
                      }

                      globalThis
                        .__AAG_PRODUCTION_TAB_FALLBACK_DONE =
                        true;

                      try {
                        const tabId =
                          globalThis
                            .GET_TOOLBAR_TABID();

                        const value =
                          globalThis
                            .SET_TAB_DONE_LOADING_FOR_TOOLBAR();

                        return {
                          called:true,
                          tabId,
                          returnType:
                            typeof value
                        };
                      } catch (e) {
                        return {
                          called:false,
                          error:String(e)
                        };
                      }
                    })()
                  `);

                log(
                  "ORIGINAL_TRIGGER",
                  {
                    rendererId: wc.id,
                    result
                  }
                );

              } catch (e) {
                log(
                  "ERROR",
                  {
                    rendererId: wc.id,
                    error:String(e)
                  }
                );
              }
            },
            4000
          );
        }
      );
    }
  );

  log(
    "INSTALLED",
    {
      delayMs:4000,
      mode:
        "original-function-fallback"
    }
  );
})();
// /AAG_PRODUCTION_TAB_FALLBACK_20260915
