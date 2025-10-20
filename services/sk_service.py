"""Semantic Kernel service for AI-powered BLS data analysis."""
import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd
import semantic_kernel as sk
from semantic_kernel.connectors.ai.anthropic import AnthropicChatCompletion
from semantic_kernel.contents import ChatHistory
from semantic_kernel.prompt_template import PromptTemplateConfig

from config import settings
from services.bls_service import BLSService
from utils.helpers import format_data_for_display

logger = logging.getLogger(__name__)


class SemanticKernelService:
    """Service for AI-powered query processing using Semantic Kernel and Claude."""
    
    def __init__(self, api_key: str, bls_service: BLSService):
        """Initialize Semantic Kernel service.
        
        Args:
            api_key: Anthropic API key
            bls_service: BLS service instance
        """
        self.bls_service = bls_service
        self.kernel = sk.Kernel()
        
        # Add Anthropic chat completion service
        self.chat_service = AnthropicChatCompletion(
            service_id="claude",
            api_key=api_key,
            ai_model_id=settings.ANTHROPIC_MODEL
        )
        self.kernel.add_service(self.chat_service)
        
        self.chat_history = ChatHistory()
        
        # Add system message
        self.chat_history.add_system_message(
            "You are a helpful assistant specialized in analyzing Bureau of Labor Statistics (BLS) data. "
            "You help users understand employment, unemployment, CPI, wages, and other economic indicators. "
            "When users ask questions, you extract the relevant series IDs, date ranges, and provide insights. "
            "You format responses clearly and explain economic concepts when needed."
        )
        
        logger.info("Semantic Kernel service initialized with Claude Sonnet")
    
    async def process_query(self, user_query: str) -> Dict[str, Any]:
        """Process user query using Semantic Kernel and Claude.
        
        Args:
            user_query: User's natural language query
            
        Returns:
            Dictionary with response message and optional data
        """
        logger.info(f"Processing query: {user_query}")
        
        try:
            # Step 1: Extract intent and parameters
            intent = await self._extract_intent(user_query)
            
            logger.info(f"Extracted intent: {intent}")
            
            # Step 2: Fetch data if series IDs identified
            data = None
            df = None
            
            if intent.get("series_ids") and intent.get("start_year") and intent.get("end_year"):
                data = self._fetch_bls_data(intent)
                if data:
                    df = format_data_for_display(data)
            
            # Step 3: Generate response using Claude
            response_message = await self._generate_response(
                user_query,
                intent,
                data,
                df
            )
            
            return {
                "message": response_message,
                "data": df,
                "intent": intent
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            return {
                "message": f"I encountered an error processing your request: {str(e)}. Could you please rephrase your question?",
                "data": None,
                "intent": None
            }
    
    async def _extract_intent(self, query: str) -> Dict[str, Any]:
        """Extract intent, series IDs, and date range from query.
        
        Args:
            query: User query
            
        Returns:
            Dictionary with extracted parameters
        """
        current_year = datetime.now().year
        
        # Create prompt for intent extraction
        prompt = f"""Analyze this query about BLS (Bureau of Labor Statistics) data and extract:
1. The type of data requested (unemployment, CPI, employment, wages, etc.)
2. Relevant BLS series IDs (if identifiable)
3. Date range (start_year and end_year)
4. Whether a report is requested

Common BLS Series IDs:
- LNS14000000: Unemployment Rate (National)
- CUUR0000SA0: Consumer Price Index (CPI-U)
- CES0000000001: Total Nonfarm Employment
- LNS12300000: Labor Force Participation Rate
- CES0500000003: Average Hourly Earnings

Query: "{query}"

Respond in JSON format with keys: data_type, series_ids (list), start_year, end_year, needs_report (boolean).
If date range not specified, use the last 5 years (start_year: {current_year - 5}, end_year: {current_year}).
If series IDs cannot be determined, return empty list.

JSON:"""
        
        self.chat_history.add_user_message(prompt)
        
        # Get response from Claude
        response = await self.chat_service.get_chat_message_content(
            chat_history=self.chat_history,
            settings=sk.connectors.ai.PromptExecutionSettings(
                service_id="claude",
                max_tokens=1000,
                temperature=0.3
            )
        )
        
        self.chat_history.add_assistant_message(str(response))
        
        # Parse JSON response
        try:
            # Extract JSON from response
            response_text = str(response)
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            
            if json_match:
                intent = json.loads(json_match.group())
            else:
                # Fallback: try to identify keywords
                intent = self._fallback_intent_extraction(query, current_year)
            
            return intent
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse intent JSON: {e}")
            return self._fallback_intent_extraction(query, current_year)
    
    def _fallback_intent_extraction(self, query: str, current_year: int) -> Dict[str, Any]:
        """Fallback intent extraction using keyword matching.
        
        Args:
            query: User query
            current_year: Current year
            
        Returns:
            Intent dictionary
        """
        query_lower = query.lower()
        
        # Determine data type and series IDs
        series_ids = []
        data_type = "general"
        
        if "unemployment" in query_lower:
            series_ids = ["LNS14000000"]
            data_type = "unemployment"
        elif "cpi" in query_lower or "inflation" in query_lower:
            series_ids = ["CUUR0000SA0"]
            data_type = "cpi"
        elif "employment" in query_lower or "jobs" in query_lower:
            series_ids = ["CES0000000001"]
            data_type = "employment"
        elif "wage" in query_lower or "earnings" in query_lower:
            series_ids = ["CES0500000003"]
            data_type = "wages"
        elif "participation" in query_lower:
            series_ids = ["LNS12300000"]
            data_type = "labor_force"
        
        # Extract years
        year_matches = re.findall(r'\b(19|20)\d{2}\b', query)
        
        if len(year_matches) >= 2:
            start_year = min(year_matches)
            end_year = max(year_matches)
        elif len(year_matches) == 1:
            start_year = year_matches[0]
            end_year = str(current_year)
        else:
            start_year = str(current_year - 5)
            end_year = str(current_year)
        
        needs_report = "report" in query_lower or "analysis" in query_lower or "trend" in query_lower
        
        return {
            "data_type": data_type,
            "series_ids": series_ids,
            "start_year": start_year,
            "end_year": end_year,
            "needs_report": needs_report
        }
    
    def _fetch_bls_data(self, intent: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Fetch BLS data based on intent.
        
        Args:
            intent: Extracted intent dictionary
            
        Returns:
            BLS API response data
        """
        try:
            series_ids = intent["series_ids"]
            start_year = intent["start_year"]
            end_year = intent["end_year"]
            
            if not series_ids:
                return None
            
            data = self.bls_service.get_series_data(
                series_ids=series_ids,
                start_year=start_year,
                end_year=end_year,
                catalog=False
            )
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching BLS data: {e}")
            return None
    
    async def _generate_response(
        self,
        user_query: str,
        intent: Dict[str, Any],
        data: Optional[Dict[str, Any]],
        df: Optional[pd.DataFrame]
    ) -> str:
        """Generate natural language response using Claude.
        
        Args:
            user_query: Original user query
            intent: Extracted intent
            data: Raw BLS data
            df: Formatted DataFrame
            
        Returns:
            Response message
        """
        # Prepare context
        context = f"""User Query: {user_query}

Extracted Intent:
- Data Type: {intent.get('data_type', 'N/A')}
- Series IDs: {', '.join(intent.get('series_ids', []))}
- Date Range: {intent.get('start_year', 'N/A')} to {intent.get('end_year', 'N/A')}
"""
        
        if df is not None and not df.empty:
            # Add data summary
            context += f"\n\nData Retrieved: {len(df)} data points"
            context += f"\n\nSample Data:\n{df.head(10).to_string()}"
            
            # Add statistical summary
            if 'Value' in df.columns:
                context += f"\n\nStatistical Summary:"
                context += f"\n- Latest Value: {df['Value'].iloc[0]}"
                context += f"\n- Average: {df['Value'].astype(float).mean():.2f}"
                context += f"\n- Min: {df['Value'].astype(float).min():.2f}"
                context += f"\n- Max: {df['Value'].astype(float).max():.2f}"
        else:
            context += "\n\nNo data was retrieved. The series IDs may not have been identified or there was an error."
        
        # Generate response prompt
        prompt = f"""{context}

Based on the above information, provide a helpful, conversational response to the user's query.
If data was retrieved:
1. Summarize the key findings
2. Highlight important trends or values
3. Provide context about what the numbers mean
4. If requested, offer analysis or insights

If no data was retrieved:
1. Explain what information you need
2. Suggest how the user can rephrase their question
3. Provide examples of what data is available

Keep the response concise but informative. Use markdown formatting for better readability."""
        
        self.chat_history.add_user_message(prompt)
        
        # Get Claude's response
        response = await self.chat_service.get_chat_message_content(
            chat_history=self.chat_history,
            settings=sk.connectors.ai.PromptExecutionSettings(
                service_id="claude",
                max_tokens=settings.SK_MAX_TOKENS,
                temperature=settings.SK_TEMPERATURE
            )
        )
        
        self.chat_history.add_assistant_message(str(response))
        
        return str(response)