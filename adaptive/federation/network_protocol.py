"""Ed25519 identities and immutable view envelopes. Signatures do not attest truth."""
import hashlib
import re
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from .core import canonical, fields
from .views import validate

POLICY = 'genius-network-2026-10-16-v1'
FORMAT = 'genius-signed-view/1'
ENROLL = 'genius-node-enrollment/1'


def hexbytes(value, length):
    if not isinstance(value,str) or not re.fullmatch('[0-9a-f]{'+str(length*2)+'}',value):
        raise ValueError('INVALID_KEY_OR_SIGNATURE')
    return bytes.fromhex(value)


def identity(public_key):
    return hashlib.sha256(hexbytes(public_key,32)).hexdigest()


def generate():
    key=Ed25519PrivateKey.generate()
    return dict(private_key=key.private_bytes_raw().hex(),public_key=key.public_key().public_bytes_raw().hex())


def sign(payload, private_key):
    return Ed25519PrivateKey.from_private_bytes(hexbytes(private_key,32)).sign(
        b'GENIUS_NETWORK_V1\x00'+canonical(payload)).hex()


def verify(payload, public_key, signature):
    try:
        Ed25519PublicKey.from_public_bytes(hexbytes(public_key,32)).verify(
            hexbytes(signature,64),b'GENIUS_NETWORK_V1\x00'+canonical(payload))
    except InvalidSignature:
        raise ValueError('SIGNATURE_INVALID') from None


def envelope(view, keys):
    payload=dict(format=FORMAT,node_id=identity(keys['public_key']),public_key=keys['public_key'],view=view)
    result=dict(payload,signature=sign(payload,keys['private_key']))
    verify_view(result)
    return result


def verify_view(value):
    fields(value,'format node_id public_key view signature')
    if value['format']!=FORMAT or value['node_id']!=identity(value['public_key']):
        raise ValueError('INVALID_ENVELOPE_IDENTITY')
    validate(value['view'])
    if value['view']['owner']!=value['node_id'] or value['view']['shareable'] is not True:
        raise ValueError('PUBLIC_OWNER_REQUIRED')
    verify({k:v for k,v in value.items() if k!='signature'},value['public_key'],value['signature'])
    return value['view']
