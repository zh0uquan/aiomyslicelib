aiomyslicelib
=============


Introduction
------------

Aiomyslicelib is an abstract implementation of the myslicelib(what I did in Onelab, which
was mainly implemented by multithreading). by taking advantage of the new python feature asyncio,
for use in asynchronous interactions, which I believe will significantly improve the performance
of original code due to I/O bound is common case in Onelab application.

Basic usage:

.. code-block:: python

    import asyncio
    from aiomyslicelib import (
        FacadeApi, Authentication, Endpoint
    )

    loop = asyncio.get_event_loop()

    # simple config
    path = "/var/myslice/"
    pkey = path + "myslice.pkey"
    hrn = "onelab.myslice"
    email = "support@myslice.info"
    cert = path + "myslice.cert"

    s.authentication = Authentication(hrn=hrn, email=email,
                                      certificate=cert, private_key=pkey)
    endpoint = Endpoint(url="https://localhost:6080", type="Reg")
    authentication = Authentication(hrn=hrn, email=email,
                                    certificate=cert, private_key=pkey)

    api = FacadeApi(endpoint=endpoint, authentication=authentication)

    # async init of the facade api
    loop.run_until_complete(api._init())
    # get the version of the remote or local Sfa server
    loop.run_until_complete(api.version())

An Overview of the Architecture
===============================
See the image below

.. image 
