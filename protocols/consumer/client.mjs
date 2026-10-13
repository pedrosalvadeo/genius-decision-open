import { StdioTransport } from './transport.mjs';
import { byteEnvelope, ConsumerError, decodeEnvelope, exactKeys, inspectResult, insist, isNat, sha256 } from './bytes.mjs';

export { ConsumerError, byteEnvelope, decodeEnvelope, inspectResult, sha256 } from './bytes.mjs';
export { RpcError } from './transport.mjs';

export const CAPABILITIES = ['evaluate', 'verify_result', 'verify_certificate'];
export const KERNEL_LIMITS = ['max_nodes', 'max_operations', 'max_seconds', 'max_input_bytes', 'max_integer_digits'];
export const TRANSPORT_LIMITS = {
  max_frame_bytes: '16777216', max_input_bytes: '2097152', max_candidate_bytes: '8388608',
  max_response_bytes: '33554432', max_batch_items: '16', max_limit_digits: '12',
};
const IDENTITIES = {
  protocol_version: 'genius-protocols/1.0', protocols_version: 'GENIUS-PROTOCOLS-1.0.0',
  kernel_version: 'GENIUS-KERNEL-1.0.1', specification: 'GENIUS-SPEC-1.0.0',
  theory_snapshot: 'GENIUS-THEORY-2026-09-23-S2', profile: 'FP1_FINITE_EXACT',
  input_format: 'genius-fp1/1.0', result_format: 'genius-fp1-result/1.0',
  cancellation: 'PROCESS_TERMINATION_ONLY',
};
function sameSet(actual, expected) {
  return Array.isArray(actual) && actual.length === expected.length && new Set(actual).size === actual.length && expected.every(value => actual.includes(value));
}
export function checkCapabilities(info, offer, required) {
  exactKeys(info, [...Object.keys(IDENTITIES), 'capabilities', 'transport_limits', 'default_kernel_limits', 'allowed_kernel_limits', 'environment']);
  for (const [key, expected] of Object.entries(IDENTITIES)) insist(info[key] === expected, `Incompatible ${key}`);
  insist(offer.includes(info.protocol_version), 'Selected protocol was not offered');
  insist(sameSet(info.capabilities, CAPABILITIES) && required.every(cap => info.capabilities.includes(cap)), 'Incompatible capabilities');
  exactKeys(info.transport_limits, Object.keys(TRANSPORT_LIMITS));
  for (const [key, expected] of Object.entries(TRANSPORT_LIMITS)) insist(info.transport_limits[key] === expected, `Incompatible ${key}`);
  exactKeys(info.default_kernel_limits, []);
  insist(sameSet(info.allowed_kernel_limits, KERNEL_LIMITS), 'Incompatible Kernel limit names');
  exactKeys(info.environment, ['python_recursion_depth']);
  insist(isNat(info.environment.python_recursion_depth), 'Recursion depth must be Nat');
  return info;
}

export function checkLimits(limits) {
  exactKeys(limits, [], KERNEL_LIMITS);
  for (const [name, value] of Object.entries(limits)) insist(isNat(value) && value.length <= 12, `${name} must be a canonical Nat string of at most 12 digits`, 'LOCAL_INPUT');
  return limits;
}

export class GeniusClient {
  constructor(options = {}) { this.transport = new StdioTransport(options); this.state = 'UNINITIALIZED'; this.capabilities = null; }

  async initialize({ protocolVersions = ['genius-protocols/1.0'], requiredCapabilities = CAPABILITIES, signal } = {}) {
    insist(this.state === 'UNINITIALIZED', 'Client initialization is allowed once', 'LOCAL_STATE');
    this.state = 'NEGOTIATING';
    try {
      const info = await this.transport.request('genius.initialize', { protocol_versions: protocolVersions, required_capabilities: requiredCapabilities }, { signal });
      this.capabilities = checkCapabilities(info, protocolVersions, requiredCapabilities);
      this.state = 'READY';
      return info;
    } catch (error) {
      // An unsuccessful negotiation never authorizes input transmission. Open
      // a new client explicitly; no retry can silently downgrade semantics.
      this.state = 'FAILED';
      await this.transport.close();
      throw error;
    }
  }

  params(input, limits, candidate) {
    insist(this.state === 'READY', 'A compatible handshake is required before instance transmission', 'LOCAL_STATE');
    const request = { input: byteEnvelope(input) };
    insist(BigInt(input.length) <= BigInt(this.capabilities.transport_limits.max_input_bytes), 'Input exceeds negotiated transport maximum', 'LOCAL_LIMIT');
    if (candidate !== undefined) {
      request.candidate = byteEnvelope(candidate);
      insist(BigInt(candidate.length) <= BigInt(this.capabilities.transport_limits.max_candidate_bytes), 'Candidate exceeds negotiated transport maximum', 'LOCAL_LIMIT');
    }
    if (limits !== undefined) request.limits = checkLimits(limits);
    return request;
  }

  async evaluate(input, { limits, signal, timeoutMs } = {}) {
    insist(Buffer.isBuffer(input), 'Input must be a Buffer', 'LOCAL_INPUT');
    input = Buffer.from(input);
    const params = this.params(input, limits);
    const response = await this.transport.request('genius.evaluate', params, { signal, timeoutMs });
    exactKeys(response, ['input', 'result']);
    const inputBytes = decodeEnvelope(response.input, this.capabilities.transport_limits.max_input_bytes);
    insist(inputBytes.equals(input), 'Echoed input bytes differ from the original request');
    const resultBytes = decodeEnvelope(response.result, this.capabilities.transport_limits.max_response_bytes);
    const result = inspectResult(resultBytes, params.input.sha256);
    return { inputBytes, resultBytes, inputDigest: params.input.sha256, resultDigest: response.result.sha256, result };
  }

  async verify(method, input, candidate, { limits, signal, timeoutMs } = {}) {
    insist(Buffer.isBuffer(input) && Buffer.isBuffer(candidate), 'Input and candidate must be Buffers', 'LOCAL_INPUT');
    input = Buffer.from(input); candidate = Buffer.from(candidate);
    const params = this.params(input, limits, candidate);
    const response = await this.transport.request(method, params, { signal, timeoutMs });
    exactKeys(response, ['input_digest', 'artifact_digest', 'report']);
    insist(response.input_digest === params.input.sha256, 'Verification input digest mismatch');
    insist(response.artifact_digest === params.candidate.sha256, 'Verification artifact digest mismatch');
    exactKeys(response.report, ['valid', 'status', 'errors']);
    insist(({ VALID: true, INVALID: false, INCOMPLETE: null })[response.report.status] === response.report.valid && ['VALID', 'INVALID', 'INCOMPLETE'].includes(response.report.status), 'Invalid verification status/value pairing');
    insist(Array.isArray(response.report.errors) && response.report.errors.every(item => typeof item === 'string'), 'Invalid verification errors');
    return { inputBytes: Buffer.from(input), candidateBytes: Buffer.from(candidate), inputDigest: response.input_digest, artifactDigest: response.artifact_digest, report: response.report };
  }

  verifyResult(input, candidate, options) { return this.verify('genius.verify_result', input, candidate, options); }
  verifyCertificate(input, candidate, options) { return this.verify('genius.verify_certificate', input, candidate, options); }
  async close() { this.state = 'CLOSED'; await this.transport.close(); }
}
