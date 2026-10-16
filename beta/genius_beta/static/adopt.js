'use strict';
(() => {
  const $ = id => document.getElementById(id);
  let prediction = null, policy = null;
  const predictions = {last:22, mean:20};
  function reset() {
    prediction = null;
    $('estimator').disabled = false; $('predict').disabled = false;
    $('reveal').disabled = true; $('share-demo').disabled = true;
    $('demo-result').textContent = 'Todavía no registraste una predicción.';
    $('demo-link').value = ''; $('demo-share-status').textContent = '';
  }
  $('predict').addEventListener('click', () => {
    prediction = predictions[$('estimator').value];
    $('estimator').disabled = true; $('predict').disabled = true; $('reveal').disabled = false;
    $('demo-result').textContent = `Predicción sintética registrada: ${prediction} °C. Revelá el dato posterior para medir el error.`;
  });
  $('reveal').addEventListener('click', () => {
    if (prediction === null) return;
    $('demo-result').textContent = `Demo sintética: predicción ${prediction} °C; dato posterior 21 °C; error absoluto ${Math.abs(prediction - 21)} °C. Esto no confirma una mejora genética.`;
    $('reveal').disabled = true; $('share-demo').disabled = false;
    const link = new URL('/adopt', location.origin);
    link.hash = 'demo-' + $('estimator').value;
    $('demo-link').value = link.href;
  });
  $('reset').addEventListener('click', reset);
  $('share-demo').addEventListener('click', async () => {
    const link = $('demo-link').value;
    if (!link) return;
    try {
      await navigator.clipboard.writeText(link);
      $('demo-share-status').textContent = 'Enlace copiado. Al abrirlo se identifica como demo sintética; no acredita actividad de un organismo.';
    } catch (_) {
      $('demo-share-status').textContent = 'No se pudo copiar automáticamente. Seleccioná y copiá el enlace de abajo.';
      $('demo-link').focus(); $('demo-link').select();
    }
  });
  function readDemoLink() {
    const preset = location.hash.slice(1);
    if (preset === 'demo-last' || preset === 'demo-mean') {
      reset();
      $('estimator').value = preset.slice(5);
      $('demo-result').textContent = 'Ejemplo sintético compartido. Registrá la predicción y revelá el dato para reproducirlo.';
      $('demo').scrollIntoView();
    }
  }
  readDemoLink(); window.addEventListener('hashchange', readDemoLink);
  function invalidatePolicy() {
    policy = null; $('policy-output').hidden = true; $('policy-json').textContent = '';
    $('policy-status').textContent = '';
  }
  $('hosting-mode').addEventListener('change', () => { $('policy-consent').checked = false; invalidatePolicy(); });
  $('policy-consent').addEventListener('change', invalidatePolicy);
  $('policy-form').addEventListener('submit', event => {
    event.preventDefault();
    if (!$('policy-consent').checked) return;
    const persistent = $('hosting-mode').value === 'persistent';
    policy = {worlds:[{world_id:'genius-reference-synthetic-v1',focus:['pump']}],max_births:1,
      ...(persistent ? {persistent:true,lease_seconds:null,valid_until:null} :
        {lease_seconds:86400,valid_until:new Date(Date.now()+86400000).toISOString()})};
    $('policy-json').textContent = JSON.stringify(policy, null, 2);
    $('policy-output').hidden = false;
    $('policy-status').textContent = persistent ? 'Preparada para revisión: permiso persistente y revocable. Todavía no está autorizado.' : 'Preparada para revisión: oferta válida durante 24 horas desde ahora. Regenerala si vence antes de instalar.';
  });
  $('download-policy').addEventListener('click', () => {
    if (!policy || !$('policy-consent').checked) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify(policy,null,2)+'\n'], {type:'application/json'}));
    const a = document.createElement('a'); a.href = url; a.download = 'policy.json'; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
})();
