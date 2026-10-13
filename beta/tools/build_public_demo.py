"""Generate a public, synthetic receipt through the real queue and isolated engine.

Runs offline in a disposable database. Never reads production data or secrets.
GET of the resulting static file does not execute a job or create an account.
"""
from datetime import datetime, timezone
import hashlib
import html
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'beta'))
from genius_beta.app import create_app
from genius_beta.worker import Worker


def build():
    if os.environ.get('GENIUS_R2_BACKUP_ENABLED') == 'true':
        raise RuntimeError('Use an offline environment without production backup credentials')
    records = []
    with tempfile.TemporaryDirectory(prefix='genius-public-demo-') as temp:
        root = Path(temp)
        config = dict(DATA_DIR=root,DATABASE=root/'db.sqlite3',SUSPEND_FILE=root/'SUSPENDED',
            PUBLIC_URL='http://localhost',ENV='development',REGISTRATION_OPEN=True,TESTING=True)
        app = create_app(config)
        client = app.test_client(use_cookies=False)
        worker = Worker(config)
        worker.acquire()
        try:
            for name in ('hours-known', 'hours-unknown'):
                raw = (ROOT/'beta/examples'/(name+'.json')).read_bytes()
                response = client.post('/api/agents/demo',json={'example':name})
                assert response.status_code == 202
                token = response.json['credential']['token']
                headers = {'Authorization':'Bearer '+token}
                try:
                    assert worker.run_once()
                    job = client.get(response.json['poll_url'],headers=headers).json['job']
                    assert job['status'] == 'completed'
                    assert job['result']['evidence_origin'] == 'synthetic'
                    records.append(dict(example=name,input=json.loads(raw),input_file_sha256=hashlib.sha256(raw).hexdigest(),
                        observation=dict(environment='offline-disposable-database',transport='Flask WSGI test client',
                            bootstrap_http_status=202,job_http_status=200,job_status=job['status']),
                        result=job['result'],result_sha256=hashlib.sha256(json.dumps(job['result'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
                        result_hash_encoding='UTF-8 JSON: ensure_ascii=false, sort_keys=true, separators=comma-colon',
                        artifact_sha256=job['artifacts']['sha256']))
                finally:
                    assert client.delete('/api/agents/me',headers=headers).status_code == 204
                    token = None
        finally:
            worker.close()
    upstream = json.loads((ROOT/'beta/vendor/UPSTREAM_MANIFEST.json').read_text())
    return dict(format='genius-public-demo-result/1',generated_at_utc=datetime.now(timezone.utc).isoformat(),
        evidence_origin='synthetic',live_request=False,
        notice='Real engine executions on fixed synthetic fixtures. Reading this saved receipt does not run the engine. Not empirical validation or an unrestricted decision solver.',
        engine_upstream_commit=upstream['base_commit'],records=records)


def render(receipt):
    sections=[]
    for record in receipt['records']:
        response=record['result']['response']
        excerpt={key:response[key] for key in ('transport','execution','evidence','decisions','quality','obligations_ref','closure') if key in response}
        title='Datos conocidos' if record['example']=='hours-known' else 'Un dato desconocido'
        sections.append('<section><h2>'+title+'</h2><p>Ejemplo: <code>'+record['example']+'</code>. Ejecución: <code>'+response['execution']['state']+'</code>. Cierre: <code>'+response['closure']['state']+'</code>.</p><h3>Entrada sintética</h3><pre>'+html.escape(json.dumps(record['input'],ensure_ascii=False,indent=2))+'</pre><h3>Capas del resultado original</h3><pre>'+html.escape(json.dumps(excerpt,ensure_ascii=False,indent=2))+'</pre></section>')
    return '''<!doctype html><html lang="es-AR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Resultados de demostración · Genius Decision</title><meta name="description" content="Dos ejecuciones reales de Genius con ejemplos sintéticos: datos conocidos y valores PV_UNKNOWN. Lectura sin registro."><link rel="stylesheet" href="/static/styles.css"><link rel="alternate" type="application/json" href="/static/demo-result.json"></head><body><header class="topbar"><a class="brand" href="/">genius decision</a><span class="beta-label">DEMOSTRACIÓN SINTÉTICA</span></header><main class="docs"><h1>Así responde Genius.</h1><p>Estos resultados fueron generados por el motor real en un entorno local aislado, usando los ejemplos públicos de la beta. Están guardados: abrir esta página no inicia otra ejecución ni crea una cuenta.</p><p>Un trabajo completo puede conservar una decisión pendiente. <code>PV_UNKNOWN</code> significa desconocido; no se convierte en cero. Estas ejecuciones no acreditan utilidad en casos reales ni autorizan acciones sobre personas.</p><p><a href="/static/demo-result.json">Descargar resultados completos en JSON</a> · <a href="/static/mcp.html">Conectar por MCP</a> · <a href="/agents">Todas las formas de acceso</a></p><p>Generados: <time>'''+html.escape(receipt['generated_at_utc'])+'''</time>. El JSON conserva entradas, resultados, identificación del motor y hashes de comprobación. Los bloques siguientes muestran las capas originales; el documento completo incluye también la solicitud compilada y su presentación.</p>'''+''.join(sections)+'''</main><footer class="footer"><a href="/">Acceso humano</a><a href="/static/privacy.html">Privacidad</a></footer></body></html>\n'''


if __name__ == '__main__':
    output = ROOT/'beta/genius_beta/static/demo-result.json'
    receipt = build()
    output.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    output.with_name('demo.html').write_text(render(receipt))
    print(json.dumps({'path':str(output.relative_to(ROOT)),'examples':[r['example'] for r in receipt['records']],
        'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'bytes':output.stat().st_size}))
