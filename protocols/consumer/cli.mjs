#!/usr/bin/env node
import { readFile } from 'node:fs/promises';
import { dirname, resolve, join, delimiter } from 'node:path';
import { fileURLToPath } from 'node:url';
import { GeniusClient } from './client.mjs';
import { describeResult, strictJSON } from './bytes.mjs';
import { exportExchange, jsonBytes, newDirectory, writeNew } from './package.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const usage = 'node protocols/consumer/cli.mjs capabilities|eval|verify|verify-certificate --out NEW_DIRECTORY [--input FILE] [--candidate FILE] [--limits FILE] [--python EXECUTABLE]';
const [operation, ...args] = process.argv.slice(2);
const options = {};
let client;
try {
  if (!['capabilities', 'eval', 'verify', 'verify-certificate'].includes(operation)) throw Error(usage);
  for (let index = 0; index < args.length; index += 2) {
    const key = args[index];
    if (!['--out', '--input', '--candidate', '--limits', '--python'].includes(key) || Object.hasOwn(options, key) || args[index + 1] === undefined) throw Error(usage);
    options[key] = args[index + 1];
  }
  if (!options['--out'] || (operation !== 'capabilities' && !options['--input']) || (['verify', 'verify-certificate'].includes(operation) && !options['--candidate'])) throw Error(usage);
  const input = options['--input'] ? await readFile(options['--input']) : undefined;
  const candidate = options['--candidate'] ? await readFile(options['--candidate']) : undefined;
  const limits = options['--limits'] ? strictJSON(await readFile(options['--limits']), { numbers: 'none' }) : undefined;
  client = new GeniusClient({ command: options['--python'] || 'python3', cwd: root,
    env: { ...process.env, PYTHONPATH: [join(root, 'protocols'), join(root, 'kernel')].join(delimiter) } });
  const controller = new AbortController();
  const cancel = () => controller.abort();
  process.once('SIGINT', cancel); process.once('SIGTERM', cancel);
  const capabilities = await client.initialize({ signal: controller.signal });
  let summary;
  if (operation === 'capabilities') {
    await newDirectory(options['--out']);
    await writeNew(join(options['--out'], 'capabilities.json'), jsonBytes(capabilities));
    summary = capabilities;
  } else {
    const methodOptions = { limits, signal: controller.signal };
    const exchange = operation === 'eval' ? await client.evaluate(input, methodOptions)
      : operation === 'verify' ? await client.verifyResult(input, candidate, methodOptions)
      : await client.verifyCertificate(input, candidate, methodOptions);
    await exportExchange(options['--out'], exchange, capabilities);
    summary = exchange.result ? { input_digest: exchange.inputDigest, result_digest: exchange.resultDigest, ...describeResult(exchange.result) }
      : { input_digest: exchange.inputDigest, artifact_digest: exchange.artifactDigest, ...exchange.report };
  }
  process.stdout.write(JSON.stringify({ output_directory: resolve(options['--out']), ...summary }) + '\n');
} catch (error) {
  process.stderr.write(JSON.stringify({ status: 'CLIENT_ERROR', code: error.code ?? 'USAGE_OR_FILESYSTEM', message: error.message, details: error.details ?? {} }) + '\n');
  process.exitCode = 1;
} finally { if (client) await client.close(); }
