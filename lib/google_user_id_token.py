#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Utility library for reading user information from an id_token.
This is an experimental library that can temporarily be used to extract
a user from an id_token.  The functionality provided by this library
will be provided elsewhere in the future.
"""
import base64
import time
try:
    import json
except ImportError:
    import simplejson as json
try:
    from Crypto.Hash import SHA256
    from Crypto.PublicKey import RSA
    _CRYPTO_LOADED = True
except ImportError:
    _CRYPTO_LOADED = False
_CLOCK_SKEW_SECS = 300
_MAX_TOKEN_LIFETIME_SECS = 86400
_DEFAULT_CERT_URI = ('https://www.googleapis.com/service_accounts/v1/metadata/'
                    'raw/federated-signon@system.gserviceaccount.com')

# https://www.googleapis.com/oauth2/v2/certs
_DEFAULT_CERTS = '''
{
    "keys": [
        {
            "kty": "RSA",
            "alg": "RS256",
            "use": "sig",
            "kid": "1672994d92efd7f94210f6e6558bbfc6819e280b",
            "n": "AMHlELIXrXphInB/85TVOXlkqoFNtPrz+t41yq+GeSSdwk58RhmBOVMCuV+ZAThUlN1gK2Kht/twbKKFAZnhhHYjOwPewJmGTjq1c7nItNfr0B7y9HDYv1YKl9GRV3sC+/R6UAMmv+9ikgErW5WRlTHfOxoagXiJyYMAxCtMqsZ5",
            "e": "AQAB"
        },
        {
            "kty": "RSA",
            "alg": "RS256",
            "use": "sig",
            "kid": "85385898cd069b16c7aeac9c6550e31c442f320e",
            "n": "AJe2Dal9CL4I6q1GtIG29y54118Psb2jUF/IlFZM8GC0W4D17hJ7aIRjCWLvWr5viPKUp8RmH1xjwBUVSCxUIEP+U/1RtILa9xQV/tDDgs5AJEFUR9Z/IeNU3C7grtpwYHYWFT+Efwa9u2EQd3ewzl/74C6cd7Rv1LU312aIaV13",
            "e": "AQAB"
        }
    ]
}
'''


def parse_id_token(id_token):
    now = long(time.time())
    return _verify_signed_jwt_with_certs(id_token, now)


class _AppIdentityError(Exception):
    pass


def _urlsafe_b64decode(b64string):
    b64string = b64string.encode('ascii')
    padded = b64string + '=' * ((4 - len(b64string)) % 4)
    return base64.urlsafe_b64decode(padded)


def _b64_to_long(b):
    b = b.encode('ascii')
    b += '=' * ((4 - len(b)) % 4)
    b = base64.b64decode(b)
    return long(b.encode('hex'), 16)


def _verify_signed_jwt_with_certs(
        jwt, time_now,
        certs=_DEFAULT_CERTS):
    """Verify a JWT against public certs.
    See http://self-issued.info/docs/draft-jones-json-web-token.html.
    The PyCrypto library included with Google App Engine is severely limited and
    so you have to use it very carefully to verify JWT signatures. The first
    issue is that the library can't read X.509 files, so we make a call to a
    special URI that has the public cert in modulus/exponent form in JSON.
    The second issue is that the RSA.verify method doesn't work, at least for
    how the JWT tokens are signed, so we have to manually verify the signature
    of the JWT, which means hashing the signed part of the JWT and comparing
    that to the signature that's been encrypted with the public key.
    Args:
        jwt: string, A JWT.
        time_now: The current time, as a long (eg. long(time.time())).
        certs: string, certs in JSON format.
    Returns:
        dict, The deserialized JSON payload in the JWT.
    Raises:
        _AppIdentityError: if any checks are failed.
    """
    segments = jwt.split('.')
    if len(segments) != 3:
        raise _AppIdentityError('Wrong number of segments in token: %s' % jwt)
    signed = '%s.%s' % (segments[0], segments[1])
    signature = _urlsafe_b64decode(segments[2])
    lsignature = long(signature.encode('hex'), 16)
    header_body = _urlsafe_b64decode(segments[0])
    try:
        header = json.loads(header_body)
    except:
        raise _AppIdentityError('Can\'t parse header: %s' % header_body)

    if header.get('alg') != 'RS256':
        raise _AppIdentityError('Unexpected encryption algorithm: %s' % header.get('alg'))
    json_body = _urlsafe_b64decode(segments[1])
    try:
        parsed = json.loads(json_body)
    except:
        raise _AppIdentityError('Can\'t parse token: %s' % json_body)
    if certs is None:
        raise _AppIdentityError('Unable to retrieve certs needed to verify the signed JWT: %s' % jwt)
    if not _CRYPTO_LOADED:
        raise _AppIdentityError('Unable to load pycrypto library.  Can\'t verify '
                                'id_token signature.  See http://www.pycrypto.org '
                                'for more information on pycrypto.')
    verified = False
    certs = json.loads(certs)
    for keyvalue in certs['keys']:
        modulus = _b64_to_long(keyvalue['n'])
        exponent = _b64_to_long(keyvalue['e'])
        key = RSA.construct((modulus, exponent))
        local_hash = SHA256.new(signed).hexdigest()
        local_hash = local_hash.zfill(64)
        hexsig = '%064x' % key.encrypt(lsignature, '')[0]
        verified = (hexsig[-64:] == local_hash)
        if verified:
            break
    if not verified:
        raise _AppIdentityError('Invalid token signature: %s' % jwt)
    iat = parsed.get('iat')
    if iat is None:
        raise _AppIdentityError('No iat field in token: %s' % json_body)
    earliest = iat - _CLOCK_SKEW_SECS
    exp = parsed.get('exp')
    if exp is None:
        raise _AppIdentityError('No exp field in token: %s' % json_body)
    if exp >= time_now + _MAX_TOKEN_LIFETIME_SECS:
        raise _AppIdentityError('exp field too far in future: %s' % json_body)
    latest = exp + _CLOCK_SKEW_SECS
    if time_now < earliest:
        raise _AppIdentityError('Token used too early, %d < %d: %s' %
                                (time_now, earliest, json_body))
    if time_now > latest:
        raise _AppIdentityError('Token used too late, %d > %d: %s' %
                                (time_now, latest, json_body))
    return parsed
