// A side-effect-free example. Loading it never starts services or makes requests.
import {fileURLToPath} from 'node:url';

const directory = (name) => fileURLToPath(new URL(`./${name}/`, import.meta.url));

export default {
  nome: 'hello-plugin',
  publico: [directory('public')],
  locales: [directory('locales')],
  portas() {
    return {
      ferramentas: {
        doTurno() {
          return [{
            name: 'hello_plugin_status',
            description: 'Read the example plugin status. Does not change anything.',
            parameters: {type: 'object', properties: {}, additionalProperties: false},
            run: async () => JSON.stringify({plugin: 'hello-plugin', ready: true}),
          }];
        },
        vetar: () => null,
        instrucoes: () => [],
      },
    };
  },
  ligar({rotas}) {
    // Public, read-only metadata: no account data, actions or authentication bypass.
    rotas.registrar('GET', '/api/hello-plugin/status', (_req, res) => {
      res.writeHead(200, {'content-type': 'application/json; charset=utf-8'});
      res.end(JSON.stringify({plugin: 'hello-plugin', ready: true}));
    });
  },
};
