# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse, urlunparse
import time
import csv
import traceback # Keep for reporting unexpected errors
import os

# --- Selenium Imports ---
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException # Import specifically
from webdriver_manager.chrome import ChromeDriverManager

# --- Configuration ---
# --- !! YEAR SELECTION !! ---
START_YEAR = 2015
END_YEAR = 2024
# To scrape 2015-2024, set: START_YEAR = 2015, END_YEAR = 2024
# --- End Year Selection ---

BASE_URL = "https://www.formula1.com"
RESULTS_BASE_URL = f"{BASE_URL}/en/results.html"
ALLOWED_DOMAIN = urlparse(BASE_URL).netloc

# Base output directory for CSV files
OUTPUT_DIR = "f1_results_by_type_simple"

# --- Selenium Settings (Mimicking the simpler working code where sensible) ---
# Using a moderate timeout - 20s was in the simple code, 90s failed, let's try 30s
SELENIUM_WAIT_TIMEOUT = 30
REQUEST_DELAY_SECONDS = 2 # Slightly increased delay from simple code

# --- !!! HEADLESS DEBUGGING CONTROL !!! ---
RUN_HEADLESS = True # Set to False to run VISIBLE if timeouts persist
# --- End Headless Control ---

# --- URL Patterns ---
# Pattern for yearly overview pages
YEARLY_OVERVIEW_PATTERN = re.compile(r'/en/results\.html/(\d{4})/races\.html$', re.IGNORECASE)
# Pattern to find links to specific races on the yearly overview page
RACE_LINK_IDENTIFIER_PATTERN = re.compile(r'/en/results\.html/(\d{4})/races/(\d+)/([^/]+)')

# --- CSS Selectors (Using selectors from simpler code where applicable) ---
# Default wait element from simple code
DEFAULT_WAIT_ELEMENT = "footer"
# Overview table selector from simple code
OVERVIEW_TABLE_SELECTOR = "table.f1-table.f1-table-with-data"
# General data table selector (use robust one from later versions)
DATA_TABLE_SELECTOR = "table.resultsarchive-table, table.f1-table.f1-table-with-data"

# --- Selenium Options Setup (Using User-Agent from simple code) ---
SELENIUM_OPTIONS = Options()
if RUN_HEADLESS:
    SELENIUM_OPTIONS.add_argument('--headless')
SELENIUM_OPTIONS.add_argument('--disable-gpu')
SELENIUM_OPTIONS.add_argument('--no-sandbox')
SELENIUM_OPTIONS.add_argument('--window-size=1920,1080')
SELENIUM_OPTIONS.add_argument('--disable-dev-shm-usage')
# User agent from the simple code that worked
SELENIUM_OPTIONS.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36')


# --- Helper Function: Fetch HTML (Simplified Error Handling) ---
def get_rendered_html_selenium(url, wait_for_selector, timeout=SELENIUM_WAIT_TIMEOUT):
    """ Fetches HTML using Selenium. Simplified error handling, no explicit retry. """
    print(f"Fetching: {url} (Wait: '{wait_for_selector}', Timeout: {timeout}s)")
    driver = None
    service = None
    html_content = None
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=SELENIUM_OPTIONS)
        # driver.set_page_load_timeout(timeout + 10) # Keep page load timeout reasonable
        driver.get(url)
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_selector))
        )
        # Small pause might help let things settle after wait condition met
        # time.sleep(0.2)
        html_content = driver.page_source
        print("-> Fetch successful.")
    except TimeoutException:
        print(f"!!! TIMEOUT waiting for element '{wait_for_selector}' on {url}")
    except Exception as e:
        print(f"!!! ERROR fetching {url}: {type(e).__name__} - {e}")
    finally:
        if driver:
            driver.quit()
    return html_content


# --- Parsing Functions (Keep the necessary ones from previous versions) ---
# Metadata extraction
def extract_metadata(soup, url):
    year, race_name, race_id_str, location = "Unknown", "Unknown", "Unknown", "Unknown"
    url_match_result = re.search(r'/en/results\.html/(\d{4})/races/(\d+)/([^/]+)/', url)
    if url_match_result:
        year, race_id_str, location = url_match_result.groups()
        race_name = location.replace('-', ' ').title() + " Grand Prix"
    else:
        year_match = re.search(r'/(\d{4})/', url)
        if year_match: year = year_match.group(1)
    try:
        title_tag = soup.select_one("h1.ResultsArchiveTitle, h1.f1-heading")
        if title_tag:
            full_title = title_tag.get_text(strip=True)
            title_match = re.match(r'.*?([\w\s-]+?)\s*(?:GRAND PRIX)?\s*(\d{4})', full_title, re.IGNORECASE)
            if title_match:
                extracted_race, extracted_year = title_match.group(1).strip(), title_match.group(2)
                if extracted_race and len(extracted_race) > 3: race_name = extracted_race
                if extracted_year: year = extracted_year
            elif year != "Unknown":
                 cleaned_name = full_title.replace(year, '').replace('FORMULA 1', '').replace('GRAND PRIX', '').strip(' -').strip()
                 cleaned_name = re.sub(r'\b(Race Result|Fastest Laps|Qualifying|Practice\s*\d|Starting Grid|Pit Stop Summary)\b', '', cleaned_name, flags=re.IGNORECASE).strip()
                 if cleaned_name: race_name = cleaned_name
    except Exception: pass
    if race_name == "Unknown" or race_name.lower() == 'results':
        if location != "Unknown": race_name = location.replace('-', ' ').title() + " Grand Prix"
        else: race_name = "Unknown Race"
    return year, race_name, race_id_str

# Driver cell parsing
def parse_driver_cell(driver_cell):
    driver_name, driver_code = '', ''
    if not driver_cell: return driver_name, driver_code
    first = driver_cell.select_one("span.hide-for-mobile")
    last = driver_cell.select_one("span.hide-for-tablet")
    code = driver_cell.select_one("span.hide-for-desktop")
    if first and last: driver_name = f"{first.text.strip()} {last.text.strip()}"
    if code: driver_code = code.text.strip()
    if not driver_name and not driver_code:
        full_text = driver_cell.get_text(" ", strip=True); parts = full_text.split()
        if parts:
            if len(parts[-1]) == 3 and parts[-1].isupper(): driver_code = parts[-1]; driver_name = " ".join(parts[:-1])
            else: driver_name = full_text
    elif not driver_name and driver_code: driver_name = driver_cell.get_text(" ", strip=True).replace(driver_code, '').strip()
    elif driver_name and not driver_code:
        potential_code = driver_cell.get_text(" ", strip=True).replace(driver_name, '').strip()
        if len(potential_code) == 3 and potential_code.isupper(): driver_code = potential_code
    return driver_name.strip(), driver_code.strip()

# General table parser (for Race, Quali, Practice, FL, Start Grid)
def parse_results_table(html_content, url, result_type_name, column_mapping):
    results = []
    if not html_content: return results
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        year, race_name, race_id = extract_metadata(soup, url)
        data_table = soup.select_one(DATA_TABLE_SELECTOR)
        if not data_table: return results # Silently return if no table
        tbody = data_table.select_one("tbody")
        rows = tbody.select("tr") if tbody else data_table.select("tr:not(:first-child)")
        for row in rows:
            cols = row.select("td")
            min_cols = max(column_mapping.values()) if column_mapping else 3
            if len(cols) <= min_cols - 1: continue
            row_data = {'year': year, 'race_name': race_name, 'race_id': race_id, 'result_type': result_type_name, 'url': url}
            has_essential_data = False
            for col_name, col_index in column_mapping.items():
                if col_index < len(cols):
                    cell = cols[col_index]
                    if col_name == 'driver': name, code = parse_driver_cell(cell); row_data['driver_name'], row_data['driver_code'] = name, code; has_essential_data |= bool(name or code)
                    elif col_name == 'team': row_data[col_name] = cell.get_text(strip=True); has_essential_data |= bool(row_data[col_name])
                    else:
                        row_data[col_name] = cell.get_text(strip=True)
                        if col_name == 'position' and row_data[col_name] and (row_data[col_name].isdigit() or len(row_data[col_name]) <= 3): has_essential_data = True
                else: row_data[col_name] = ''
            if has_essential_data: results.append(row_data)
    except Exception as e: print(f"!!! Error parsing {result_type_name} table for {url}: {type(e).__name__}") # Simplified error log
    return results

# Pit stop parser
def parse_pit_stop_summary(html_content, url):
    results = []; result_type_name = 'pit_stop'
    if not html_content: return results
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        year, race_name, race_id = extract_metadata(soup, url)
        data_table = soup.select_one(DATA_TABLE_SELECTOR)
        if not data_table: return results
        tbody = data_table.select_one("tbody")
        rows = tbody.select("tr") if tbody else data_table.select("tr:not(:first-child)")
        pit_stop_mapping = {'stops': 0, 'driver_number': 1, 'driver': 2, 'team': 3, 'lap': 4, 'time_of_day': 5, 'pit_time': 6, 'total_pit_time': 7}
        for row in rows:
            cols = row.select("td")
            if len(cols) < 7: continue
            row_data = {'year': year, 'race_name': race_name, 'race_id': race_id, 'result_type': result_type_name, 'url': url}
            has_essential_data = False
            for col_name, col_index in pit_stop_mapping.items():
                if col_index < len(cols):
                    cell = cols[col_index]
                    if col_name == 'driver': name, code = parse_driver_cell(cell); row_data['driver_name'], row_data['driver_code'] = name, code; has_essential_data |= bool(name or code)
                    elif col_name == 'team': row_data[col_name] = cell.get_text(strip=True); has_essential_data |= bool(row_data[col_name])
                    else:
                        row_data[col_name] = cell.get_text(strip=True)
                        if col_name == 'pit_time' and row_data[col_name]: has_essential_data = True
                else: row_data[col_name] = ''
            if has_essential_data: results.append(row_data)
    except Exception as e: print(f"!!! Error parsing pit stop table for {url}: {type(e).__name__}")
    return results

# --- CSV Saving Function (Unchanged) ---
def save_to_csv(data, filename):
    if not data:
        print(f"No data collected for {filename}, skipping CSV save.")
        return
    print(f"\nAttempting to save {len(data)} data rows to {filename}...")
    headers = set()
    for row in data: headers.update(row.keys())
    final_headers = sorted(list(headers))
    for key in ['url', 'result_type', 'race_id', 'race_name', 'year']: # Move keys to front
        if key in final_headers: final_headers.insert(0, final_headers.pop(final_headers.index(key)))
    try:
        os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=final_headers, restval='')
            writer.writeheader(); writer.writerows(data)
        print(f"Successfully saved data to {filename}")
    except Exception as e: print(f"!!! ERROR saving data to CSV {filename}: {e}")


# --- Function to Crawl Data for a SPECIFIC Result Type (Adapted) ---
def crawl_single_result_type(years_to_scrape, target_suffix, result_type_name, column_mapping, parse_function):
    """ Crawls data for only one type of result (e.g., 'race-result.html'). """
    urls_to_visit = set()
    visited_urls = set()
    collected_data = []
    request_count = 0
    max_requests_per_type = 5000

    print(f"\n----- Starting crawl for: {result_type_name} -----")
    for year in years_to_scrape: urls_to_visit.add(f"{RESULTS_BASE_URL}/{year}/races.html")

    while urls_to_visit and request_count < max_requests_per_type:
        if request_count > 0: time.sleep(REQUEST_DELAY_SECONDS)

        current_url = urls_to_visit.pop()
        request_count += 1
        # print(f"Req {request_count}/{max_requests_per_type} ({result_type_name}): {current_url}") # Verbose

        parsed_url = urlparse(current_url)
        if not parsed_url.scheme: current_url = urljoin(BASE_URL, current_url)
        if parsed_url.netloc != ALLOWED_DOMAIN: continue
        # Use target_url_to_fetch for visited check, potentially adding .html if needed (though generation adds it now)
        target_url_to_fetch = current_url
        if not target_url_to_fetch.endswith('.html') and not YEARLY_OVERVIEW_PATTERN.search(target_url_to_fetch):
             # If it's not overview and doesn't end with .html, assume it needs it
             # This logic might be less needed now we generate URLs with .html
             target_url_to_fetch += ".html"

        if target_url_to_fetch in visited_urls: continue
        visited_urls.add(target_url_to_fetch) # Visit the URL we intend to fetch

        is_overview = YEARLY_OVERVIEW_PATTERN.search(target_url_to_fetch)
        # Check if the fetch URL matches the target suffix for this pass
        is_target_result_page = target_url_to_fetch.lower().endswith(target_suffix.lower())

        # Determine wait selector based on page type - use simple code's logic
        wait_selector = OVERVIEW_TABLE_SELECTOR if is_overview else DEFAULT_WAIT_ELEMENT
        html = get_rendered_html_selenium(target_url_to_fetch, wait_selector) # Use potentially different wait selector

        if not html:
            # print(f"-> Fetch failed for {target_url_to_fetch}, skipping.") # Less verbose
            continue

        soup = BeautifulSoup(html, 'html.parser')

        # If Yearly Overview Page: Find races and queue ONLY the target result type URL
        if is_overview:
            # print(f"-> Overview Page. Finding links in '{OVERVIEW_TABLE_SELECTOR}'...") # Verbose
            links_added = 0
            # Use the overview selector from simple code
            content_area = soup.select_one(OVERVIEW_TABLE_SELECTOR)
            if content_area:
                links = content_area.find_all('a', href=True)
                for link in links:
                    abs_link = urljoin(target_url_to_fetch, link['href'])
                    match = RACE_LINK_IDENTIFIER_PATTERN.search(abs_link)
                    if match and urlparse(abs_link).netloc == ALLOWED_DOMAIN:
                        year, race_id, loc = match.groups()
                        base_race_url = f"{RESULTS_BASE_URL}/{year}/races/{race_id}/{loc}"
                        # Generate ONLY the target URL with .html suffix
                        generated_url = base_race_url + target_suffix
                        if generated_url not in visited_urls and generated_url not in urls_to_visit:
                            urls_to_visit.add(generated_url)
                            links_added += 1
                # print(f"-> Added {links_added} '{target_suffix}' URLs.") # Verbose
            # else:
                # print(f"-> Overview table ('{OVERVIEW_TABLE_SELECTOR}') not found.") # Less verbose


        # If Specific Result Page AND it matches the target type for this pass: Parse it
        elif is_target_result_page:
            # print(f"-> Target Page ({result_type_name}). Parsing...") # Verbose
            if column_mapping:
                 parsed_data = parse_function(html, target_url_to_fetch, result_type_name, column_mapping)
            else: # For pit stops
                 parsed_data = parse_function(html, target_url_to_fetch)

            if parsed_data:
                 # print(f"-> Parsed {len(parsed_data)} rows.") # Verbose
                 collected_data.extend(parsed_data)
            # else:
                # print(f"-> No data parsed.") # Less verbose

    if request_count >= max_requests_per_type:
         print(f"Warning: Reached request limit ({max_requests_per_type}) for {result_type_name}.")

    return collected_data


# --- Main Execution (Iterates through Result Types) ---
if __name__ == "__main__":
    print("="*40)
    print(" F1 Results Scraper by Type (Simplified)")
    print("="*40)
    print(f"Target Years: {START_YEAR} to {END_YEAR}")
    print(f"Output Dir: {OUTPUT_DIR}")
    print(f"Headless: {RUN_HEADLESS}")
    print(f"Timeout: {SELENIUM_WAIT_TIMEOUT}s")
    print("User Agent: Chrome/108") # Indicate older UA being used
    print("-" * 40)

    start_run_time = time.time()
    years = list(range(START_YEAR, END_YEAR + 1))
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # --- Define Tasks: One for each result type ---
    # Suffix must include .html as generated URLs will have it
    tasks = [
        ("/race-result.html", 'race', {'position': 1, 'driver_number': 2, 'driver': 3, 'team': 4, 'laps': 5, 'time_or_retired': 6, 'points': 7}, parse_results_table),
        ("/fastest-laps.html", 'fastest_lap', {'position': 1, 'driver_number': 2, 'driver': 3, 'team': 4, 'lap': 5, 'time_of_day': 6, 'lap_time': 7, 'avg_speed': 8}, parse_results_table),
        ("/qualifying.html", 'qualifying', {'position': 1, 'driver_number': 2, 'driver': 3, 'team': 4, 'q1_time': 5, 'q2_time': 6, 'q3_time': 7, 'laps': 8}, parse_results_table),
        ("/starting-grid.html", 'starting_grid', {'position': 1, 'driver_number': 2, 'driver': 3, 'team': 4, 'sg_time': 5}, parse_results_table),
        ("/pit-stop-summary.html", 'pit_stop', None, parse_pit_stop_summary),
        ("/practice-1.html", 'practice_1', {'position': 1, 'driver_number': 2, 'driver': 3, 'team': 4, 'lap_time': 5, 'gap': 6, 'laps': 7}, parse_results_table),
        ("/practice-2.html", 'practice_2', {'position': 1, 'driver_number': 2, 'driver': 3, 'team': 4, 'lap_time': 5, 'gap': 6, 'laps': 7}, parse_results_table),
        ("/practice-3.html", 'practice_3', {'position': 1, 'driver_number': 2, 'driver': 3, 'team': 4, 'lap_time': 5, 'gap': 6, 'laps': 7}, parse_results_table),
    ]

    total_rows_collected = 0

    # --- Loop through each task ---
    for suffix, type_name, col_map, parse_func in tasks:
        task_start_time = time.time()
        # Pass the correct parsing function based on the task definition
        data_for_type = crawl_single_result_type(years, suffix, type_name, col_map, parse_func)
        output_filename = os.path.join(OUTPUT_DIR, f"f1_{START_YEAR}-{END_YEAR}_{type_name}.csv")
        save_to_csv(data_for_type, output_filename)
        task_end_time = time.time()
        print(f"----- Finished crawl for: {type_name} -----")
        print(f"Collected {len(data_for_type)} rows.")
        print(f"Time for this type: {task_end_time - task_start_time:.2f} seconds.")
        print("-" * 40)
        total_rows_collected += len(data_for_type)

    # --- Overall Summary ---
    end_run_time = time.time()
    print("\n" + "=" * 40)
    print("All Scraping Tasks Finished!")
    print(f"Total rows collected across all files: {total_rows_collected}")
    print(f"Total execution time: {end_run_time - start_run_time:.2f} seconds")
    print(f"Data saved in directory: {OUTPUT_DIR}")
    print("=" * 40)