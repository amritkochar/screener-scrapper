import re
import json
import requests
from bs4 import BeautifulSoup

def parse_company_name(soup) -> str:
    """
    Extracts the company name from:
      <div class="bg-base sticky company-nav">
        <div class="flex flex-space-between container hide-from-tablet-landscape">
          <h1 class="h2 shrink-text" style="margin: 0.5em 0">Kotak Mahindra Bank Ltd</h1>
    Returns e.g. "Kotak Mahindra Bank Ltd" or "UnknownCompany" if not found.
    """
    name_tag = soup.select_one("div.company-nav h1.h2.shrink-text")
    if name_tag:
        return name_tag.get_text(strip=True)
    return "UnknownCompany"

def parse_table(table_tag):
    """
    Parses an HTML <table> into a structured dict:
    {
      "headers": [...],
      "rows": [
         ["cell00", "cell01", ...],
         ["cell10", "cell11", ...],
         ...
      ]
    }
    """
    if not table_tag:
        return {}

    # Extract headers
    headers = []
    header_row = table_tag.select_one("thead tr")
    if header_row:
        headers = [th.get_text(strip=True) for th in header_row.select("th")]

    # Extract body rows
    data_rows = []
    body = table_tag.select_one("tbody")
    if body:
        for row in body.select("tr"):
            row_cells = row.find_all(["th", "td"])
            row_data = [cell.get_text(strip=True) for cell in row_cells]
            # Skip if row is entirely blank
            if any(item for item in row_data):
                data_rows.append(row_data)

    return {
        "headers": headers,
        "rows": data_rows
    }

def parse_summary_section(summary_soup):
    """
    Example parser for the 'Summary' section:
    - About text
    - Key Points
    - Top Ratios
    """
    data = {}

    # "About" text
    about_tag = summary_soup.select_one("div.about")
    data["about"] = about_tag.get_text(strip=True) if about_tag else ""

    # "Key Points"
    key_points_tag = summary_soup.select_one("div.sub.commentary")
    data["key_points"] = key_points_tag.get_text(" ", strip=True) if key_points_tag else ""

    # "Top Ratios"
    ratio_data = []
    top_ratios = summary_soup.select("#top-ratios > li")
    for r in top_ratios:
        name = r.select_one(".name")
        val = r.select_one(".value")
        if name and val:
            ratio_data.append({
                "ratio_name": name.get_text(strip=True),
                "ratio_value": val.get_text(strip=True)
            })
    data["top_ratios"] = ratio_data

    return data

def parse_analysis_section(analysis_soup):
    """For the 'Analysis' section: Pros and Cons."""
    data = {}

    # Pros
    pros_list = []
    pros_ul = analysis_soup.select_one("div.pros ul")
    if pros_ul:
        for li in pros_ul.select("li"):
            pros_list.append(li.get_text(strip=True))
    data["pros"] = pros_list

    # Cons
    cons_list = []
    cons_ul = analysis_soup.select_one("div.cons ul")
    if cons_ul:
        for li in cons_ul.select("li"):
            cons_list.append(li.get_text(strip=True))
    data["cons"] = cons_list

    return data


def parse_peers_section(peers_soup):
    """
    Parses the 'Peers' section to capture only the peer comparison table.
    Ignores all links for benchmarks (BSE Sensex, Nifty, etc.).
    
    Returns a dict like:
    {
      "peer_comparison": {
         "headers": [...],  # e.g. ["S.No.", "Name", "CMP", "P/E", ...]
         "rows": [
           ["1.", "HDFC Bank", "1805.95", "19.86", ...],
           ["2.", "ICICI Bank", "1335.40", "19.17", ...],
           ...
         ],
         "footer": [
           ["", "Median: 29 Co.", "177.5", "10.84", ...]
         ]
      }
    }
    """

    data = {}

    # Look for the table with classes "data-table text-nowrap striped mark-visited no-scroll-right"
    # to ensure we grab the correct table even if there are other data-table elements
    table = peers_soup.select_one("table.data-table.text-nowrap.striped.mark-visited.no-scroll-right")
    if not table:
        data["peer_comparison"] = {"info": "No peer table found"}
        return data

    headers = []
    rows = []
    footer = []

    # 1. Parse <thead>
    thead = table.select_one("thead")
    if thead:
        header_cells = thead.select("tr th")
        headers = [hc.get_text(strip=True) for hc in header_cells]

    # 2. Parse <tbody>
    tbody = table.select_one("tbody")
    if tbody:
        for tr in tbody.select("tr"):
            cells = tr.find_all(["td", "th"])
            row_text = [c.get_text(strip=True) for c in cells]
            if any(row_text):
                rows.append(row_text)

    # 3. Parse <tfoot>
    tfoot = table.select_one("tfoot")
    if tfoot:
        for tr in tfoot.select("tr"):
            cells = tr.find_all(["td", "th"])
            row_text = [c.get_text(strip=True) for c in cells]
            if any(row_text):
                footer.append(row_text)

    data["peer_comparison"] = {
        "headers": headers,
        "rows": rows,
        "footer": footer
    }

    return data


def parse_quarters_section(quarters_soup):
    """Parse the 'Quarters' section table."""
    data = {}
    quarters_table = quarters_soup.select_one("table.data-table")
    data["quarterly_results"] = parse_table(quarters_table)
    return data

def parse_profit_loss_section(pnl_soup):
    """Parse the Profit & Loss table."""
    data = {}
    pnl_table = pnl_soup.select_one("table.data-table")
    data["profit_loss"] = parse_table(pnl_table)
    return data

def parse_balance_sheet_section(bs_soup):
    """Parse the Balance Sheet table."""
    data = {}
    bs_table = bs_soup.select_one("table.data-table")
    data["balance_sheet"] = parse_table(bs_table)
    return data

def parse_cash_flow_section(cf_soup):
    """Parse the Cash Flow table."""
    data = {}
    cf_table = cf_soup.select_one("table.data-table")
    data["cash_flow"] = parse_table(cf_table)
    return data

def parse_ratios_section(ratios_soup):
    """Parse the Ratios table."""
    data = {}
    ratios_table = ratios_soup.select_one("table.data-table")
    data["ratios"] = parse_table(ratios_table)
    return data

def parse_shareholding_section(sh_soup):
    """Parse the shareholding (Investors) table if present."""
    data = {}
    sh_table = sh_soup.select_one("table.data-table")
    data["shareholding"] = parse_table(sh_table)
    return data

def parse_documents_section(docs_soup):
    """Parse the Documents section."""
    data = {}
    data["documents_info"] = docs_soup.get_text(" ", strip=True)
    return data

def parse_growth_tables(section_soup) -> dict:
    """
    Parses the four 'ranges-table' elements, each containing data like:
      Compounded Sales Growth, Compounded Profit Growth, Stock Price CAGR, Return on Equity

    Example HTML snippet:
      <table class="ranges-table">
        <tbody>
          <tr><th>Compounded Sales Growth</th></tr>
          <tr><td>10 Years:</td><td>17%</td></tr>
          ...
        </tbody>
      </table>

    Returns a dict, for example:
    {
      "Compounded Sales Growth": {
        "10 Years": "17%",
        "5 Years": "14%",
        "3 Years": "20%",
        "TTM": "21%"
      },
      "Compounded Profit Growth": { ... },
      "Stock Price CAGR": { ... },
      "Return on Equity": { ... }
    }
    """
    data = {}

    tables = section_soup.select("table.ranges-table")
    if not tables:
        print("No 'ranges-table' elements found.")
        return data

    for idx, tbl in enumerate(tables, start=1):
        rows = tbl.select("tr")
        heading_text = None
        row_data = {}

        for row in rows:
            th_el = row.find("th")
            if th_el:
                heading_text = th_el.get_text(strip=True)
                # Initialize sub-dict for this heading
                data[heading_text] = {}
                row_data = data[heading_text]
            else:
                tds = row.find_all("td")
                if len(tds) == 2 and heading_text is not None:
                    label = tds[0].get_text(strip=True).rstrip(":")
                    value = tds[1].get_text(strip=True)
                    row_data[label] = value

        if heading_text is None:
            print(f"No heading row found in ranges-table #{idx}")

    # print("parse_growth_tables extracted:", data)
    return data

# --------------------------------------------------------------------------
# PARSE COMMENTARY (the second request)
# --------------------------------------------------------------------------
def parse_commentary_html(commentary_html: str) -> dict:
    """
    Given the raw HTML from the commentary endpoint (company/ID/commentary/v2/),
    parse out the headings (like "About", "Key Points", etc.) and gather the text
    in the following <div class="sub"> block.
    """
    soup = BeautifulSoup(commentary_html, "html.parser")
    commentary_data = {}

    heading_divs = soup.select("div.strong.upper.letter-spacing")

    for heading in heading_divs:
        heading_text = heading.get_text(strip=True)
        next_sub = heading.find_next_sibling("div", class_="sub")
        if next_sub:
            body_text = next_sub.get_text(" ", strip=True)
            commentary_data[heading_text] = body_text

    return commentary_data

def fetch_commentary_data(company_id: str) -> dict:
    """
    Makes a request to Screener's commentary endpoint:
      https://www.screener.in/wiki/company/{company_id}/commentary/v2/
    using provided cookies/headers (if needed).
    Returns a dict of parsed commentary data.
    """
    commentary_url = f"https://www.screener.in/wiki/company/{company_id}/commentary/v2/"

    headers = {
        "User-Agent": ("Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/134.0.0.0 Mobile Safari/537.36"),
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "*/*",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Referer": "https://www.screener.in/company/KOTAKBANK/consolidated/"
    }

    # If login is required, set valid cookies here
    cookies = {
        "csrftoken": "qqgI5LPMGQOwRyHbocfjYB0DiQDUypNX",
        "sessionid": "2dvmmu21airzcahg76vubryti9hs4wiz"
    }

    resp = requests.get(commentary_url, headers=headers, cookies=cookies)
    resp.raise_for_status()
    return parse_commentary_html(resp.text)

# --------------------------------------------------------------------------
# MAIN SCRAPER (primary page)
# --------------------------------------------------------------------------
def scrape_screener_data(url: str) -> dict:
    """
    1) Fetch main Screener page
    2) Extract company_name and company_id
    3) Parse known sections (#analysis, #peers, #quarters, etc.)
    4) Parse the '4 data points' growth tables
    5) If we found a company_id, fetch commentary data
    6) Return final dictionary
    """
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    results = {}

    # 1. Extract the company name from the nav
    company_name = parse_company_name(soup)
    results["company_name"] = company_name

    # 2. Extract the Company ID from the <style> snippet
    style_tags = soup.find_all("style")
    company_id = None
    for st in style_tags:
        match = re.search(r'data-row-company-id="(\d+)"', st.text)
        if match:
            company_id = match.group(1)
            break
    results["company_id"] = company_id or "N/A"

    # 3. Parse sub-nav sections from the main page
    sub_nav = soup.select_one("div.sub-nav-holder .sub-nav")
    if not sub_nav:
        print("Warning: sub-navigation not found.")
        return results

    nav_links = sub_nav.find_all("a", href=True)
    parser_map = {
        "Summary": parse_summary_section,
        "top": parse_summary_section,
        "Chart": None,
        "analysis": parse_analysis_section,
        "Analysis": parse_analysis_section,
        "peers": parse_peers_section,
        "Peers": parse_peers_section,
        "quarters": parse_quarters_section,
        "Quarters": parse_quarters_section,
        "profit-loss": parse_profit_loss_section,
        "Profit & Loss": parse_profit_loss_section,
        "balance-sheet": parse_balance_sheet_section,
        "Balance Sheet": parse_balance_sheet_section,
        "cash-flow": parse_cash_flow_section,
        "Cash Flow": parse_cash_flow_section,
        "ratios": parse_ratios_section,
        "Ratios": parse_ratios_section,
        "shareholding": parse_shareholding_section,
        "investors": parse_shareholding_section,
        "Investors": parse_shareholding_section,
        "documents": parse_documents_section,
        "Documents": parse_documents_section
    }

    for link in nav_links:
        href = link["href"]
        if not href.startswith("#"):
            continue

        section_id = href.lstrip("#")
        if not section_id:
            continue

        link_label = link.get_text(strip=True) or section_id
        section_tag = soup.select_one(f"section#{section_id}") or soup.select_one(f"div#{section_id}")
        if not section_tag:
            continue

        parser_func = parser_map.get(link_label) or parser_map.get(section_id)
        if parser_func is not None:
            cleaned_data = parser_func(section_tag)
            results[link_label] = cleaned_data
        else:
            results[link_label] = {"info": "No specialized parser for this section."}

    # 4. Parse the '4 data points' growth tables if present
    growth_div = soup.select_one("div[style*='grid-template-columns']")
    if growth_div:
        results["growth_metrics"] = parse_growth_tables(growth_div)

    # 5. If we found a company_id, fetch commentary
    if company_id:
        commentary_data = fetch_commentary_data(company_id)
        results["commentary"] = commentary_data
    else:
        results["commentary"] = {"info": "Company ID not found, so commentary not fetched."}

    return results

# --------------------------------------------------------------------------
# DRIVER
# --------------------------------------------------------------------------
if __name__ == "__main__":
    url = "https://www.screener.in/company/KOTAKBANK/consolidated/"
    scraped_data = scrape_screener_data(url)

    # Attempt to retrieve and sanitize the company_name
    company_name = scraped_data.get("company_name", "UnknownCompany")
    import re
    safe_company_name = re.sub(r"[^a-zA-Z0-9]+", "_", company_name)

    # Construct a dynamic filename with the company name
    filename = f"screener_cleaned_data_{safe_company_name}_with_growth_tables.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(scraped_data, f, indent=2, ensure_ascii=False)

    print(f"Scraped data (including 4 data points for growth) saved to {filename}")
