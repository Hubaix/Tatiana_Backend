
# Company Info Extractor

Extract all the company information powered by OpenAI assitants.
# Company Info Extractor

This project provides a set of APIs to extract and validate company information from various sources like LinkedIn and Wikipedia. The project uses FastAPI to create RESTful APIs and OpenAI for response validation.

## Requirements

- Python 3.8+
- The following Python packages:
  - `langchain-community`
  - `openai`
  - `pandas`
  - `python-docx`
  - `requests`
  - `wikipedia`
  - `python-dotenv`
  - `tavily-python`
  - `fastapi`
  - `uvicorn`
  - `numpy`
  - `docx`

## Installation

1. **Clone the repository**:

   ```sh
   git clone https://github.com/yourusername/company-info-extractor.git
   cd company-info-extractor

2. **Create a virtual enviroment and activate it**:

   ```sh
    python -m venv env
    env\Scripts\activate`

3. **Setup enviroment variables**:
   ```sh
    OPENAI_API_KEY=your_openai_api_key
    TAVILY_API_KEY=your_tavily_api_key
    PROXY_CURL_API_KEY=your_proxy_api


4. **Running the application**:
   ```sh
    uvicorn app:app --host 0.0.0.0 --port 5678

