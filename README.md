# BLS Data Intelligence Assistant

A Streamlit application powered by Semantic Kernel and Claude Sonnet (Anthropic) that provides intelligent analysis and reporting on Bureau of Labor Statistics (BLS) data.

## Features

- 🤖 Conversational AI interface powered by Claude Sonnet
- 📊 Real-time BLS data retrieval (unemployment, CPI, employment statistics)
- 🧠 Semantic Kernel integration for intelligent data analysis
- 📈 Automated report generation
- 💬 Natural language queries about economic data
- 🔐 Secure API key management
- ⚡ Async operations for better performance

## Prerequisites

- Python 3.9+
- Anthropic API key (get one at https://console.anthropic.com/)
- BLS API key (optional but recommended - register at https://www.bls.gov/developers/)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd bls-data-semantic-kernel
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## Configuration

Edit `.env` file with your credentials:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key
BLS_API_KEY=your_bls_api_key  # Optional but increases rate limits
```

## Running the Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

## Usage

### Example Queries

- "What's the current unemployment rate?"
- "Show me CPI data for the last 5 years"
- "Compare employment trends between 2020 and 2023"
- "Generate a report on inflation trends"
- "What are the latest job statistics?"

### Popular BLS Series IDs

The application supports various BLS series:

- **LNS14000000** - Unemployment Rate (National)
- **CUUR0000SA0** - Consumer Price Index (CPI-U)
- **CES0000000001** - Total Nonfarm Employment
- **LNS12300000** - Labor Force Participation Rate
- **CUSR0000SA0** - CPI for All Urban Consumers

## Project Structure

```
bls-data-semantic-kernel/
├── app.py                 # Main Streamlit application
├── config.py             # Configuration management
├── services/
│   ├── bls_service.py    # BLS API integration
│   └── sk_service.py     # Semantic Kernel service
├── utils/
│   └── helpers.py        # Helper functions
├── tests/
│   ├── test_bls_service.py
│   └── test_sk_service.py
├── requirements.txt
├── .env.example
└── README.md
```

## Testing

Run tests:
```bash
pytest tests/
```

With coverage:
```bash
pytest --cov=. --cov-report=html tests/
```

## API Rate Limits

- **Without BLS API Key**: 25 queries per day, 10 years per query
- **With BLS API Key**: 500 queries per day, 20 years per query

## Features in Detail

### Semantic Kernel Integration

The application uses Semantic Kernel to:
- Parse natural language queries
- Execute BLS API calls based on intent
- Format and analyze retrieved data
- Generate comprehensive reports

### Claude Sonnet (Anthropic)

Leverages Claude Sonnet 3.5 for:
- Natural language understanding
- Context-aware responses
- Data interpretation and insights
- Report generation

## Troubleshooting

### Common Issues

1. **API Key Errors**
   - Ensure `.env` file exists and contains valid API keys
   - Check that API keys are not expired

2. **BLS API Errors**
   - Verify series IDs are correct
   - Check date ranges (max 20 years with API key)
   - Ensure you haven't exceeded rate limits

3. **Streamlit Issues**
   - Clear cache: Click "C" in the running app or use `streamlit cache clear`
   - Restart the application

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License

## Acknowledgments

- Bureau of Labor Statistics for providing public API
- Anthropic for Claude AI model
- Microsoft for Semantic Kernel framework

## Support

For issues and questions:
- Open an issue on GitHub
- Check BLS API documentation: https://www.bls.gov/developers/
- Semantic Kernel docs: https://learn.microsoft.com/en-us/semantic-kernel/