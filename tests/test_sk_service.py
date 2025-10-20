"""Tests for Semantic Kernel service."""
import pytest
from unittest.mock import AsyncMock, Mock, patch

from services.bls_service import BLSService
from services.sk_service import SemanticKernelService


@pytest.fixture
def mock_bls_service():
    """Create mock BLS service."""
    service = Mock(spec=BLSService)
    service.get_series_data.return_value = {
        "status": "REQUEST_SUCCEEDED",
        "Results": {
            "series": [{
                "seriesID": "LNS14000000",
                "data": [{
                    "year": "2023",
                    "period": "M12",
                    "periodName": "December",
                    "value": "3.7"
                }]
            }]
        }
    }
    return service


@pytest.mark.asyncio
class TestSemanticKernelService:
    """Test cases for Semantic Kernel service."""
    
    async def test_fallback_intent_extraction(self, mock_bls_service):
        """Test fallback intent extraction."""
        sk_service = SemanticKernelService(
            api_key="test_key",
            bls_service=mock_bls_service
        )
        
        intent = sk_service._fallback_intent_extraction(
            "What's the unemployment rate?",
            2023
        )
        
        assert intent["data_type"] == "unemployment"
        assert "LNS14000000" in intent["series_ids"]
        assert intent["start_year"] == "2018"
        assert intent["end_year"] == "2023"
    
    async def test_fetch_bls_data(self, mock_bls_service):
        """Test BLS data fetching."""
        sk_service = SemanticKernelService(
            api_key="test_key",
            bls_service=mock_bls_service
        )
        
        intent = {
            "series_ids": ["LNS14000000"],
            "start_year": "2020",
            "end_year": "2023"
        }
        
        data = sk_service._fetch_bls_data(intent)
        
        assert data is not None
        assert data["status"] == "REQUEST_SUCCEEDED"