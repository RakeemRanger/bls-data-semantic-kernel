"""BLS API service for fetching labor statistics data."""
import logging
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class BLSService:
    """Service for interacting with BLS API."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.bls.gov/publicAPI/v2"):
        """Initialize BLS service.
        
        Args:
            api_key: BLS API key (optional but recommended)
            base_url: BLS API base URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self.session = self._create_session()
        
        logger.info(f"BLS Service initialized with API key: {bool(api_key)}")
    
    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic."""
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def get_series_data(
        self,
        series_ids: List[str],
        start_year: str,
        end_year: str,
        catalog: bool = False
    ) -> Dict[str, Any]:
        """Fetch data for specified BLS series.
        
        Args:
            series_ids: List of BLS series identifiers
            start_year: Start year (YYYY)
            end_year: End year (YYYY)
            catalog: Include catalog metadata
            
        Returns:
            Dictionary containing series data
            
        Raises:
            ValueError: If parameters are invalid
            requests.HTTPError: If API request fails
        """
        if not series_ids:
            raise ValueError("At least one series ID is required")
        
        if len(series_ids) > 50:
            raise ValueError("Maximum 50 series IDs allowed per request")
        
        # Validate year format
        try:
            start = int(start_year)
            end = int(end_year)
            if start > end:
                raise ValueError("Start year must be <= end year")
        except ValueError as e:
            raise ValueError(f"Invalid year format: {e}")
        
        # Prepare request payload
        payload = {
            "seriesid": series_ids,
            "startyear": start_year,
            "endyear": end_year,
            "catalog": catalog
        }
        
        if self.api_key:
            payload["registrationkey"] = self.api_key
        
        logger.info(f"Fetching BLS data for {len(series_ids)} series: {start_year}-{end_year}")
        
        try:
            response = self.session.post(
                f"{self.base_url}/timeseries/data/",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") != "REQUEST_SUCCEEDED":
                error_messages = data.get("message", ["Unknown error"])
                raise ValueError(f"BLS API error: {error_messages}")
            
            logger.info(f"Successfully fetched data for {len(series_ids)} series")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error fetching BLS data: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            raise
    
    def get_single_series(
        self,
        series_id: str,
        start_year: str,
        end_year: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch data for a single series.
        
        Args:
            series_id: BLS series identifier
            start_year: Start year (YYYY)
            end_year: End year (YYYY)
            
        Returns:
            Series data dictionary or None
        """
        try:
            result = self.get_series_data([series_id], start_year, end_year)
            series_list = result.get("Results", {}).get("series", [])
            return series_list[0] if series_list else None
        except Exception as e:
            logger.error(f"Error fetching single series {series_id}: {e}")
            return None
    
    def search_series_by_keyword(self, keyword: str) -> List[str]:
        """Search for series IDs by keyword (simplified mapping).
        
        Args:
            keyword: Search keyword
            
        Returns:
            List of relevant series IDs
        """
        # Common series mappings
        keyword_map = {
            "unemployment": ["LNS14000000", "LNS14000006"],
            "cpi": ["CUUR0000SA0", "CUSR0000SA0"],
            "inflation": ["CUUR0000SA0"],
            "employment": ["CES0000000001", "LNS12000000"],
            "jobs": ["CES0000000001"],
            "labor force": ["LNS12300000", "LNS11300000"],
            "wages": ["CES0500000003", "CES0500000008"],
            "participation": ["LNS12300000"]
        }
        
        keyword_lower = keyword.lower()
        for key, series_ids in keyword_map.items():
            if key in keyword_lower:
                return series_ids
        
        return []
    
    def get_latest_value(self, series_id: str) -> Optional[Dict[str, str]]:
        """Get the most recent value for a series.
        
        Args:
            series_id: BLS series identifier
            
        Returns:
            Dictionary with latest year, period, and value
        """
        from datetime import datetime
        current_year = datetime.now().year
        
        try:
            series_data = self.get_single_series(
                series_id,
                str(current_year - 2),
                str(current_year)
            )
            
            if series_data and "data" in series_data:
                data_points = series_data["data"]
                if data_points:
                    latest = data_points[0]  # BLS returns most recent first
                    return {
                        "year": latest.get("year"),
                        "period": latest.get("period"),
                        "period_name": latest.get("periodName"),
                        "value": latest.get("value")
                    }
        except Exception as e:
            logger.error(f"Error getting latest value for {series_id}: {e}")
        
        return None