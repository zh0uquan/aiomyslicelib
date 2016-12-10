import asyncio
import ssl  # NOQA

from .sfa import SfaAm, SfaReg
from .util import (
    Endpoint, Authentication
)
from .errors import MySliceLibSetupError
from typing import List

__all__ = ('FacadeApi', )


class FacadeApi(object):
    """
    This is the generic "facade" API interface to the actual API interfaces
    to the AM and Registry endpoints.
    Depending on the protocol a different AM and Registry API is needed,
    e.g. SFA needs two separate endpoints, MyPLC only one.

    This class will instantiate two classes, one am and one reg,
    if the protocol provides only one endpoint
    it will be used for both functions (am and reg).

    AM class will manage:
    - Resources list
    - Slice resource provisioning (with and without lease)

    Registry class will manage:
    - Slice creation, update, delete
    - Authority creation, update, delete
    - User creation, update, delete

    """
    _entities = [
        'testbed',
        'resource',
        'slice',
        'user',
        'authority',
        'lease',
        'project'
    ]

    _am = [
        'resource',
        'slice',
        'lease'
    ]

    _registry = [
        'slice',
        'user',
        'authority',
        'project'
    ]

    def __init__(
            self, endpoints: List[Endpoint], authentication: Authentication,
            loop: asyncio.AbstractEventLoop) -> None:

        if (not isinstance(endpoints, list) or
           (not all(isinstance(endpoint, Endpoint)
                    for endpoint in endpoints))):
            raise MySliceLibSetupError("API needs an object of type Endpoint")

        if not isinstance(authentication, Authentication):
            raise MySliceLibSetupError(
                "API needs an object of type Authentication")

        self.endpoints = endpoints
        self.authentication = authentication
        self._loop = loop or asyncio.get_event_loop()
        self.agents = None  # type: ignore

    async def _init(self) -> None:
        # at least one registry endpoint must be present
        self.registry = None
        self.ams = []  # type: List[SfaAm]

        for endpoint in self.endpoints:
            if (endpoint.protocol == "SFA") and (endpoint.type == "Reg"):
                self.registry = SfaReg(endpoint, self.authentication)
                registry_endpoint = endpoint
                break

        if not self.registry:
            raise MySliceLibSetupError("At least a Registry must be specified")

        await self.registry._init()

        # search for the AMs
        for endpoint in self.endpoints:
            if (endpoint.protocol == "SFA") and (endpoint.type == "AM"):
                am = SfaAm(endpoint,
                           SfaReg(registry_endpoint, self.authentication))
                self.ams.append(am)

        self.agents = self.ams + [self.registry]

    async def get(self):
        pass

    async def create(self):
        pass

    async def update(self):
        pass

    async def delete(self):
        pass
