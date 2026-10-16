import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import test from 'node:test';
import plugin from '../examples/hello-plugin/index.mjs';
import activePlugins from '../examples/hello-plugin/active.mjs';
import {arquivoDosPlugins, carregarPlugins, juntarPortas, pastasDoSite} from '../web/plugins.mjs';
import {createRotas} from '../web/rotas.mjs';
import {conferirFerramentas} from '../web/ferramentas.mjs';
import {createI18n, localeLayers} from '../web/i18n.mjs';
import {fillPage} from '../web/page-i18n.mjs';
import {checkCatalogs} from '../test-support/i18n-guard.mjs';

const list = new URL('../examples/hello-plugin/active.mjs', import.meta.url);

test('the documented explicit list loads through the real plugin loader', async () => {
  const location = arquivoDosPlugins({BRAMBIT_PLUGINS: fileURLToPath(list)});
  assert.equal(location.href, list.href);
  const loaded = await carregarPlugins(location);
  assert.equal(loaded, activePlugins);
  assert.deepEqual(loaded, [plugin]);
  assert.ok(pastasDoSite(loaded).every(path.isAbsolute));
  assert.throws(() => juntarPortas([plugin, {...plugin, nome: 'second-owner'}], {}), /dois plugins/);
});

test('the route answers GET and leaves unrelated paths and writes unhandled', async () => {
  const routes = createRotas();
  plugin.ligar({rotas: routes});
  let status, headers, body;
  const res = {writeHead(code, value) { status = code; headers = value; }, end(value) { body = value; }};
  const endpoint = new URL('http://localhost/api/hello-plugin/status');
  assert.equal(await routes.atender({method: 'GET'}, res, endpoint), true);
  assert.equal(status, 200);
  assert.match(headers['content-type'], /^application\/json/);
  assert.deepEqual(JSON.parse(body), {plugin: 'hello-plugin', ready: true});
  assert.equal(await routes.atender({method: 'POST'}, res, endpoint), false);
  assert.equal(await routes.atender({method: 'GET'}, res, new URL('http://localhost/elsewhere')), false);
});

test('the tool satisfies the actual port contract and returns read-only data', async () => {
  const ports = juntarPortas([plugin], {});
  const tools = conferirFerramentas(ports.ferramentas);
  const [tool] = tools.doTurno({userId: 'example-account', agentId: 'example-agent'});
  assert.equal(tool.name, 'hello_plugin_status');
  assert.deepEqual(JSON.parse(await tool.run({})), {plugin: 'hello-plugin', ready: true});
  assert.equal(tools.vetar({nome: tool.name, mensagem: 'Show the status.'}), null);
  assert.deepEqual(tools.instrucoes(new Set([tool.name])), []);
});

test('the page renders all three catalogs through the actual translation engine', () => {
  const checked = checkCatalogs(plugin.locales);
  assert.deepEqual(checked.errors, []);
  assert.deepEqual(checked.missing, []);
  const i18n = createI18n({layers: localeLayers({plugins: [plugin], overlayDir: null})});
  const html = readFileSync(new URL('../examples/hello-plugin/public/hello-plugin.html', import.meta.url), 'utf8');
  for (const [language, expected] of [['en', 'Example plugin'], ['pt-BR', 'Plugin de exemplo'], ['es', 'Plugin de ejemplo']]) {
    const problems = [];
    const rendered = fillPage(html, language, {i18n, onProblem: (p) => problems.push(p)});
    assert.ok(rendered.includes(expected));
    assert.deepEqual(problems, []);
  }
});
