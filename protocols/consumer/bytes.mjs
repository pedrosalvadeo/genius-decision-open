import { createHash } from 'node:crypto';
import { TextDecoder } from 'node:util';

export class ConsumerError extends Error {
  constructor(code, message, details = {}) {
    super(message);
    this.name = 'ConsumerError';
    this.code = code;
    this.details = details;
  }
}

export function insist(condition, message, code = 'PROTOCOL_VIOLATION') {
  if (!condition) throw new ConsumerError(code, message);
}

export function exactKeys(value, required, optional = []) {
  insist(value !== null && typeof value === 'object' && !Array.isArray(value), 'Expected an object');
  const allowed = new Set([...required, ...optional]);
  insist(required.every(k => Object.hasOwn(value, k)) && Object.keys(value).every(k => allowed.has(k)),
    `Expected fields ${required.join(',')} with optional ${optional.join(',')}; received ${Object.keys(value).join(',')}`);
}

export const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');

export function byteEnvelope(bytes) {
  insist(Buffer.isBuffer(bytes), 'Input must be a Buffer: string encoding must be an explicit caller decision', 'LOCAL_INPUT');
  return { encoding: 'base64', data: bytes.toString('base64'), sha256: sha256(bytes) };
}

export function decodeEnvelope(envelope, maximum) {
  exactKeys(envelope, ['encoding', 'data', 'sha256']);
  insist(envelope.encoding === 'base64', 'Unsupported byte encoding');
  insist(typeof envelope.data === 'string' && /^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(envelope.data), 'Invalid base64');
  insist(typeof envelope.sha256 === 'string' && /^[0-9a-f]{64}$/.test(envelope.sha256), 'Invalid SHA-256');
  if (maximum !== undefined) insist(BigInt(envelope.data.length / 4 * 3) <= BigInt(maximum) + 2n, 'Envelope exceeds declared byte bound');
  const bytes = Buffer.from(envelope.data, 'base64');
  insist(bytes.toString('base64') === envelope.data, 'Noncanonical base64');
  if (maximum !== undefined) insist(BigInt(bytes.length) <= BigInt(maximum), 'Decoded envelope exceeds declared byte bound');
  insist(sha256(bytes) === envelope.sha256, 'Envelope byte digest mismatch');
  return bytes;
}

// A small independent JSON reader rejects duplicate keys, isolated Unicode
// surrogates and unsafe numeric values before they can be silently collapsed.
// Domain documents use numbers='none': Nat, Bit and Q are always strings.
export function strictJSON(bytes, { numbers = 'safe', maximumDepth = 512 } = {}) {
  let source;
  try { source = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(bytes); }
  catch { throw new ConsumerError('PROTOCOL_VIOLATION', 'Invalid UTF-8'); }
  let at = 0;
  const ws = () => { while (/[\x20\x09\x0a\x0d]/.test(source[at] ?? '\0')) at++; };
  function string() {
    const start = at++;
    let escaped = false;
    while (at < source.length) {
      const ch = source[at++];
      if (escaped) { escaped = false; continue; }
      if (ch === '\\') { escaped = true; continue; }
      if (ch === '"') {
        let value;
        try { value = JSON.parse(source.slice(start, at)); }
        catch { throw new ConsumerError('PROTOCOL_VIOLATION', 'Invalid JSON string'); }
        for (let p = 0; p < value.length; p++) {
          const unit = value.charCodeAt(p);
          if (unit >= 0xd800 && unit <= 0xdbff) {
            const next = value.charCodeAt(++p);
            insist(next >= 0xdc00 && next <= 0xdfff, 'Isolated high surrogate');
          } else insist(unit < 0xdc00 || unit > 0xdfff, 'Isolated low surrogate');
        }
        return value;
      }
    }
    throw new ConsumerError('PROTOCOL_VIOLATION', 'Unterminated JSON string');
  }
  function value(depth) {
    insist(depth <= maximumDepth, 'JSON nesting exceeds consumer bound');
    ws();
    const ch = source[at];
    if (ch === '"') return string();
    if (ch === '{') {
      at++; ws();
      const result = {};
      const seen = new Set();
      if (source[at] === '}') { at++; return result; }
      for (;;) {
        insist(source[at] === '"', 'Expected JSON object key');
        const key = string(); ws();
        insist(!seen.has(key), `Duplicate JSON key ${key}`); seen.add(key);
        insist(source[at++] === ':', 'Expected JSON colon');
        Object.defineProperty(result, key, { value: value(depth + 1), enumerable: true, configurable: true, writable: true });
        ws();
        if (source[at] === '}') { at++; return result; }
        insist(source[at++] === ',', 'Expected JSON object separator'); ws();
      }
    }
    if (ch === '[') {
      at++; ws();
      const result = [];
      if (source[at] === ']') { at++; return result; }
      for (;;) {
        result.push(value(depth + 1)); ws();
        if (source[at] === ']') { at++; return result; }
        insist(source[at++] === ',', 'Expected JSON array separator');
      }
    }
    for (const [word, primitive] of [['true', true], ['false', false], ['null', null]]) {
      if (source.startsWith(word, at)) { at += word.length; return primitive; }
    }
    const match = /-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?/.exec(source.slice(at));
    insist(match && match.index === 0, 'Invalid JSON value');
    insist(numbers === 'safe', 'JSON numbers are forbidden in FP1 result documents');
    const number = Number(match[0]);
    insist(Number.isSafeInteger(number), 'Only safe integers are accepted in transport fields');
    at += match[0].length;
    return number;
  }
  const result = value(0); ws();
  insist(at === source.length, 'Trailing data after JSON');
  return result;
}

export const isNat = value => typeof value === 'string' && /^(?:0|[1-9][0-9]*)$/.test(value);
export const isID = value => typeof value === 'string' && /^[A-Za-z][A-Za-z0-9_.-]*$/.test(value);

export function describeResult(result) {
  return {
    presentation: result.presentation,
    execution: result.execution.status,
    decision: result.decision.state,
    coverage: result.decision.state === 'DEFINED' ? result.decision.value.coverage : null,
    integration: result.integration.state,
    diagnostics: result.diagnostics.map(item => item.code),
  };
}

export function inspectResult(bytes, inputDigest) {
  const result = strictJSON(bytes, { numbers: 'none' });
  exactKeys(result, ['format', 'input_digest', 'specification', 'execution', 'presentation', 'diagnostics', 'checks', 'policies', 'decision', 'integration']);
  insist(result.format === 'genius-fp1-result/1.0' && result.specification === 'GENIUS-SPEC-1.0.0', 'Incompatible result version');
  insist(result.input_digest === inputDigest, 'Result input_digest does not bind exact input bytes');
  insist(['VALID', 'INVALID', 'UNRESOLVED'].includes(result.presentation), 'Unknown presentation status');
  exactKeys(result.execution, ['status', 'limits', 'progress']);
  insist(['COMPLETE', 'LIMITED', 'ERROR'].includes(result.execution.status), 'Unknown execution status');
  insist(Array.isArray(result.execution.limits), 'Result limits must be an array');
  const names = new Set();
  for (const item of result.execution.limits) {
    exactKeys(item, ['name', 'bound']);
    insist(typeof item.name === 'string' && isNat(item.bound) && !names.has(item.name), 'Invalid result limit'); names.add(item.name);
  }
  exactKeys(result.execution.progress, ['completed_policies', 'expanded_nodes']);
  insist(isNat(result.execution.progress.expanded_nodes), 'expanded_nodes is not Nat');
  insist(Array.isArray(result.execution.progress.completed_policies) && result.execution.progress.completed_policies.every(isID), 'Invalid completed policies');
  for (const field of ['diagnostics', 'checks', 'policies']) insist(Array.isArray(result[field]), `${field} must be an array`);
  function cell(item) {
    insist(item && ['DEFINED', 'OUTSIDE_DOMAIN', 'BLOCKED'].includes(item.state), 'Unknown cell state');
    if (item.state === 'DEFINED') exactKeys(item, ['state', 'value', 'checks']);
    else if (item.state === 'OUTSIDE_DOMAIN') exactKeys(item, ['state', 'reasons', 'checks']);
    else exactKeys(item, ['state', 'reasons']);
    if ('checks' in item) insist(Array.isArray(item.checks) && item.checks.every(isID), 'Invalid cell checks');
    if ('reasons' in item) insist(Array.isArray(item.reasons) && item.reasons.length > 0 && item.reasons.every(isID), 'Invalid cell reasons');
  }
  cell(result.decision); cell(result.integration);
  if (result.presentation === 'INVALID') insist(result.policies.length === 0 && result.decision.state === 'BLOCKED' && result.integration.state === 'BLOCKED', 'INVALID presentation contains mathematical conclusions');
  if (result.execution.status !== 'COMPLETE') {
    insist(result.integration.state !== 'DEFINED', 'Incomplete execution claims integration');
    if (result.decision.state === 'DEFINED') insist(result.decision.value.selection?.state !== 'DEFINED', 'Incomplete execution claims selection');
  }
  return result;
}
