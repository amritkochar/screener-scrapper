from bs4 import BeautifulSoup
import requests
import json
import matplotlib.pyplot as plt

def fetch_html(url):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch the URL. Status Code: {response.status_code}")
        return None
    return BeautifulSoup(response.content, 'html.parser')

def fetch_api_data(company_id, parent_label, section):
    api_url = f'https://www.screener.in/api/company/{company_id}/schedules/?parent={parent_label}&section={section}&consolidated='
    headers = {
        'Referer': 'https://www.screener.in/',
        'X-Requested-With': 'XMLHttpRequest'
    }
    response = requests.get(api_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch API data for {parent_label}. Status Code: {response.status_code}")
        return []
    data = response.json().get('data', [])
    print(f"Data received for {parent_label}: {data}")  # Print the data if status code is 200
    return data

def extract_company_name(soup):
    return soup.find('h1', class_='h2').text.strip()

def extract_years(soup, section_id):
    headers = soup.select(f'#{section_id} table thead tr th')[1:]
    return [header.text.strip() for header in headers]

def extract_data(soup, section_id, company_id):
    data_section = soup.select(f'#{section_id} table tbody tr')
    data = {}
    if not data_section:
        print(f"{section_id.replace('-', ' ').title()} data not found.")
        return data

    for row in data_section:
        columns = row.find_all('td')
        if columns and len(columns) > 1:
            label = columns[0].text.strip()
            values = [float(col.text.replace(',', '').strip() or '0') for col in columns[1:]]
            data[label] = values

            # Check for expandable data using API call
            if row.select_one('button[onclick*="Company.showSchedule"]'):
                print(f"Fetching expanded data for {label}")
                expanded_data = fetch_api_data(company_id, label, section_id)
                data[label + ' (Expanded)'] = expanded_data
    
    return data

def plot_data(years, data, title):
    plt.figure(figsize=(10, 6))
    for label, values in data.items():
        if isinstance(values, list):
            plt.plot(years, values, label=label)

    plt.xlabel('Year')
    plt.ylabel('Amount (in Crores)')
    plt.title(title)
    plt.legend(loc='best')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def scrape_data(url, company_id):
    soup = fetch_html(url)
    if not soup:
        return

    company_name = extract_company_name(soup)
    years = extract_years(soup, 'cash-flow')
    cash_flow_data = extract_data(soup, 'cash-flow', company_id)
    balance_sheet_data = extract_data(soup, 'balance-sheet', company_id)

    result = {
        "Company Name": company_name,
        "Years": years,
        "Cash Flow Data": cash_flow_data,
        "Balance Sheet Data": balance_sheet_data
    }

    filename = f"{company_name.replace(' ', '_')}_data.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    print(f"Data extraction complete. Saved to {filename}")

    plot_data(years, cash_flow_data, f'{company_name} - Cash Flow Data')

# Example URL (replace with actual URL and Company ID)
scrape_data('https://www.screener.in/company/KOTAKBANK/consolidated/', 1818)