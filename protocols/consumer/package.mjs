import { mkdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { sha256 } from './bytes.mjs';

export async function newDirectory(path) { await mkdir(path, { mode: 0o700 }); return path; }
export async function writeNew(path, contents) { await writeFile(path, contents, { flag: 'wx', mode: 0o600 }); }
export const jsonBytes = object => Buffer.from(JSON.stringify(object, null, 2) + '\n');

// The caller supplies a new directory. Exclusive writes never replace any
// source input, pre-existing result, or earlier failure evidence.
export async function exportExchange(directory, exchange, capabilities) {
  await newDirectory(directory);
  await writeNew(join(directory, 'input.json'), exchange.inputBytes);
  const hashes = { 'input.json': sha256(exchange.inputBytes) };
  if (exchange.resultBytes) {
    await writeNew(join(directory, 'result.json'), exchange.resultBytes);
    hashes['result.json'] = sha256(exchange.resultBytes);
  }
  if (exchange.candidateBytes) {
    await writeNew(join(directory, 'candidate.json'), exchange.candidateBytes);
    await writeNew(join(directory, 'verification.json'), jsonBytes(exchange.report));
    hashes['candidate.json'] = sha256(exchange.candidateBytes);
  }
  if (capabilities) await writeNew(join(directory, 'capabilities.json'), jsonBytes(capabilities));
  await writeNew(join(directory, 'digests.json'), jsonBytes(hashes));
}
