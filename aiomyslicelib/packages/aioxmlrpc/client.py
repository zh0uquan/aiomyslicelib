"""
XML-RPC Client with asyncio.
This module adapt the ``xmlrpc.client`` module of the standard library to
work with asyncio.
"""

import asyncio
import logging
from xmlrpc import client

import aiohttp


__ALL__ = ['ServerProxy', 'Fault', 'ProtocolError']

# you don't have to import xmlrpc.client from your code
Fault = client.Fault
ProtocolError = client.ProtocolError

log = logging.getLogger(__name__)


class _Method:
    # some magic to bind an XML-RPC method to an RPC server.
    # supports "nested" methods (e.g. examples.getStateName)
    def __init__(self, send, name):
        self.__send = send
        self.__name = name

    def __getattr__(self, name):
        return _Method(self.__send, "%s.%s" % (self.__name, name))

    @asyncio.coroutine
    def __call__(self, *args):
        ret = yield from self.__send(self.__name, args)
        return ret


class AioTransport(client.Transport):
    """
    ``xmlrpc.Transport`` subclass for asyncio support
    """

    user_agent = 'python/aioxmlrpc'

    def __init__(self, use_https, *, use_datetime=False,
                 use_builtin_types=False, loop, context=None):
        super().__init__(use_datetime, use_builtin_types)
        self.use_https = use_https
        self._loop = loop
        self._context = context
        self._connector = aiohttp.TCPConnector(loop=self._loop,
                                               ssl_context=self._context)

    @asyncio.coroutine
    def request(self, host, handler, request_body, verbose):
        """
        Send the XML-RPC request, return the response.
        This method is a coroutine.
        """
        headers = {'User-Agent': self.user_agent,
                   # Proxy-Connection': 'Keep-Alive',
                   # 'Content-Range': 'bytes oxy1.0/-1',
                   'Accept': 'text/xml',
                   'Content-Type': 'text/xml'}
        url = self._build_url(host, handler)
        response = None
        try:
            response = yield from aiohttp.request(
                'POST', url, headers=headers, data=request_body,
                connector=self._connector, loop=self._loop)
            body = yield from response.text()
            if response.status != 200:
                raise ProtocolError(url, response.status,
                                    body, response.headers)
        except ProtocolError:
            raise
        except Exception as exc:
            log.error('Unexpected error', exc_info=True)
            raise ProtocolError(url, response.status,
                                str(exc), response.headers)
        return self.parse_response(body)

    def parse_response(self, body):
        """
        Parse the xmlrpc response.
        """
        p, u = self.getparser()
        p.feed(body)
        p.close()
        return u.close()

    def _build_url(self, host, handler):
        """
        Build a url for our request based on the host, handler and use_http
        property
        """
        scheme = 'https' if self.use_https else 'http'
        return '%s://%s%s' % (scheme, host, handler)

    def close(self):
        self._connector.close()


class ServerProxy(client.ServerProxy):
    """
    ``xmlrpc.ServerProxy`` subclass for asyncio support
    """

    def __init__(self, uri, transport=None, encoding=None, verbose=False,
                 allow_none=False, use_datetime=False, use_builtin_types=False,
                 loop=None, context=None):
        self._loop = loop or asyncio.get_event_loop()
        if not transport:
            transport = AioTransport(uri.startswith('https://'),
                                     use_datetime=True,
                                     loop=self._loop,
                                     context=context)
        super().__init__(uri, transport, encoding, verbose, allow_none,
                         use_datetime, context)

    @asyncio.coroutine
    def __request(self, methodname, params):
        # call a method on the remote server
        request = client.dumps(
            params, methodname,
            encoding=self.__encoding,
            allow_none=self.__allow_none).encode(self.__encoding)

        response = yield from self.__transport.request(
            self.__host,
            self.__handler,
            request,
            verbose=self.__verbose)

        if len(response) == 1:
            response = response[0]

        return response

    def close(self):
        self.__transport.close()

    def __getattr__(self, name):
        return _Method(self.__request, name)

    def __aenter__(self):
        return self

    def __aexit__(self, exc_type, exc, traceback):
        # TODO: we need to check for the unexcepted errors
        self.close()
