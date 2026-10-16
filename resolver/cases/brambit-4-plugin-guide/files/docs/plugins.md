# Writing a plugin

A plugin adds deployment-specific behavior without making the engine depend on
that deployment. Branding, a customer integration, billing rules and analytics
belong in a plugin. A capability needed by the generic engine belongs in the core.
Do not make `web/server.mjs` import your plugin: register it in a plugin list.

This guide uses the executable [hello example](../examples/hello-plugin/index.mjs).
It adds a public status endpoint, a read-only assistant tool and a translated page.
It makes no network requests, writes no database rows and requires no provider key
for its focused tests. It is not an example of authentication or billing.

## 1. Start with the smallest plugin

The minimum export is an object with a nonempty `nome`. Use English for new names,
code and documentation; retain the Portuguese field names of the existing API.
The example adds the following files:

| File | Purpose |
|---|---|
| `examples/hello-plugin/index.mjs` | Plugin object and behavior |
| `examples/hello-plugin/active.mjs` | List exported to the loader |
| `examples/hello-plugin/public/hello-plugin.html` | Page supplied by this plugin |
| `examples/hello-plugin/locales/en.json` | Source text |
| `examples/hello-plugin/locales/pt-BR.json` | Portuguese text |
| `examples/hello-plugin/locales/es.json` | Spanish text |
| `tests/hello-plugin.test.mjs` | Focused integration tests |

Paths in `publico`, `locales` and the other folder fields must be absolute. Build
them with `fileURLToPath(new URL('./folder/', import.meta.url))`, as the example
does, so they follow the module when the installation directory changes.

## 2. Understand the lifecycle

[`web/plugins.mjs`](../web/plugins.mjs) loads the list and checks plugin names,
known fields, functions, folder paths and CSP configuration. Duplicate names fail
loading. `portas(nucleo)` is called early in server setup; its returned entries
fill the engine's ports. At that stage `nucleo` supplies `publicBase` and
`notifyOwner`, not the complete running server.

`ligar(servidor)` runs after the server helpers have been assembled. Register routes,
event subscriptions and published media there. Its invocation is synchronous: do
not depend on a promise returned by an async `ligar` being awaited by the server.
For plugin tables, `esquema({pool, S})` joins database initialization after the core
schema, in plugin-list order. Schema and account-isolation changes need the review
described in [CONTRIBUTING](../CONTRIBUTING.md).

Leave unused fields out. Unknown ports and two providers for one port fail boot;
port providers are not automatically merged. When composing several extensions,
have a single plugin own a port and combine their behavior explicitly.

## 3. Select the plugin list

Normally the loader looks for `web/plugins/ativos.mjs`, whose default export is an
array of plugin objects. The optional default list may be absent; the core then
uses its defaults.

To try the included example from the repository root in a POSIX shell, after the
normal development setup described in the [README](../README.md#quick-start):

```sh
BRAMBIT_PLUGINS="$PWD/examples/hello-plugin/active.mjs" npm run local
```

In PowerShell, set the variable separately:

```powershell
$env:BRAMBIT_PLUGINS = (Resolve-Path examples/hello-plugin/active.mjs).Path
npm run local
```

An explicit `BRAMBIT_PLUGINS` file must exist. A relative value resolves against
the process working directory. An error inside a present list stops loading;
there is no fallback that hides a failed import. Restart to load changed modules.

For an external installation, copy the example directory into an operator-owned
location and point `BRAMBIT_PLUGINS` at its `active.mjs`. The example only imports
Node built-ins and local files, so it does not depend on the core repository's
location. Plugins that import other packages need those dependencies installed
where their own modules can resolve them. Brambit does not install or sandbox a
plugin: the operator must review it as server-side code.

## 4. Choose a port

The current names are exported by `PORTAS_DE_PLUGIN` in `web/plugins.mjs`.
Consult each linked implementation for its method signatures before replacing it.

| Port | Responsibility | Behavior without a plugin |
|---|---|---|
| `permissoes` | App limits, disk quota and admission | Environment/profile-aware defaults in [permissoes.mjs](../web/permissoes.mjs); do not assume sign-up is always open |
| `contaPagadora` | Resolve and lock the account paying for usage | Personal account handling in [conta-pagadora.mjs](../web/conta-pagadora.mjs) |
| `gasto` | Usage accounting, spending status and related tools | US-dollar usage recording without a credit sales system; [gasto-simples.mjs](../web/gasto-simples.mjs) |
| `ferramentas` | Extra tools, their veto and prompt context | No added tools; [ferramentas.mjs](../web/ferramentas.mjs) |
| `contaPagamento` | Operator-managed payment-account behavior | Existing user-provided Asaas connections can still be selected; no operator-added tools; [conta-pagamento.mjs](../web/conta-pagamento.mjs) |
| `ganchosDaEmpresa` | Deployment hooks for business accounts | No plugin hooks attached; [empresa.mjs](../web/empresa.mjs) |
| `premiacaoDoConvite` | Referral reward explanation | No reward text contributed by this port |
| `assuntosConversados` | Topics used in routine suggestions | Empty topic input; [rotina-oferta.mjs](../web/rotina-oferta.mjs) |
| `diagnosticoDosFiltros` | Observe turn filtering | Empty removals and no-op cut callback |
| `briefDaJornada` | Journey-feedback instructions | Core report instructions; [discovery-report-instructions.mjs](../web/discovery-report-instructions.mjs) |
| `chaveDeepSeek` | Official selectable DeepSeek-model key | `DEEPSEEK_API_KEY` handling in [server.mjs](../web/server.mjs) |
| `atendimentoPublico` | Hooks before/after the public-support model | Core flow without deployment hooks; [publico.mjs](../web/publico.mjs) |
| `systemNote` | Stable installation context for the model | No extra installation note |

`rotas`, `eventos` and `midiaPublica` are helpers passed to `ligar`, rather than
additional keys to return from `portas`.

## 5. Add a route and a tool

The example registers `GET /api/hello-plugin/status` through `rotas.registrar`.
Registration matches method and path exactly; a duplicate fails. Handlers receive
`(req, res, url, ctx)`, and `ctx.currentUser()` is available for session-dependent
work. Use the existing authorization mechanisms before serving private data.
For free-form routing, see `usar` and `SEGUE` in [rotas.mjs](../web/rotas.mjs).
The public-support profile admits registered `/api/` routes, making this route
shape useful across profiles.

The example's `ferramentas` provides all three required functions: `doTurno`,
`vetar` and `instrucoes`. The returned `hello_plugin_status` tool takes an empty
object and produces read-only JSON. Tool descriptions, results and model prompts
stay in English. A tool with external effects needs an appropriate action gate;
the example's permissive veto is appropriate only for its inert status read.

Do not add a path to `semCsrf` merely to make a failing request pass. That list
removes the browser-origin requirement for exact paths; the plugin must provide
the authentication and validation required for its webhook or other use case.

## 6. Add pages and translated messages

`publico` supplies page directories. With the example enabled, open
`/hello-plugin`; the file is `public/hello-plugin.html`. Site lookup considers
brand folders first, plugin folders in list order next, and the core pages last.
Serving these files uses GET/HEAD. This example has no private page data.

New text belongs in `locales`, under a plugin-specific key prefix. The example
uses `hello_plugin.page.*` and `data-i18n` marks in HTML. English is the source;
Portuguese and Spanish catalogs carry the same keys. The actual renderer performs
translation and escapes text. Read [i18n.md](i18n.md) before adding variables,
attributes, plurals or client-side text. Do not translate the tool's prompt text.

Catalog precedence differs from page lookup: later plugin catalogs override
earlier ones, above the instance overlay and the core. Use unique keys unless an
override is intentional. `siteTextos` and `textosServidor` are older mechanisms;
use `locales` for new messages.

The `app` field can supply files for existing screen slots; inspect the markers
and validation in [app-encaixes.mjs](../web/app-encaixes.mjs). Add external page
origins only through the constrained `csp` field described in
[csp.mjs](../web/csp.mjs). This example needs neither screen slots nor external
origins.

## 7. Test before enabling

After installing the normal project dependencies, the focused example test is:

```sh
node --test tests/hello-plugin.test.mjs
node test-support/i18n-guard.mjs examples/hello-plugin/locales
```

The tests use the real loader, route registry, tool contract and translation
engine. They check duplicate port ownership, unrelated routes, POST left unhandled and
all three translations. They do not boot Postgres, call a model or test a production
deployment. The catalog checker also checks the core catalogs and may report
existing fallback entries; distinguish those from new plugin errors.

When testing a plugin in its installation repository, keep core modules independent
of deployment files. `test-support/nucleo-guard.mjs` checks references to files
listed in `nuvem.txt` and can boot a copy with those files omitted:

```sh
node test-support/nucleo-guard.mjs --sem-boot
```

Omitting `--sem-boot` adds its boot check and requires the normal development
dependencies. Run checks relevant to your change; do not silently claim the full
test suite or a deployment passed. Follow the contribution assignment, review and
CLA process before submitting upstream.
