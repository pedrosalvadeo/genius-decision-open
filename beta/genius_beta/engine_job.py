"""Isolated child: strict input, real R2/R3 execution, bounded complete store archive."""
import base64
import contextlib
import ctypes
import hashlib
import io
import json
import os
from pathlib import Path
import resource
import signal
import sys
import zipfile


def install_parent_death_guard():
    """Linux: losing the worker terminates this private group, including R2 children.

    Worker passes its PID and starts a new session. The two PID checks cover a
    parent that dies before PR_SET_PDEATHSIG was installed. Fail closed if the
    kernel cannot provide the guard; deployment targets Linux explicitly.
    """
    expected=int(os.environ['GENIUS_WORKER_PID'])
    if expected<=1 or os.getpgrp()!=os.getpid():
        raise RuntimeError('Invalid engine process supervision')

    def kill_group(*_):
        os.killpg(os.getpgrp(),signal.SIGKILL)

    # R2 owns SIGINT/SIGTERM, so use a dedicated signal it never replaces.
    signal.signal(signal.SIGUSR1,kill_group)
    if os.getppid()!=expected:
        kill_group()
    libc=ctypes.CDLL(None,use_errno=True)
    # Linux PR_SET_PDEATHSIG=1; the signal targets only this process initially.
    if libc.prctl(1,signal.SIGUSR1,0,0,0)!=0:
        raise OSError(ctypes.get_errno(),'Parent-death supervision unavailable')
    if os.getppid()!=expected:
        kill_group()


def main():
    install_parent_death_guard()
    resource.setrlimit(resource.RLIMIT_CPU,(30,30))
    resource.setrlimit(resource.RLIMIT_AS,(1024*1024*1024,1024*1024*1024))
    resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024*1024,4*1024*1024))
    resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
    os.umask(0o077)
    from .adapter import execute_profile, AdmissionError
    payload=json.loads(sys.stdin.buffer.read(131073))
    case_dir=Path(sys.argv[1])/'case'
    try:
        with contextlib.redirect_stdout(sys.stderr):
            result=execute_profile(payload,case_dir)
    except AdmissionError as exc:
        # Adapter emits only fixed machine codes; never return stderr or input text.
        allowed={'PAYLOAD_MUST_BE_OBJECT','PROFILE_FIELDS','EVIDENCE_ORIGIN','PROFILE_MISMATCH','PROCESSING_PERMISSION_REQUIRED','FORMAL_SCOPE_ACKNOWLEDGEMENT_REQUIRED','BETA_ARTIFACT_TOO_LARGE','HOURS_REQUIRE_EXACT_TEXT_OR_NULL','HOURS_NONNEGATIVE_DECIMAL_OR_RATIONAL_REQUIRED','HOURS_ASSIGNMENT_COUNT','HOURS_ASSIGNMENT_FIELDS','HOURS_ASSIGNMENT_ID','DUPLICATE_ASSIGNMENT_ID','FDQ_QUERY_KIND','FDQ_REQUIRES_ORIGINAL_JSON_TEXT','FDQ_INVALID_STRICT_JSON','FDQ_ARTIFACT_MUST_BE_OBJECT','FDQ_CERTIFICATE_QUERY_MUST_MATCH_EXACTLY','FDQ_CERTIFICATE_CLAIM_MUST_MATCH_EXACTLY','FDQ_ORIGINAL_BYTE_DIGEST_MISMATCH','BETA_FDQ_FAMILY_LIMIT','FDQ_INPUT_OUTSIDE_STRUCTURAL_PROFILE','FDQ_ONLY_HORIZON_ONE','PROFILE_OUTSIDE_BETA','NEW_DOSSIER_PATH_REQUIRED','R3_RESPONSE_BINDING_FAILED'}
        code=str(exc)
        allowed.add('CHOICE_PROFILE_REJECTED')
        sys.stdout.write(json.dumps({'admission_error':code if code in allowed else 'ADMISSION_REJECTED'}))
        return
    buffer=io.BytesIO()
    total=0
    with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(case_dir.rglob('*')):
            if path.is_symlink():
                raise ValueError('Store symlink not allowed')
            if path.is_file():
                total+=path.stat().st_size
                if total>2*1024*1024:
                    raise ValueError('Store size limit')
                archive.write(path,path.relative_to(case_dir).as_posix())
    raw=buffer.getvalue()
    if len(raw)>1024*1024:
        raise ValueError('Archive size limit')
    output=dict(result=result,archive_b64=base64.b64encode(raw).decode(),archive_sha256=hashlib.sha256(raw).hexdigest())
    encoded=json.dumps(output,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()
    if len(encoded)>2*1024*1024:
        raise ValueError('Output size limit')
    sys.stdout.buffer.write(encoded)


if __name__=='__main__':
    main()
