import ssl


def configure_tls_context(client_cert: str=None,
                          client_key: str=None) -> ssl.SSLContext:
    if hasattr(ssl, '_create_unverified_context'):
        context = ssl._create_unverified_context()
    else:
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

    context.load_cert_chain(client_cert, client_key, password=None)

    return context
