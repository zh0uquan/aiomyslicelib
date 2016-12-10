import ssl  # NOQA
import os
import asyncio  # NOQA

from OpenSSL import crypto

from .packages.aioxmlrpc.client import ServerProxy
from .errors import (
    MySliceLibSSLError, MySliceLibSetupError
)
from .utils.url import validateUrl
from .utils.certificate import Keypair, Certificate
from .tls import configure_tls_context
from typing import Iterable, Union

__all__ = (
    'Endpoint', 'Authentication',
    'SfaApi', 'SfaAm', 'SfaReg'
)


class Endpoint(object):
    """
    An endpoint specifies a remote API endpoint.
    type is the type of endpoint, e.g. AM, Reg
    protocol specifies the protocol, default is SFA
    url is the remote url

    name: name of the testbed/facility (not needed)

    """

    def __init__(
            self, type: str="AM", protocol: str="SFA",
            url: str=None, name: str=None,
            timeout: Union[float, int]=None) -> None:
        self._name = name
        self._type = type
        self.protocol = protocol
        if timeout:
            self.timeout = timeout
        else:
            self.timeout = 10
        if not url or not validateUrl(url):
            raise MySliceLibSetupError("URL not valid")
        else:
            self._url = url

    @property
    def url(self):
        return self._url

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type

    def __str__(self):
        return "Endpoint({_name}, {_type})".format(self._name, self._type)


class Authentication(object):

    def __init__(
            self, userid: str=None, password: str=None,
            email: str=None, hrn: str=None, private_key: str=None,
            certificate: Union[bytes, str]=None,
            credentials: Iterable=None) -> None:
        if not private_key or not email or not hrn:
            raise MySliceLibSetupError(
                "private key, email and hrn must be specified")
        self.userid = userid
        self.password = password
        self.email = email
        self._hrn = hrn
        self._private_key = private_key

        if not certificate:
            certificate = self.create_self_signed_cert(private_key)
        if not isinstance(certificate, str):
            certificate = certificate.decode('utf-8')

        if os.path.isfile(certificate):
            with open(certificate, "r") as f:
                certificate = f.read()

        self._certificate = certificate

        if credentials:
            self._credentials = credentials

    @property
    def credentials(self):
        return self._credentials

    @property
    def private_key(self):
        return self._private_key

    @property
    def hrn(self):
        return self._hrn

    @property
    def certificate(self):
        return self.certificate

    def create_self_signed_cert(self, private_key=None):
        if not private_key:
            # create a key pair
            k = crypto.PKey()
            k.generate_key(crypto.TYPE_RSA, 1024)
        else:
            k = crypto.load_privatekey(crypto.FILETYPE_PEM, private_key)

        # create a self-signed cert
        cert = crypto.X509()
        cert.get_subject().C = "FR"
        cert.get_subject().ST = "Paris"
        cert.get_subject().L = "Paris"
        cert.get_subject().O = "Onelab"
        # cert.get_subject().OU = ""
        cert.get_subject().CN = self.hrn.encode('latin1')
        cert.set_serial_number(1000)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(10 * 365 * 24 * 60 * 60)
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(k)
        cert.sign(k, 'sha1')

        return crypto.dump_certificate(crypto.FILETYPE_PEM, cert)

    def sign_certificate(self):
        keypair = Keypair(filename=self.private_key.encode('latin1'))
        self_signed = Certificate(subject=self.hrn)
        self_signed.set_pubkey(keypair)
        self_signed.set_issuer(keypair, subject=self.hrn.encode('latin1'))
        self_signed.set_data('email:' + self.email, 'subjectAltName')
        self_signed.sign()
        return self_signed.save_to_string()


class SfaApi(object):
    """
    This is the the base client for accessing to the sfa remote servers.
    The running status and remote server informations can be accessed
    by `self.version()` method.
    """

    def __init__(
            self, endpoint: Endpoint,
            authentication: Authentication,
            loop: asyncio.AbstractEventLoop=None) -> None:
        self.endpoint = endpoint
        self.authentication = authentication
        self._proxy = None  # type: ignore
        self._loop = loop or asyncio.get_event_loop()

    def setup_proxy(self) -> ServerProxy:
        context = self.load_context()
        if self._proxy is None:
            self._proxy = ServerProxy(self.endpoint.url, allow_none=True,
                                      verbose=False, use_datetime=True,
                                      context=context)
        return self._proxy

    def load_context(self) -> ssl.SSLContext:
        client_key = self.authentication.private_key
        client_cert = self.authentication.certificate

        try:
            context = configure_tls_context(client_cert, client_key)
        except:
            raise MySliceLibSSLError("Problem with certificate and/or key")
        return context

    async def version(self):
        self.proxy = self.setup_proxy()

        # We are using the `GetVersion` method provided from Remote Server
        result = await self.proxy.GerVersion()

        self.proxy.close()
        return result


class SfaReg(SfaApi):
    """
    An SfaReg client will talk to the registeration of testbeds, which stores
    all the certs/infos about AM Type Server, and help to manage AM Server.
    """
    _types = ['slice', 'user', 'authority']

    def __init__(
            self, endpoint: Endpoint, authentication: Authentication,
            loop: asyncio.AbstractEventLoop=None) -> None:
        super().__init__(endpoint, authentication, loop)

    async def _init(self) -> None:
        cert = self.authentication.certificate
        hrn = self.authentication.hrn

        self.user_credential = \
            await self.proxy.GetSelfCredential(cert, hrn, 'user')

    async def get(self):
        pass

    async def create(self):
        pass

    async def update(self):
        pass

    async def delete(self):
        pass


class SfaAm(SfaApi):
    """
    An SfaAm client will talk to Type AM Server.
    An Registry Server Client(SfaReg) is required to instantiate an SfaAm,
    because Reg Server will provide the sufficient authentication to this
    client during the RPC calls to AM Server.
    """

    def __init__(
            self, endpoint: Endpoint, registry: SfaReg,
            loop: asyncio.AbstractEventLoop=None) -> None:
        super().__init__(endpoint, registry.authentication, loop)
        self.registry = registry

    async def get(self):
        pass

    async def create(self):
        pass

    async def update(self):
        pass

    async def delete(self):
        pass
