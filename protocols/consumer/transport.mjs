import { spawn } from 'node:child_process';
import { ConsumerError, exactKeys, insist, strictJSON } from './bytes.mjs';

export class RpcError extends ConsumerError {
  constructor(error) { super('RPC_ERROR', error.message, error); this.rpcCode = error.code; }
}

// JSON-RPC 2.0 one-JSON-value-per-LF stdio transport. No shell and no shared
// Python objects: only the process pipes cross the language boundary.
export class StdioTransport {
  constructor({ command = 'python3', args = ['-m', 'genius_protocols'], cwd, env = process.env,
    timeoutMs = 60000, maxRequestBytes = 16 * 1024 * 1024,
    maxResponseBytes = 32 * 1024 * 1024, onFrame } = {}) {
    this.timeoutMs = timeoutMs;
    this.maxRequestBytes = maxRequestBytes;
    this.maxResponseBytes = maxResponseBytes;
    this.onFrame = onFrame;
    this.pending = new Map();
    this.nextID = 0n;
    this.buffer = Buffer.alloc(0);
    this.stderr = Buffer.alloc(0);
    this.ended = null;
    this.child = spawn(command, args, { cwd, env, stdio: ['pipe', 'pipe', 'pipe'], shell: false });
    this.closed = new Promise(resolve => { this.resolveClosed = resolve; });
    this.child.stderr.on('data', chunk => {
      this.stderr = Buffer.concat([this.stderr, chunk]).subarray(-65536);
    });
    this.child.stdout.on('data', chunk => this.receive(chunk));
    this.child.stdout.on('error', error => this.fail(new ConsumerError('TRANSPORT_IO', error.message)));
    this.child.stdin.on('error', error => this.fail(new ConsumerError('TRANSPORT_IO', error.message)));
    this.child.on('error', error => this.fail(new ConsumerError('TRANSPORT_START', error.message)));
    this.child.on('close', (code, signal) => {
      this.fail(new ConsumerError('TRANSPORT_CLOSED', 'Server closed before a complete reply',
        { exit_code: code, signal, trailing_bytes: this.buffer.length, stderr: this.stderr.toString('utf8') }), false);
      this.resolveClosed({ code, signal });
    });
  }

  receive(chunk) {
    if (this.ended) return;
    this.buffer = Buffer.concat([this.buffer, chunk]);
    try {
      let end;
      while ((end = this.buffer.indexOf(10)) >= 0) {
        insist(end <= this.maxResponseBytes, 'Response frame exceeds consumer maximum');
        const frame = this.buffer.subarray(0, end);
        this.buffer = this.buffer.subarray(end + 1);
        if (this.onFrame) this.onFrame('receive', Buffer.from(frame));
        const response = strictJSON(frame);
        const isError = Object.hasOwn(response, 'error');
        exactKeys(response, ['jsonrpc', 'id', isError ? 'error' : 'result']);
        insist(response.jsonrpc === '2.0' && typeof response.id === 'string', 'Invalid response version or ID');
        const pending = this.pending.get(response.id);
        insist(pending, `Unexpected or duplicate response ID ${response.id}`);
        if (isError) {
          exactKeys(response.error, ['code', 'message']);
          insist(Number.isSafeInteger(response.error.code) && typeof response.error.message === 'string', 'Invalid JSON-RPC error');
        }
        this.pending.delete(response.id);
        pending.cleanup();
        if (isError) {
          pending.reject(new RpcError(response.error));
        } else pending.resolve(response.result);
      }
      insist(this.buffer.length <= this.maxResponseBytes, 'Unterminated response frame exceeds consumer maximum');
    } catch (error) { this.fail(error); }
  }

  request(method, params, { signal, timeoutMs = this.timeoutMs } = {}) {
    if (this.ended) return Promise.reject(this.ended);
    if (this.pending.size) return Promise.reject(new ConsumerError('LOCAL_STATE', 'This serial transport requires waiting for the pending response'));
    if (signal?.aborted) return Promise.reject(new ConsumerError('CANCELLED', 'Caller cancelled before sending request'));
    const id = `consumer-${++this.nextID}`;
    const frame = Buffer.from(JSON.stringify({ jsonrpc: '2.0', id, method, params }), 'utf8');
    if (frame.length > this.maxRequestBytes) return Promise.reject(new ConsumerError('LOCAL_LIMIT', 'Request frame exceeds consumer maximum'));
    return new Promise((resolve, reject) => {
      const abort = () => this.fail(new ConsumerError('CANCELLED', 'Caller cancelled the process session'));
      const timer = setTimeout(() => this.fail(new ConsumerError('TRANSPORT_TIMEOUT', 'No complete response before consumer deadline')), timeoutMs);
      const cleanup = () => { clearTimeout(timer); signal?.removeEventListener('abort', abort); };
      this.pending.set(id, { resolve, reject, cleanup });
      signal?.addEventListener('abort', abort, { once: true });
      try {
        if (this.onFrame) this.onFrame('send', Buffer.from(frame));
        this.child.stdin.write(Buffer.concat([frame, Buffer.from('\n')]), error => {
          if (error) this.fail(new ConsumerError('TRANSPORT_IO', error.message));
        });
      } catch (error) { this.fail(error); }
    });
  }

  fail(error, kill = true) {
    if (this.ended) return;
    this.ended = error instanceof Error ? error : new ConsumerError('TRANSPORT_IO', String(error));
    for (const pending of this.pending.values()) { pending.cleanup(); pending.reject(this.ended); }
    this.pending.clear();
    if (kill && !this.child.killed) this.child.kill('SIGTERM');
  }

  async close() {
    if (!this.ended) {
      this.fail(new ConsumerError('CLIENT_CLOSED', 'Consumer closed session'), false);
      this.child.stdin.end();
    }
    const force = setTimeout(() => this.child.kill('SIGKILL'), 2000);
    force.unref();
    await this.closed;
    clearTimeout(force);
  }
}
