// AAG_WINDOW_CONTROL_BRIDGE_V1_20260918
(() => {
  const { ipcMain } = require("electron");
  const fs = require("fs");
  const path = require("path");
  const originalHandle = ipcMain.handle.bind(ipcMain);
  let sequence = 0;

  const requestDir =
    process.env.AAG_WINDOW_CONTROL_DIR_WIN ||
    "Z:\\state\\window-control";

  function request(action) {
    try {
      const stem =
        String(Date.now()) + "-" +
        String(process.pid) + "-" +
        String(++sequence);
      const finalPath =
        path.win32.join(requestDir, stem + ".json");
      const tempPath = finalPath + ".tmp";
      const body = JSON.stringify({
        action: action,
        time: Date.now(),
        pid: process.pid
      });
      fs.writeFileSync(
        tempPath,
        body,
        { encoding: "utf8", flag: "wx" }
      );
      fs.renameSync(tempPath, finalPath);
      return { ok: true, action: action };
    } catch (error) {
      console.error(
        "[AAG_WINDOW_CONTROL] REQUEST_FAILED",
        action,
        String(error)
      );
      return { ok: false, error: String(error) };
    }
  }

  ipcMain.handle = function(channel, listener) {
    if (channel === "TOGGLEMINMAX") {
      return originalHandle(
        channel,
        () => request("maximize")
      );
    }
    if (channel === "MINIMIZE") {
      return originalHandle(
        channel,
        () => request("minimize")
      );
    }
    return originalHandle(channel, listener);
  };

  console.log(
    "[AAG_WINDOW_CONTROL] INTERCEPTOR_INSTALLED"
  );
})();
// /AAG_WINDOW_CONTROL_BRIDGE_V1_20260918
