"""Main Streamlit application for BLS Data Intelligence Assistant."""
import asyncio
import logging
from datetime import datetime

import streamlit as st

from config import settings
from services.bls_service import BLSService
from services.sk_service import SemanticKernelService
from utils.helpers import format_data_for_display, parse_year_range

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title=settings.APP_TITLE,
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize services
@st.cache_resource
def init_services():
    """Initialize BLS and Semantic Kernel services."""
    try:
        bls_service = BLSService(
            api_key=settings.BLS_API_KEY,
            base_url=settings.BLS_API_BASE_URL
        )
        sk_service = SemanticKernelService(
            api_key=settings.ANTHROPIC_API_KEY,
            bls_service=bls_service
        )
        return bls_service, sk_service
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        st.error(f"Initialization error: {e}")
        return None, None

bls_service, sk_service = init_services()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": "Hello! I'm your BLS Data Intelligence Assistant. I can help you with:\n\n"
                   "- Unemployment rates\n"
                   "- Employment statistics\n"
                   "- Consumer Price Index (CPI)\n"
                   "- Labor force data\n\n"
                   "Ask me anything about Bureau of Labor Statistics data!"
    })

if "current_data" not in st.session_state:
    st.session_state.current_data = None

# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")
    
    st.subheader("Quick Actions")
    
    # Popular queries
    st.markdown("### 💡 Example Queries")
    example_queries = [
        "Current unemployment rate",
        "CPI trends last 5 years",
        "Employment growth 2023",
        "Inflation analysis"
    ]
    
    for query in example_queries:
        if st.button(query, key=f"example_{query}"):
            st.session_state.messages.append({"role": "user", "content": query})
            st.rerun()
    
    st.markdown("---")
    
    # Popular series IDs
    st.subheader("📈 Popular Series")
    st.markdown("""
    - **LNS14000000**: Unemployment Rate
    - **CUUR0000SA0**: CPI-U
    - **CES0000000001**: Nonfarm Employment
    - **LNS12300000**: Labor Force Participation
    """)
    
    st.markdown("---")
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = [st.session_state.messages[0]]
        st.session_state.current_data = None
        st.rerun()
    
    # Status indicators
    st.markdown("---")
    st.subheader("🔌 Status")
    
    if bls_service and sk_service:
        st.success("✅ Services Connected")
    else:
        st.error("❌ Service Error")
    
    if settings.BLS_API_KEY:
        st.info("🔑 BLS API Key: Configured")
    else:
        st.warning("⚠️ BLS API Key: Not configured (limited access)")

# Main content
st.title(settings.APP_TITLE)
st.markdown("### Powered by Claude Sonnet & Semantic Kernel")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Display data if available
        if "data" in message and message["data"] is not None:
            with st.expander("📊 View Data", expanded=False):
                st.dataframe(message["data"], use_container_width=True)

# Chat input
if prompt := st.chat_input("Ask me about BLS data..."):
    if not bls_service or not sk_service:
        st.error("Services not initialized. Please check your configuration.")
    else:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Use Semantic Kernel to process query
                    response = asyncio.run(sk_service.process_query(prompt))
                    
                    st.markdown(response["message"])
                    
                    # Store message with data if available
                    message_data = {
                        "role": "assistant",
                        "content": response["message"]
                    }
                    
                    if response.get("data") is not None:
                        message_data["data"] = response["data"]
                        with st.expander("📊 View Data", expanded=False):
                            st.dataframe(response["data"], use_container_width=True)
                            
                            # Download button
                            csv = response["data"].to_csv(index=False)
                            st.download_button(
                                label="📥 Download CSV",
                                data=csv,
                                file_name=f"bls_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                    
                    st.session_state.messages.append(message_data)
                    
                except Exception as e:
                    error_msg = f"Error processing query: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"I encountered an error: {str(e)}. Please try rephrasing your question."
                    })

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Data provided by <a href='https://www.bls.gov/developers/' target='_blank'>Bureau of Labor Statistics</a> | "
    "Powered by <a href='https://www.anthropic.com/' target='_blank'>Anthropic Claude</a>"
    "</div>",
    unsafe_allow_html=True
)