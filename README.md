# Screener Stocks Data Scrapper

This project is a Python-based tool designed to scrape and analyze financial data from the Screener website. It extracts key financial metrics, growth tables, shareholding patterns, and other relevant data for companies listed on the platform. The tool is particularly useful for investors and analysts looking to automate the process of gathering financial insights.

## Features

- **Data Extraction**:
  - Scrapes financial data such as profit & loss, balance sheet, cash flow, and key ratios.
  - Extracts shareholding patterns, peer comparisons, and quarterly results.
  - Fetches additional commentary and documents related to the company.

- **Growth Metrics**:
  - Parses growth tables to compute metrics like compounded sales growth, profit growth, and return on equity (ROE).

- **Visualization**:
  - Includes functionality to plot financial data (e.g., cash flow trends) for better analysis.

- **Dynamic File Generation**:
  - Saves scraped data into JSON files with dynamically generated filenames based on the company name.

## File Structure

- `scrapper.py`: The main script that handles scraping and parsing of data from the Screener website.

## How It Works

1. **Scraping**:
   - The tool fetches the HTML content of a company's Screener page using `requests` and parses it with `BeautifulSoup`.
   - It identifies and extracts data from various sections like `#analysis`, `#peers`, `#quarters`, etc.

2. **Data Parsing**:
   - Specialized parsers are implemented for sections like growth tables, shareholding patterns, and financial statements.
   - If no specialized parser exists for a section, a default message is returned.

3. **Commentary Fetching**:
   - If a company ID is available, additional commentary and document data are fetched via API calls.

4. **Data Storage**:
   - The extracted data is saved in JSON format for easy access and further analysis.

5. **Visualization**:
   - Financial trends like cash flow and balance sheet data can be visualized using `matplotlib`.

## Usage

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd screener-scrapper