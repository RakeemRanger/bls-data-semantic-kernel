"""Tests for BLS service."""
import pytest
from unittest.mock import Mock, patch

from services.bls_service import BLSService


@pytest.fixture
def bls_service():
    """Create BLS service instance."""
    return BLSService(api_key="test_key")


@pytest.fixture
def mock_bls_response():
    """Mock BLS API response."""
    return {
        "status": "REQUEST_SUCCEEDED",
        "Results": {
            "series": [
                {
                    "seriesID": "LNS14000000",
                    "data": [
                        {
                            "year": "2023",
                            "period": "M12",
                            "periodName": "December",
                            "value": "3.7",
                            "footnotes": []
                        }
                    ]
                }
            ]
        }
    }


class TestBLSService:
    """Test cases for BLS service."""
    
    def test_init(self, bls_service):
        """Test service initialization."""
        assert bls_service.api_key == "test_key"
        assert bls_service.base_url == "https://api.bls.gov/publicAPI/v2"
        assert bls_service.session is not None
    
    def test_search_series_by_keyword(self, bls_service):
        """Test series search by keyword."""
        result = bls_service.search_series_by_keyword("unemployment")
        assert isinstance(result, list)
        assert "LNS14000000" in result
    
    def test_invalid_year_range(self, bls_service):
        """Test invalid year range."""
        with pytest.raises(ValueError):
            bls_service.get_series_data(
                series_ids=["LNS14000000"],
                start_year="2023",
                end_year="2020"
            )
    
    def test_too_many_series(self, bls_service):
        """Test too many series IDs."""
        series_ids = [f"SERIES{i}" for i in range(51)]
        with pytest.raises(ValueError):
            bls_service.get_series_data(
                series_ids=series_ids,
                start_year="2020",
                end_year="2023"
            )
    
    @patch('requests.Session.post')
    def test_get_series_data_success(self, mock_post, bls_service, mock_bls_response):
        """Test successful data retrieval."""
        mock_post.return_value.json.return_value = mock_bls_response
        mock_post.return_value.raise_for_status = Mock()
        
        result = bls_service.get_series_data(
            series_ids=["LNS14000000"],
            start_year="2020",
            end_year="2023"
        )
        
        assert result["status"] == "REQUEST_SUCCEEDED"
        assert "Results" in result