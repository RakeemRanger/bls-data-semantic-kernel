"""Helper functions for data formatting and processing."""
import logging
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


def format_data_for_display(bls_data: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """Format BLS API response data into a pandas DataFrame.
    
    Args:
        bls_data: BLS API response dictionary
        
    Returns:
        Formatted DataFrame or None
    """
    try:
        results = bls_data.get("Results", {})
        series_list = results.get("series", [])
        
        if not series_list:
            return None
        
        all_data = []
        
        for series in series_list:
            series_id = series.get("seriesID")
            data_points = series.get("data", [])
            
            for point in data_points:
                all_data.append({
                    "Series ID": series_id,
                    "Year": point.get("year"),
                    "Period": point.get("period"),
                    "Period Name": point.get("periodName"),
                    "Value": point.get("value"),
                    "Footnotes": ", ".join([f.get("text", "") for f in point.get("footnotes", [])]) if point.get("footnotes") else ""
                })
        
        df = pd.DataFrame(all_data)
        
        # Sort by year and period (most recent first)
        if not df.empty:
            df = df.sort_values(by=["Year", "Period"], ascending=[False, False])
            df = df.reset_index(drop=True)
        
        return df
        
    except Exception as e:
        logger.error(f"Error formatting data: {e}", exc_info=True)
        return None


def parse_year_range(text: str, default_years: int = 5) -> Tuple[str, str]:
    """Parse year range from text.
    
    Args:
        text: Input text
        default_years: Default number of years if not specified
        
    Returns:
        Tuple of (start_year, end_year)
    """
    import re
    from datetime import datetime
    
    current_year = datetime.now().year
    
    # Look for year patterns
    years = re.findall(r'\b(19|20)\d{2}\b', text)
    
    if len(years) >= 2:
        return min(years), max(years)
    elif len(years) == 1:
        return years[0], str(current_year)
    else:
        return str(current_year - default_years), str(current_year)


def identify_series_from_keywords(text: str) -> List[str]:
    """Identify BLS series IDs from keywords in text.
    
    Args:
        text: Input text
        
    Returns:
        List of series IDs
    """
    text_lower = text.lower()
    series_ids = []
    
    # Keyword to series ID mapping
    mappings = {
        "unemployment rate": "LNS14000000",
        "unemployment": "LNS14000000",
        "jobless": "LNS14000000",
        "cpi": "CUUR0000SA0",
        "consumer price": "CUUR0000SA0",
        "inflation": "CUUR0000SA0",
        "employment": "CES0000000001",
        "jobs": "CES0000000001",
        "nonfarm": "CES0000000001",
        "labor force participation": "LNS12300000",
        "participation rate": "LNS12300000",
        "wages": "CES0500000003",
        "earnings": "CES0500000003",
        "hourly earnings": "CES0500000003"
    }
    
    for keyword, series_id in mappings.items():
        if keyword in text_lower and series_id not in series_ids:
            series_ids.append(series_id)
    
    return series_ids


def format_number(value: str, decimal_places: int = 1) -> str:
    """Format numeric value with specified decimal places.
    
    Args:
        value: Numeric value as string
        decimal_places: Number of decimal places
        
    Returns:
        Formatted string
    """
    try:
        num = float(value)
        return f"{num:.{decimal_places}f}"
    except (ValueError, TypeError):
        return value


def create_summary_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """Create summary statistics from DataFrame.
    
    Args:
        df: Input DataFrame with BLS data
        
    Returns:
        Dictionary with summary statistics
    """
    if df is None or df.empty or "Value" not in df.columns:
        return {}
    
    try:
        values = df["Value"].astype(float)
        
        return {
            "count": len(values),
            "mean": float(values.mean()),
            "std": float(values.std()),
            "min": float(values.min()),
            "max": float(values.max()),
            "latest": float(values.iloc[0]) if not values.empty else None,
            "earliest": float(values.iloc[-1]) if not values.empty else None
        }
    except Exception as e:
        logger.error(f"Error creating summary statistics: {e}")
        return {}