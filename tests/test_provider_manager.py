import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from provider_manager import ProviderManager, ProviderScore
from provider_client import ProviderClient


@pytest.fixture
def multiple_mock_providers():
    providers = []
    for i in range(3):
        provider = AsyncMock(spec=ProviderClient)
        provider.name = f"Provider{i}"
        provider.head.return_value = 111
        provider.get_average_latency.return_value = 0.1
        provider.get_error_ratio.return_value = 1
        providers.append(provider)
    return providers


@pytest.fixture
def provider_manager(multiple_mock_providers):
    return ProviderManager(
        providers=multiple_mock_providers,
        lag_thr=1.0,
        error_thr=0.1,
        halflife=60.0
    )

@pytest.fixture
def metrics_moc():
    metrics = MagicMock(spec=ProviderScore)
    metrics.is_healthy = False
    return metrics

class TestProviderManager:

    @pytest.mark.asyncio
    async def test_switch_to_healthy_provider(self, provider_manager, metrics_moc):
        metrics_moc.is_healthy = False
        provider_manager.metrics[1] = metrics_moc
        await provider_manager.switch_to_healthy_provider()

        assert provider_manager.active != provider_manager.providers[0]
        assert provider_manager.active != provider_manager.providers[1]
        assert provider_manager.active == provider_manager.providers[2]

    @pytest.mark.asyncio
    async def test_switch_provider_aborted_when_head_consensus(self, provider_manager, metrics_moc):
        active = provider_manager.active
        await provider_manager.switch_provider_consensus_based()
        assert provider_manager.active == active

    @pytest.mark.asyncio
    async def test_switch_provider_when_its_not_in_head_consensus(self, provider_manager, metrics_moc):
        rouge_provider = provider_manager.active
        rouge_provider.head.return_value = 5

        await provider_manager.switch_provider_consensus_based()
        assert provider_manager.active != rouge_provider
        assert await provider_manager.active.head() != rouge_provider.head()

    def test_provider_manager_empty_providers_raises_error(self):
        with pytest.raises(ValueError, match="At least one provider required"):
            ProviderManager(providers=[], lag_thr=1.0, error_thr=0.1, halflife=60.0)

    

    



