from app.models.registry_types import ModelDescriptor
from app.services.runtime import PeakVoxRuntime


class _Adapter:
    def __init__(self, descriptor, healthy):
        self.descriptor = descriptor
        self._healthy = healthy

    @property
    def model_id(self):
        return self.descriptor.id

    async def health_check(self) -> bool:
        return self._healthy


def _rt(healthy):
    rt = PeakVoxRuntime()
    rt.register_adapter(_Adapter(
        ModelDescriptor(id="d", name="d", description="d", provider="p", is_default=True),
        healthy,
    ))
    return rt


async def test_is_ready_reflects_default_adapter_health():
    assert await _rt(True).is_ready() is True
    assert await _rt(False).is_ready() is False


async def test_is_ready_false_when_no_adapters():
    assert await PeakVoxRuntime().is_ready() is False


def test_is_generating_delegates_to_registry():
    rt = _rt(True)
    # No generation in flight in a fresh process → not generating.
    assert rt.is_generating is False
