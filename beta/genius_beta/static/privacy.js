"use strict";
(async () => {
  const status = document.getElementById("privacy-status");
  try {
    const response = await fetch("/api/config", {credentials: "omit", cache: "no-store", headers: {Accept: "application/json"}});
    if (!response.ok) throw new Error("config");
    const config = await response.json(), privacy = config.privacy;
    if (!privacy || privacy.version !== "beta-2026-10-05-v2" || !privacy.controller || !privacy.contact || !Number.isInteger(privacy.retention_days)) throw new Error("version");
    for (const field of ["controller", "contact", "retention_days"]) {
      for (const element of document.querySelectorAll('[data-privacy="' + field + '"]')) element.textContent = String(privacy[field]);
    }
    status.textContent = config.registration_open ? "Altas habilitadas en esta instancia." : "Las altas están cerradas en esta instancia. Este aviso puede consultarse antes de crear una cuenta.";
  } catch (_) {
    status.textContent = "No se pudo confirmar que este aviso coincida con la configuración vigente. Recargá la página o consultá al responsable antes de aceptar.";
    status.setAttribute("role", "alert");
  }
})();
