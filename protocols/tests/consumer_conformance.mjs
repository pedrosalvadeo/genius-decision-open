#!/usr/bin/env node
import { readFile, readdir } from 'node:fs/promises';
import { dirname, resolve, join, delimiter } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFile } from 'node:child_process';
import { promisify, isDeepStrictEqual } from 'node:util';
import { GeniusClient, byteEnvelope, sha256 } from '../consumer/client.mjs';
import { describeResult, inspectResult, strictJSON } from '../consumer/bytes.mjs';
import { exportExchange, jsonBytes, newDirectory, writeNew } from '../consumer/package.mjs';
import { makeFixture, LARGE_Q, NEGATIVE_Q } from './consumer_fixture.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const output = process.argv[2];
if (!output) throw Error('Usage: node protocols/tests/consumer_conformance.mjs NEW_DIRECTORY');
await newDirectory(output);
await newDirectory(join(output, 'artifacts'));
const env = { ...process.env, PYTHONPATH: [join(root, 'protocols'), join(root, 'kernel')].join(delimiter) };
const options = { cwd: root, env };
const report = { format: 'genius-consumer-conformance/1.0', author_role: 'independent_external_Node_consumer', node_version: process.version,
  claim: 'Protocol conformance and finite independent fixture assertions; not empirical validation or a new Kernel correctness proof', cases: [], source_hashes: {} };
for (const directory of ['protocols/consumer', 'protocols/genius_protocols', 'protocols/tests']) {
  for (const file of (await readdir(join(root, directory))).filter(name => directory.endsWith('/tests') ? /^consumer_.*\.mjs$/.test(name) : /\.(mjs|py)$/.test(name))) {
    const name = `${directory}/${file}`; report.source_hashes[name] = sha256(await readFile(join(root, name)));
  }
}
report.source_hashes['protocols/CONTRACT.md'] = sha256(await readFile(join(root, 'protocols/CONTRACT.md')));
let assertions;
function check(actual, expected, label) {
  const passed = isDeepStrictEqual(actual, expected);
  assertions.push({ label, expected, actual, passed });
  if (!passed) throw Error(`Assertion failed: ${label}`);
}
async function expectError(fn, code, rpcCode) {
  let error;
  try { await fn(); } catch (caught) { error = caught; }
  check(error?.code ?? null, code, 'Error remains in its own transport/client plane');
  if (rpcCode !== undefined) check(error?.rpcCode, rpcCode, 'Exact JSON-RPC error code');
  return error;
}
async function test(id, name, body) {
  assertions = [];
  const row = { id, name, assertions };
  try { await body(); row.status = 'PASS'; }
  catch (error) { row.status = 'FAIL'; row.error = { code: error.code ?? null, message: error.message, stack: error.stack, details: error.details ?? {} }; }
  report.cases.push(row);
  await writeNew(join(output, `${id}.json`), jsonBytes(row));
  process.stdout.write(JSON.stringify({ id, status: row.status, name }) + '\n');
}
const client = new GeniusClient(options);
let capabilities;
let full;
const input = jsonBytes(makeFixture());
const save = async (id, exchange) => exportExchange(join(output, 'artifacts', id), exchange);
function fakeClient(body, changedCapabilities = capabilities) {
  const code = `const readline=require('node:readline');const caps=${JSON.stringify(changedCapabilities)};readline.createInterface({input:process.stdin}).on('line',line=>{const request=JSON.parse(line);const send=result=>process.stdout.write(JSON.stringify({jsonrpc:'2.0',id:request.id,result})+'\\n');if(request.method==='genius.initialize'){send(caps);return;} ${body} });`;
  return new GeniusClient({ command: process.execPath, args: ['-e', code], timeoutMs: 1000 });
}
try {
  await test('C01', 'Strict compatible one-time version/capability handshake', async () => {
    capabilities = await client.initialize();
    check(capabilities.protocol_version, 'genius-protocols/1.0', 'Wire version equality');
    check(capabilities.kernel_version, 'GENIUS-KERNEL-1.0.1', 'Kernel identity');
    await expectError(() => client.initialize(), 'LOCAL_STATE');
    await writeNew(join(output, 'capabilities.json'), jsonBytes(capabilities));
  });
  await test('C02', 'Independent complete fixture; exact byte package and verification', async () => {
    full = await client.evaluate(input); await save('C02', full);
    check(full.inputBytes.equals(input), true, 'Original UTF-8 byte identity');
    check(full.inputDigest, sha256(input), 'Input SHA computed independently in Node');
    check(full.resultDigest, sha256(full.resultBytes), 'Result SHA computed independently in Node');
    check([full.result.presentation, full.result.execution.status, full.result.decision.value.coverage], ['VALID', 'COMPLETE', 'EXHAUSTIVE'], 'Complete and exhaustive remain separate fields');
    check(full.result.integration.state, 'DEFINED', 'Formal conditional integration available');
    const verification = await client.verifyResult(input, full.resultBytes); await save('C02_verify', verification);
    check(verification.report, { valid: true, status: 'VALID', errors: [] }, 'Portable pair is accepted by public verifier');
    check((await readFile(join(output, 'artifacts/C02/input.json'))).equals(input), true, 'Export keeps input bytes');
    check((await readFile(join(output, 'artifacts/C02/result.json'))).equals(full.resultBytes), true, 'Export keeps result bytes');
  });
  await test('C03', 'JSON-equivalent distinct bytes retain distinct digest and reject cross-binding', async () => {
    const equivalent = Buffer.from(JSON.stringify(makeFixture()));
    check(JSON.parse(input).assumptions, JSON.parse(equivalent).assumptions, 'Unicode semantics unchanged by whitespace serialization');
    check(input.equals(equivalent), false, 'Byte sequences differ');
    const second = await client.evaluate(equivalent); await save('C03', second);
    check(second.inputDigest === full.inputDigest, false, 'Equivalent JSON digests are distinct');
    const crossed = await client.verifyResult(equivalent, full.resultBytes); await save('C03_crossbind', crossed);
    check(crossed.report.status, 'INVALID', 'A result for other exact input bytes is rejected');
  });
  await test('C04', 'Q above 2^53, negative rational, Unicode and nominal identities stay exact', async () => {
    const policy = full.result.policies[0];
    check(policy.functional.terminal.value[0].profile[0].value, LARGE_Q, 'Large reduced Q never converted to Number');
    check(policy.welfare.profile.value[0].value, NEGATIVE_Q, 'Negative rational numerator/denominator exact');
    check(policy.resources[0].total.value, LARGE_Q, 'Resource rational exact');
    check([policy.causal.nodes[0].x, policy.causal.nodes[0].i, policy.generative.origin.value, policy.welfare.profile.value[0].carrier], ['Shared', 'Shared', 'Shared', 'Shared'], 'Equal text IDs remain in four distinct fields/namespaces');
    check(JSON.parse(full.inputBytes).assumptions[0].statement, makeFixture().assumptions[0].statement, 'Unicode scalar and normalization forms preserved');
    check(typeof policy.causal.nodes[0].t, 'string', 'Nat time remains a string');
  });
  await test('C05', 'Unordered policy set cannot become an implicit preference', async () => {
    const changed = makeFixture(); changed.policies.reverse();
    const answer = await client.evaluate(jsonBytes(changed)); await save('C05', answer);
    check([...answer.result.decision.value.frontier].sort(), ['PA', 'PZ'], 'Both equivalent policy IDs remain maximal');
    check(answer.result.decision.value.selection.state, 'OUTSIDE_DOMAIN', 'unique on two maximals does not select by array order');
    check(answer.result.decision.value.pairs.length, 4, 'Complete 2-by-2 pair coverage');
  });
  await test('C06', 'Completed partial domain preserves independent data and RELATIVE scope', async () => {
    const changed = makeFixture(); changed.functional.measurements = [];
    const answer = await client.evaluate(jsonBytes(changed)); await save('C06', answer);
    check([answer.result.presentation, answer.result.execution.status, answer.result.decision.value.coverage], ['VALID', 'COMPLETE', 'RELATIVE'], 'Partial presentation remains valid and computation complete');
    check(answer.result.policies[0].functional.terminal.state, 'OUTSIDE_DOMAIN', 'Known partial function has negative domain membership');
    check(answer.result.policies[0].welfare.profile.state, 'DEFINED', 'Independent welfare stays available');
    check(answer.result.decision.value.selection.state, 'OUTSIDE_DOMAIN', 'RELATIVE cannot select');
  });
  await test('C07', 'Received F3 unresolved reference remains UNRESOLVED with COMPLETE computation', async () => {
    const original = await readFile(join(root, 'baseline/GENIUS_PHASE_3_HANDOFF/validation/runs/CORRECTNESS_FINAL/artifacts/ADV-DOM-002/001_evaluate/input.json'));
    const answer = await client.evaluate(original); await save('C07', answer);
    check([answer.result.presentation, answer.result.execution.status], ['UNRESOLVED', 'COMPLETE'], 'Reference unresolved differs from computation unfinished');
    check(answer.result.decision.value.coverage, 'RELATIVE', 'Coverage remains relative');
  });
  await test('C08', 'Operational exhaustion remains LIMITED/BLOCKED without a false negative', async () => {
    const answer = await client.evaluate(input, { limits: { max_operations: '0' } }); await save('C08', answer);
    check([answer.result.presentation, answer.result.execution.status, answer.result.decision.state], ['UNRESOLVED', 'LIMITED', 'BLOCKED'], 'Limits are an operational result, not outside-domain');
    check(answer.result.integration.state, 'BLOCKED', 'No exhausted integration certificate');
    check(answer.result.execution.limits.some(row => row.name === 'max_operations' && row.bound === '0'), true, 'Applied Nat-string limit remains visible');
  });
  await test('C09', 'Untrusted instance syntax stays in INVALID result, never RPC error', async () => {
    for (const [name, raw] of [['syntax', Buffer.from('{')], ['duplicate', Buffer.from('{"format":"genius-fp1/1.0","format":"genius-fp1/1.0"}')], ['invalid_utf8', Buffer.from([0xff])]]) {
      const answer = await client.evaluate(raw); await save(`C09_${name}`, answer);
      check([answer.result.presentation, answer.result.execution.status, answer.result.policies.length], ['INVALID', 'COMPLETE', 0], `Invalid ${name} is a preserved FP1 presentation state`);
    }
  });
  await test('C10', 'Valid decisive certificate, tampering and exact-byte cross-binding', async () => {
    const certificate = { input_digest: full.inputDigest, certificate: full.result.policies[0].evidence[0].verdict.value };
    const candidate = jsonBytes(certificate);
    const accepted = await client.verifyCertificate(input, candidate); await save('C10_valid', accepted);
    check(accepted.report.status, 'VALID', 'Valid decisive certificate accepted');
    certificate.certificate = { ...certificate.certificate, value: '0' };
    const altered = await client.verifyCertificate(input, jsonBytes(certificate)); await save('C10_invalid', altered);
    check(altered.report.status, 'INVALID', 'Altered certificate truth value rejected');
    const crossed = await client.verifyCertificate(Buffer.from(JSON.stringify(makeFixture())), candidate); await save('C10_crossbind', crossed);
    check(crossed.report.status, 'INVALID', 'Certificate cannot cross equal-JSON/different-byte inputs');
  });
  await test('C11', 'Verification exhaustion preserves null/INCOMPLETE', async () => {
    const answer = await client.verifyResult(input, full.resultBytes, { limits: { max_operations: '0' } }); await save('C11', answer);
    check([answer.report.valid, answer.report.status], [null, 'INCOMPLETE'], 'Unfinished verification is neither true nor false');
  });
  await test('C12', 'Incompatible protocol and missing capability reject before input transmission', async () => {
    for (const offer of [{ protocolVersions: ['genius-protocols/9.0'] }, { requiredCapabilities: ['evaluate', 'remote_publish'] }]) {
      const frames = [];
      const peer = new GeniusClient({ ...options, onFrame: (direction, bytes) => { if (direction === 'send') frames.push(strictJSON(bytes)); } });
      try { await expectError(() => peer.initialize(offer), 'RPC_ERROR', -32001); check(frames.map(frame => frame.method), ['genius.initialize'], 'No evaluation sent after failed negotiation'); }
      finally { await peer.close(); }
    }
  });
  await test('C13', 'Consumer rejects a falsely compatible handshake profile', async () => {
    const peer = fakeClient('', { ...capabilities, profile: 'FLOAT_APPROXIMATION' });
    try { await expectError(() => peer.initialize(), 'PROTOCOL_VIOLATION'); }
    finally { await peer.close(); }
  });
  await test('C14', 'Server process dies after accepting request but before response', async () => {
    const peer = fakeClient('process.exit(7);');
    try { await peer.initialize(); const error = await expectError(() => peer.evaluate(input), 'TRANSPORT_CLOSED'); check(error.details.exit_code, 7, 'Original process exit code retained'); }
    finally { await peer.close(); }
  });
  await test('C15', 'Parent cancellation terminates session without manufacturing LIMITED', async () => {
    const peer = fakeClient('setInterval(()=>{},1000);');
    try { await peer.initialize(); const controller = new AbortController(); const pending = peer.evaluate(input, { signal: controller.signal }); setTimeout(() => controller.abort(), 20); await expectError(() => pending, 'CANCELLED'); }
    finally { await peer.close(); }
  });
  await test('C16', 'Local timeout is TRANSPORT_TIMEOUT rather than Kernel domain evidence', async () => {
    const peer = fakeClient('setInterval(()=>{},1000);');
    try { await peer.initialize(); await expectError(() => peer.evaluate(input, { timeoutMs: 20 }), 'TRANSPORT_TIMEOUT'); }
    finally { await peer.close(); }
  });
  await test('C17', 'Malformed control params return RPC error and next valid request works', async () => {
    await expectError(() => client.transport.request('genius.evaluate', { input: { ...byteEnvelope(input), sha256: '0'.repeat(64) } }), 'RPC_ERROR', -32602);
    const answer = await client.evaluate(input); await save('C17', answer);
    check(answer.result.execution.status, 'COMPLETE', 'Protocol rejection did not mutate session or instance');
  });
  await test('C18', 'Consumer rejects tampered result envelope and cross-bound result digest', async () => {
    const badDigest = { ...byteEnvelope(full.resultBytes), sha256: '0'.repeat(64) };
    const wrongBinding = JSON.parse(full.resultBytes); wrongBinding.input_digest = '0'.repeat(64);
    for (const blob of [badDigest, byteEnvelope(jsonBytes(wrongBinding))]) {
      const peer = fakeClient(`send({input:request.params.input,result:${JSON.stringify(blob)}});`);
      try { await peer.initialize(); await expectError(() => peer.evaluate(input), 'PROTOCOL_VIOLATION'); }
      finally { await peer.close(); }
    }
  });
  await test('C19', 'Strict peer JSON rejects duplicate keys and numeric FP1 values', async () => {
    const peer = fakeClient('process.stdout.write(`{"jsonrpc":"2.0","id":${JSON.stringify(request.id)},"result":{},"result":{}}\\n`);');
    try { await peer.initialize(); await expectError(() => peer.evaluate(input), 'PROTOCOL_VIOLATION'); }
    finally { await peer.close(); }
    const altered = JSON.parse(full.resultBytes); altered.execution.progress.expanded_nodes = 2;
    await expectError(async () => inspectResult(jsonBytes(altered), full.inputDigest), 'PROTOCOL_VIOLATION');
  });
  await test('C20', 'Operational limits reject Number coercion and undeclared names locally', async () => {
    for (const limits of [{ max_nodes: 2 }, { max_nodes: '02' }, { horizon: '1' }, { max_nodes: '1000000000000' }]) {
      let thrown;
      try { await client.evaluate(input, { limits }); } catch (error) { thrown = error; }
      check(Boolean(thrown), true, 'Non-contract limit rejected before operation');
    }
  });
  await test('C21', 'Export never overwrites any earlier input/result package', async () => {
    const directory = join(output, 'artifacts/C02');
    await expectError(() => exportExchange(directory, full), 'EEXIST');
    check(sha256(await readFile(join(directory, 'input.json'))), full.inputDigest, 'Existing input unchanged');
    check(sha256(await readFile(join(directory, 'result.json'))), full.resultDigest, 'Existing result unchanged');
  });
  await test('C22', 'CLI capabilities, eval, verify and verify-certificate work as separate processes', async () => {
    const cli = join(root, 'protocols/consumer/cli.mjs');
    const original = join(output, 'artifacts/C02/input.json');
    const result = join(output, 'artifacts/C02/result.json');
    const certificate = join(output, 'artifacts/C10_valid/candidate.json');
    const invocations = [ ['capabilities'], ['eval', '--input', original], ['verify', '--input', original, '--candidate', result], ['verify-certificate', '--input', original, '--candidate', certificate] ];
    for (const args of invocations) {
      const target = resolve(output, `cli_${args[0]}`);
      const run = await promisify(execFile)(process.execPath, [cli, ...args, '--out', target], { cwd: root, env });
      const answer = JSON.parse(run.stdout);
      check(answer.output_directory, target, `CLI ${args[0]} exports into requested new directory`);
      if (args[0].startsWith('verify')) check(answer.status, 'VALID', `CLI ${args[0]} reports genuine verification`);
    }
  });
  await test('C23', 'ERROR execution grammar is preserved, not interpreted as infeasibility', async () => {
    // This is a consumer grammar test, not a claimed live Kernel crash.
    const interrupted = JSON.parse(full.resultBytes);
    interrupted.execution.status = 'ERROR';
    interrupted.presentation = 'UNRESOLVED';
    interrupted.decision = { state: 'BLOCKED', reasons: ['ExecutionDiagnostic'] };
    interrupted.integration = { state: 'BLOCKED', reasons: ['ExecutionDiagnostic'] };
    const parsed = inspectResult(jsonBytes(interrupted), full.inputDigest);
    check(describeResult(parsed).execution, 'ERROR', 'ERROR remains execution status');
    check(describeResult(parsed).decision, 'BLOCKED', 'No false empty frontier inferred');
    await writeNew(join(output, 'error_grammar_fixture.json'), jsonBytes(interrupted));
  });
  await test('C24', 'Complete negative formal outcome stays distinct from an operational error', async () => {
    const changed = makeFixture(); changed.constraints[0].bound = '0/1';
    const answer = await client.evaluate(jsonBytes(changed)); await save('C24', answer);
    check([answer.result.presentation, answer.result.execution.status, answer.result.decision.value.coverage], ['VALID', 'COMPLETE', 'EXHAUSTIVE'], 'Decided resource violation does not become a transport failure');
    check([...answer.result.decision.value.failed].sort(), ['PA', 'PZ'], 'Both policy IDs have explicit negative constraint evidence');
    check(answer.result.decision.value.frontier, [], 'Empty exhaustive feasible frontier is preserved');
    check(answer.result.policies.every(policy => policy.hard[0].value.value === '0'), true, 'Negative bits remain strings and retain their domain');
  });
  await test('C25', 'Caller buffer mutation during await cannot rewrite verified portable bytes', async () => {
    const peer = fakeClient(`setTimeout(()=>send({input_digest:request.params.input.sha256,artifact_digest:request.params.candidate.sha256,report:{valid:true,status:'VALID',errors:[]}}),30);`);
    try {
      await peer.initialize();
      const mutableInput = Buffer.from(input);
      const mutableCandidate = Buffer.from(full.resultBytes);
      const pending = peer.verifyResult(mutableInput, mutableCandidate);
      mutableInput.fill(32); mutableCandidate.fill(32);
      const answer = await pending;
      check(sha256(answer.inputBytes), answer.inputDigest, 'Verification export freezes request input before await');
      check(sha256(answer.candidateBytes), answer.artifactDigest, 'Verification export freezes candidate before await');
    } finally { await peer.close(); }
  });
} finally {
  await client.close();
  report.total_cases = report.cases.length;
  report.total_assertions = report.cases.reduce((sum, row) => sum + row.assertions.length, 0);
  report.failed_cases = report.cases.filter(row => row.status !== 'PASS').length;
  report.status = report.failed_cases === 0 ? 'PASS' : 'FAIL';
  await writeNew(join(output, 'report.json'), jsonBytes(report));
}
process.stdout.write(JSON.stringify({ status: report.status, cases: report.total_cases, assertions: report.total_assertions, failures: report.failed_cases, output_directory: resolve(output) }) + '\n');
if (report.status !== 'PASS') process.exitCode = 1;
