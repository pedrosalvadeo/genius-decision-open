"""Genius Decision finite exact reference kernel, version 1.0.1."""
from .common import VERSION as __version__


def evaluate(raw, limits=None):
    from .engine import evaluate as run
    return run(raw, limits)


def verify_result(raw, result, limits=None):
    from .verifier import verify_result as verify
    return verify(raw, result, limits)


def verify_decisive_certificate(raw, envelope, limits=None):
    from .verifier import verify_decisive_certificate as verify
    return verify(raw, envelope, limits)
