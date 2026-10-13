#!/usr/bin/env node
// Replays inherited bytes through an external process, without importing any
// Kernel, adapter, Benchmark, or Python code. This is interoperability evidence,
// not a new mathematical oracle or a performance benchmark.
import { readFile, readdir } from 'node:fs/promises';
import { dirname, resolve, join, delimiter, relative } from 'node:path';
import { fileURLToPath } from 'node:url';
import { isDeepStrictEqual } from 'node:util';
import { GeniusClient, sha256 } from '../consumer/client.mjs';
import { describeResult, strictJSON } from '../consumer/bytes.mjs';
import { exportExchange, newDirectory, writeNew, jsonBytes } from '../consumer/package.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const output = process.argv[2];
if (!output) throw Error('Usage: node protocols/tests/consumer_replay.mjs NEW_DIRECTORY [correctness|performance|all]');
const scope = process.argv[3] ?? 'all';
if (!['all', 'correctness', 'performance'].includes(scope)) throw Error('Unknown replay scope');
await newDirectory(output);
await newDirectory(join(output, 'artifacts'));
await newDirectory(join(output, 'source_snapshot'));
const sourceFiles = [];
for (const directory of ['protocols/consumer', 'protocols/genius_protocols', 'protocols/tests']) {
  for (const file of (await readdir(join(root, directory))).filter(name => directory.endsWith('/tests') ? /^consumer_.*\.mjs$/.test(name) : /\.(mjs|py)$/.test(name))) sourceFiles.push(`${directory}/${file}`);
}
sourceFiles.push('protocols/CONTRACT.md');
const sourceHashes = {};
for (const name of sourceFiles) {
  const bytes = await readFile(join(root, name)); sourceHashes[name] = sha256(bytes);
  await writeNew(join(output, 'source_snapshot', name.replaceAll('/', '__')), bytes);
}
const client = new GeniusClient({ cwd: root, env: { ...process.env, PYTHONPATH: [join(root, 'protocols'), join(root, 'kernel')].join(delimiter) }, timeoutMs: 120000 });
const report = { format: 'genius-consumer-replay/1.0', scope, evidence_kind: 'INHERITED_F3_IDENTITY_AND_DECLARED_PARSER_REJECTION_THROUGH_EXTERNAL_NODE_CONSUMER', independent_mathematical_oracle: false, source_hashes_before: sourceHashes, source_runs: [], cases_with_calls: 0, cases_without_calls: [], calls: [], status: 'RUNNING' };
function containsNumber(value) {
  if (typeof value === 'number') return true;
  return value !== null && typeof value === 'object' && Object.values(value).some(containsNumber);
}
try {
  report.capabilities = await client.initialize();
  for (const run of [scope !== 'performance' ? 'CORRECTNESS_FINAL' : null, scope !== 'correctness' ? 'PERF_FINAL' : null].filter(Boolean)) {
    const source = join(root, 'baseline/GENIUS_PHASE_3_HANDOFF/validation/runs', run);
    report.source_runs.push(relative(root, source));
    const files = (await readdir(source)).filter(name => name.endsWith('.json')).sort();
    for (const filename of files) {
      const caseBytes = await readFile(join(source, filename));
      const record = JSON.parse(caseBytes.toString('utf8'));
      if (!Array.isArray(record.calls)) continue;
      if (record.calls.length === 0) { report.cases_without_calls.push({ run, id: record.id, source_sha256: sha256(caseBytes), inherited_status: record.status }); continue; }
      report.cases_with_calls++;
      for (let index = 0; index < record.calls.length; index++) {
        const call = record.calls[index];
        const artifact = join(source, call.artifact_directory);
        const input = await readFile(join(artifact, 'input.json'));
        const expectedBytes = await readFile(join(artifact, call.result_file));
        const expected = strictJSON(expectedBytes, { numbers: 'none' });
        // F3 call metadata uses JSON integers for operational configuration;
        // only that recorded metadata is rendered to wire Nat strings.
        const limits = call.limits === null || call.limits === undefined ? undefined
          : Object.fromEntries(Object.entries(call.limits).map(([name, value]) => [name, String(value)]));
        const entry = { run, case_id: record.id, call_index: index + 1, operation: call.operation,
          source_case_sha256: sha256(caseBytes), source_artifact_directory: relative(root, artifact),
          input_sha256: sha256(input), source_input_sha256: call.input_sha256,
          expected_bytes_sha256: sha256(expectedBytes), limits: limits ?? {} };
        try {
          let exchange;
          if (call.operation === 'evaluate') exchange = await client.evaluate(input, { limits });
          else {
            const candidate = await readFile(join(artifact, 'candidate.json'));
            entry.candidate_sha256 = sha256(candidate);
            // P05 rejects numeric JSON tokens before the Kernel verifier.
            // This is an explicit protocol rejection expectation, not output
            // identity. The original expected report remains in the evidence.
            const parsedCandidate = strictJSON(candidate);
            if (containsNumber(parsedCandidate)) {
              entry.protocol_expected = { valid: false, status: 'INVALID', errors: ['CANDIDATE_TYPE'] };
              entry.protocol_expectation_basis = 'CONTRACT P05: candidate contains numeric JSON token; FP1 requires string Nat/Q/Bit';
            }
            if (call.operation === 'verify_result') exchange = await client.verifyResult(input, candidate, { limits });
            else if (call.operation === 'verify_decisive_certificate') exchange = await client.verifyCertificate(input, candidate, { limits });
            else throw Error(`Unsupported inherited operation ${call.operation}`);
          }
          const actual = exchange.result ?? exchange.report;
          entry.actual_bytes_sha256 = exchange.resultDigest ?? sha256(jsonBytes(actual));
          entry.full_object_equal = isDeepStrictEqual(actual, expected);
          entry.input_bytes_equal = exchange.inputBytes.equals(input);
          entry.expected = call.operation === 'evaluate' ? describeResult(expected) : expected;
          entry.actual = call.operation === 'evaluate' ? describeResult(actual) : actual;
          entry.contract_rejection_equal = entry.protocol_expected ? isDeepStrictEqual(actual, entry.protocol_expected) : null;
          entry.comparison_basis = entry.protocol_expected ? 'DECLARED_PROTOCOL_PARSER_REJECTION' : 'FULL_INHERITED_OBJECT_IDENTITY';
          entry.status = (entry.protocol_expected ? entry.contract_rejection_equal : entry.full_object_equal) && entry.input_bytes_equal && entry.input_sha256 === entry.source_input_sha256 ? 'PASS' : 'FAIL';
          const outputName = `${run}__${record.id}__${String(index + 1).padStart(3, '0')}`;
          await exportExchange(join(output, 'artifacts', outputName), exchange);
          entry.actual_artifact_directory = `artifacts/${outputName}`;
          if (!entry.full_object_equal) {
            await writeNew(join(output, 'artifacts', outputName, 'expected.json'), expectedBytes);
            entry.mismatch = entry.protocol_expected ? 'Inherited report differs as required by explicit P05 parser rejection; this is not a full object identity' : 'Full inherited object or exact input byte identity differs; inspect expected.json and result/verification.json';
          }
        } catch (error) {
          entry.status = 'FAIL'; entry.error = { code: error.code ?? null, message: error.message, details: error.details ?? {} };
        }
        report.calls.push(entry);
        if (report.calls.length % 100 === 0) process.stdout.write(JSON.stringify({ completed_calls: report.calls.length, failures: report.calls.filter(item => item.status === 'FAIL').length }) + '\n');
      }
    }
  }
  report.total_cases = report.cases_with_calls + report.cases_without_calls.length;
  report.total_calls = report.calls.length;
  report.failed_calls = report.calls.filter(item => item.status === 'FAIL').length;
  report.full_identity_calls = report.calls.filter(item => item.full_object_equal && item.input_bytes_equal && !item.protocol_expected).length;
  report.declared_parser_rejections = report.calls.filter(item => item.contract_rejection_equal === true).length;
  report.status = report.failed_calls === 0 ? 'PASS' : 'FAIL';
} catch (error) {
  report.status = 'FAIL'; report.fatal = { code: error.code ?? null, message: error.message, details: error.details ?? {} };
} finally {
  await client.close();
  report.source_hashes_after = {};
  for (const name of sourceFiles) report.source_hashes_after[name] = sha256(await readFile(join(root, name)));
  report.sources_unchanged_during_run = isDeepStrictEqual(report.source_hashes_before, report.source_hashes_after);
  if (!report.sources_unchanged_during_run) report.status = 'FAIL';
  await writeNew(join(output, 'report.json'), jsonBytes(report));
}
process.stdout.write(JSON.stringify({ status: report.status, total_cases: report.total_cases, calls: report.total_calls, failed_calls: report.failed_calls, output_directory: resolve(output) }) + '\n');
if (report.status !== 'PASS') process.exitCode = 1;
