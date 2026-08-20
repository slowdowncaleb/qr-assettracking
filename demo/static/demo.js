document.addEventListener("DOMContentLoaded", () => {
  const btnWipe = document.getElementById("btn-wipe");
  const btnSeed = document.getElementById("btn-seed");
  const btnTrigger5min = document.getElementById("btn-trigger-5min");
  const btnTriggerMidnight = document.getElementById("btn-trigger-midnight");
  const btnClearLogs = document.getElementById("btn-clear-logs");
  const logConsole = document.getElementById("log-console");
  const toastContainer = document.getElementById("toast-container");

  function addLog(type, text) {
    const entry = document.createElement("div");
    entry.className = `log-entry ${type}`;
    const timeStr = new Date().toLocaleTimeString();
    entry.innerHTML = `
      <span class="log-time">[${timeStr}]</span>
      <span class="log-text">${text}</span>
    `;
    logConsole.appendChild(entry);
    logConsole.scrollTop = logConsole.scrollHeight;
  }

  function showToast(type, message) {
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${message}</span>`;
    toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateX(100%)";
      toast.style.transition = "all 0.3s ease";
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  // 1. Wipe / Empty Layers
  btnWipe.addEventListener("click", async () => {
    btnWipe.disabled = true;
    btnWipe.querySelector("span").textContent = "Wiping Layers...";
    addLog("system", "Wiping all 3 ArcGIS Feature Layers & clearing local cache...");

    try {
      const res = await fetch("/api/demo/wipe", { method: "POST" });
      const data = await res.json();

      if (res.ok && data.status === "success") {
        addLog("success", "All 3 layers emptied successfully (Layer 0, 1, 2) and local cache cleared.");
        showToast("success", "All layers wiped successfully!");
      } else {
        addLog("error", `Wipe failed: ${data.message || JSON.stringify(data)}`);
        showToast("error", "Failed to wipe layers.");
      }
    } catch (err) {
      addLog("error", `Network Error: ${err.message}`);
      showToast("error", "Error connecting to server.");
    } finally {
      btnWipe.disabled = false;
      btnWipe.querySelector("span").textContent = "Wipe / Empty Layers";
    }
  });

  // 2. Reseed Demo Data
  btnSeed.addEventListener("click", async () => {
    btnSeed.disabled = true;
    btnSeed.querySelector("span").textContent = "Seeding Datasets...";
    addLog("system", "Populating demo datasets to ArcGIS (Live 10 assets, ASU 5-min tour, 30-day journey)...");

    try {
      const res = await fetch("/api/demo/seed", { method: "POST" });
      const data = await res.json();

      if (res.ok && data.status === "success") {
        addLog("success", "Demo datasets seeded successfully! 10 assets loaded in US cities, 288 ASU points for today, 60 long-term points.");
        showToast("success", "Demo datasets populated successfully!");
      } else {
        addLog("error", `Seeding failed: ${data.message || JSON.stringify(data)}`);
        showToast("error", "Failed to seed demo data.");
      }
    } catch (err) {
      addLog("error", `Network Error: ${err.message}`);
      showToast("error", "Error connecting to server.");
    } finally {
      btnSeed.disabled = false;
      btnSeed.querySelector("span").textContent = "Reseed Demo Data";
    }
  });

  // 3. Trigger 5-Min Upload
  btnTrigger5min.addEventListener("click", async () => {
    btnTrigger5min.disabled = true;
    btnTrigger5min.querySelector("span").textContent = "Uploading...";
    addLog("system", "Triggering 5-minute snapshot push to Short-Term Layer (1)...");

    try {
      const res = await fetch("/api/demo/trigger-5min", { method: "POST" });
      const data = await res.json();

      if (res.ok && data.status === "success") {
        addLog("success", `${data.message} (${data.points_uploaded} points stamped at ${data.time_stamped})`);
        showToast("success", `5-Min Upload: ${data.points_uploaded} points pushed to ArcGIS!`);
      } else {
        addLog("warning", `5-Min Upload: ${data.message}`);
        showToast("warning", data.message);
      }
    } catch (err) {
      addLog("error", `Error triggering 5-min upload: ${err.message}`);
      showToast("error", "Failed to trigger 5-minute upload.");
    } finally {
      btnTrigger5min.disabled = false;
      btnTrigger5min.querySelector("span").textContent = "Trigger 5-Min Upload";
    }
  });

  // 4. Trigger Midnight Rollover
  btnTriggerMidnight.addEventListener("click", async () => {
    btnTriggerMidnight.disabled = true;
    btnTriggerMidnight.querySelector("span").textContent = "Executing Rollover...";
    addLog("system", "Triggering Midnight Rollover (Archive to Daily Layer & Wipe Short-Term Layer)...");

    try {
      const res = await fetch("/api/demo/trigger-midnight", { method: "POST" });
      const data = await res.json();

      if (res.ok && data.status === "success") {
        addLog("success", `Midnight Rollover Complete: Archived ${data.daily_archived_count} records to Daily Layer; wiped ${data.short_term_wiped_count} records from Short-Term Layer.`);
        showToast("success", "Midnight Rollover Complete!");
      } else {
        addLog("error", `Rollover failed: ${data.message}`);
        showToast("error", "Midnight rollover failed.");
      }
    } catch (err) {
      addLog("error", `Error executing rollover: ${err.message}`);
      showToast("error", "Failed to execute rollover.");
    } finally {
      btnTriggerMidnight.disabled = false;
      btnTriggerMidnight.querySelector("span").textContent = "Trigger Midnight Rollover";
    }
  });

  // Clear Logs
  btnClearLogs.addEventListener("click", () => {
    logConsole.innerHTML = "";
    addLog("system", "Log cleared.");
  });
});
