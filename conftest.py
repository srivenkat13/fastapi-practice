import pytest


@pytest.fixture
def anyio_backend():
    # Async tests (marked @pytest.mark.anyio) run on asyncio, like uvicorn does.
    return "asyncio"
