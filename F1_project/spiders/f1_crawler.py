# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import time
import csv
import os
import traceback

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

START_YEAR = 2024
END_YEAR = 2024

BASE_URL = "https://www.formula1.com"
RESULTS_BASE_URL = f"{BASE_URL}/en/results.html"
ALLOWED_DOMAIN = urlparse(BASE_URL).netloc
OUTPUT_DIR = "f1_results_by_type_simple"

SELENIUM_WAIT_TIMEOUT = 30
REQUEST_DELAY_SECONDS = 2
RUN_HEADLESS = True
max_requests_per_type = 500 

YEARLY_OVERVIEW_PATTERN = re.compile(r'/en/results\.html/(\d{4})/races\.html$', re.IGNORECASE)
RACE_LINK_IDENTIFIER_PATTERN = re.compile(r'/en/results\.html/(\d{4})/races/(\d+)/([^/]+)')

DEFAULT_WAIT_ELEMENT = "footer"
OVERVIEW_TABLE_SELECTOR = "table.f1-table.f1-table-with-data"
DATA_TABLE_SELECTOR = "table.resultsarchive-table, table.f1-table.f1-table-with-data"

SELENIUM_OPTIONS = Options()
if RUN_HEADLESS:
    SELENIUM_OPTIONS.add_argument('--headless')
SELENIUM_OPTIONS.add_argument('--disable-gpu')
SELENIUM_OPTIONS.add_argument('--no-sandbox')
SELENIUM_OPTIONS.add_argument('--window-size=1920,1080')
SELENIUM_OPTIONS.add_argument('--disable-dev-shm-usage')
SELENIUM_OPTIONS.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36')

def get_rendered_html_selenium(url, wait_for_selector, timeout=SELENIUM_WAIT_TIMEOUT):
    print(f"Fetching: {url} (Wait: '{wait_for_selector}', Timeout: {timeout}s)")
    driver = None
    service = None
    html_content = None
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=SELENIUM_OPTIONS)
        driver.get(url)
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_selector))
        )
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
                if extracted_race and len(extracted_race) > 3 : race_name = extracted_race
                if extracted_year: year = extracted_year
            elif year != "Unknown":
                 cleaned_name = full_title.replace(year, '').replace('FORMULA 1', '').replace('GRAND PRIX', '').strip(' -').strip()
                 cleaned_name = re.sub(r'\b(Race Result|Fastest Laps|Qualifying|Practice\s*\d|Starting Grid|Pit Stop Summary)\b', '', cleaned_name, flags=re.IGNORECASE).strip()
                 if cleaned_name: race_name = cleaned_name
    except Exception: pass
    if race_name == "Unknown" or race_name.lower() == 'results' or not race_name:
        if location != "Unknown": race_name = location.replace('-', ' ').title() + " Grand Prix"
        else: race_name = "Unknown Race"
    return year, race_name, race_id_str

def parse_driver_cell(driver_cell):
    driver_name, driver_code = '', ''
    if not driver_cell: return driver_name, driver_code
    first_name_span = driver_cell.select_one("span.hide-for-mobile")
    last_name_span = driver_cell.select_one("span.hide-for-tablet")
    code_span = driver_cell.select_one("span.hide-for-desktop")
    driver_first_name = first_name_span.text.strip() if first_name_span else ''
    driver_last_name = last_name_span.text.strip() if last_name_span else ''
    if driver_first_name and driver_last_name: driver_name = f"{driver_first_name} {driver_last_name}"
    elif driver_first_name: driver_name = driver_first_name
    elif driver_last_name: driver_name = driver_last_name
    if code_span: driver_code = code_span.text.strip()
    if not driver_name and not driver_code:
        full_text = driver_cell.get_text(" ", strip=True); parts = full_text.split()
        if parts:
            if len(parts[-1]) == 3 and parts[-1].isupper(): driver_code = parts[-1]; driver_name = " ".join(parts[:-1])
            else: driver_name = full_text
    elif not driver_name and driver_code: driver_name = driver_cell.get_text(" ", strip=True).replace(driver_code, '').strip()
    elif driver_name and not driver_code:
        full_text_minus_name = driver_cell.get_text(" ", strip=True).replace(driver_name, '').strip()
        if len(full_text_minus_name) == 3 and full_text_minus_name.isupper(): driver_code = full_text_minus_name
    if (driver_first_name and not driver_last_name) or (not driver_first_name and driver_last_name):
        current_name_part = driver_first_name or driver_last_name; full_cell_text = driver_cell.get_text(" ", strip=True)
        if driver_code and full_cell_text.endswith(driver_code):
            potential_full_name = full_cell_text[:-len(driver_code)].strip()
            if current_name_part in potential_full_name : driver_name = potential_full_name
        elif current_name_part != full_cell_text and full_cell_text : driver_name = full_cell_text
    return driver_name.strip(), driver_code.strip()

def parse_results_table(html_content, url, result_type_name, column_mapping):
    results = []
    if not html_content: return results
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        year, race_name, race_id = extract_metadata(soup, url)
        data_table = soup.select_one(DATA_TABLE_SELECTOR)
        if not data_table: return results
        tbody = data_table.select_one("tbody"); rows = tbody.select("tr") if tbody else data_table.select("tr:not(:first-child)")
        highest_req_index = -1
        if column_mapping: highest_req_index = max(column_mapping.values())
        for row_idx, row in enumerate(rows):
            cols = row.select("td")
            if highest_req_index != -1 and len(cols) <= highest_req_index : continue
            row_data = {'year': year, 'race_name': race_name, 'race_id': race_id, 'result_type': result_type_name, 'url': url}
            has_essential_data = False
            for col_name, col_index in column_mapping.items():
                if col_index < len(cols):
                    cell = cols[col_index]
                    if col_name == 'driver':
                        name, code = parse_driver_cell(cell); row_data['driver_name'] = name; row_data['driver_code'] = code
                        if name or code: has_essential_data = True
                    elif col_name == 'team':
                        row_data[col_name] = cell.get_text(strip=True)
                        if row_data[col_name]: has_essential_data = True
                    else:
                        row_data[col_name] = cell.get_text(strip=True)
                        if col_name == 'position' and row_data[col_name] and (row_data[col_name].isdigit() or len(row_data[col_name]) <= 3): has_essential_data = True
                else: row_data[col_name] = ''
            if has_essential_data: results.append(row_data)
    except Exception as e: print(f"!!! Error parsing {result_type_name} table for {url}: {type(e).__name__} - {e}")
    return results

def parse_pit_stop_summary(html_content, url):
    results = []; result_type_name = 'pit_stop'
    if not html_content: return results
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        year, race_name, race_id = extract_metadata(soup, url)
        data_table = soup.select_one(DATA_TABLE_SELECTOR);
        if not data_table: return results
        tbody = data_table.select_one("tbody"); rows = tbody.select("tr") if tbody else data_table.select("tr:not(:first-child)")
        pit_stop_mapping = {'stops': 0, 'driver_number': 1, 'driver': 2, 'team': 3, 'lap': 4, 'time_of_day': 5, 'pit_time': 6, 'total_pit_time': 7}
        highest_req_index_pit = max(pit_stop_mapping.values())
        for row in rows:
            cols = row.select("td")
            if len(cols) <= highest_req_index_pit and len(cols) < 7: continue
            row_data = {'year': year, 'race_name': race_name, 'race_id': race_id, 'result_type': result_type_name, 'url': url}
            has_essential_data = False
            for col_name, col_index in pit_stop_mapping.items():
                if col_index < len(cols):
                    cell = cols[col_index]
                    if col_name == 'driver':
                        name, code = parse_driver_cell(cell); row_data['driver_name'], row_data['driver_code'] = name, code
                        if name or code: has_essential_data = True
                    elif col_name == 'team':
                        row_data[col_name] = cell.get_text(strip=True)
                        if row_data[col_name]: has_essential_data = True
                    else:
                        row_data[col_name] = cell.get_text(strip=True)
                        if col_name == 'pit_time' and row_data[col_name]: has_essential_data = True
                else: row_data[col_name] = ''
            if has_essential_data: results.append(row_data)
    except Exception as e: print(f"!!! Error parsing pit stop table for {url}: {type(e).__name__} - {e}")
    return results

def save_to_csv(data, filename):
    if not data: print(f"No data collected for {filename}, skipping CSV save."); return
    print(f"\nAttempting to save {len(data)} data rows to {filename}...")
    all_possible_headers = [
        'year', 'race_name', 'race_id', 'result_type', 'url', 'position', 'driver_number', 
        'driver_code', 'driver_name', 'team', 'laps', 'time_or_retired', 'points', 'lap', 
        'time_of_day', 'lap_time', 'avg_speed', 'q1_time', 'q2_time', 'q3_time', 'sg_time', 
        'gap', 'stops', 'pit_time', 'total_pit_time'
    ]
    actual_headers = set(); [actual_headers.update(row.keys()) for row in data]
    final_headers = [h for h in all_possible_headers if h in actual_headers]
    [final_headers.append(h) for h in actual_headers if h not in final_headers]
    try:
        os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=final_headers, extrasaction='ignore', restval='')
            writer.writeheader(); writer.writerows(data)
        print(f"Successfully saved data to {filename}")
    except Exception as e: print(f"!!! ERROR saving data to CSV {filename}: {e}")

def crawl_single_result_type(years_to_scrape_list, target_suffix, result_type_name, column_mapping, parse_function):
    visited_specific_urls_this_call = set() 
    collected_data_for_this_task = []
    requests_made_this_call = 0
    print(f"\n----- Starting crawl for: {result_type_name}, Suffix: {target_suffix} -----")
    for year_to_process in years_to_scrape_list:
        print(f"Processing Year: {year_to_process}")
        overview_url = f"{RESULTS_BASE_URL}/{year_to_process}/races.html"
        if requests_made_this_call > 0: time.sleep(REQUEST_DELAY_SECONDS)
        overview_html = get_rendered_html_selenium(overview_url, OVERVIEW_TABLE_SELECTOR)
        requests_made_this_call += 1
        if not overview_html:
            print(f"Failed to get overview page {overview_url}. Skipping for {result_type_name}.")
            continue
        soup_overview = BeautifulSoup(overview_html, 'html.parser')
        discovered_race_targets_for_year = []
        content_area = soup_overview.select_one(OVERVIEW_TABLE_SELECTOR)
        if content_area:
            links = content_area.find_all('a', href=True)
            for link_tag in links:
                abs_link = urljoin(overview_url, link_tag['href'])
                match = RACE_LINK_IDENTIFIER_PATTERN.search(abs_link)
                if match and urlparse(abs_link).netloc == ALLOWED_DOMAIN:
                    year_from_link, race_id_str, loc_from_link = match.groups()
                    if str(year_from_link) != str(year_to_process): continue
                    try:
                        race_id_int = int(race_id_str)
                        base_race_url = f"{RESULTS_BASE_URL}/{year_from_link}/races/{race_id_str}/{loc_from_link}"
                        generated_target_url = base_race_url + target_suffix
                        discovered_race_targets_for_year.append((race_id_int, generated_target_url))
                    except ValueError: print(f"Warning: Bad race_id '{race_id_str}' from {abs_link}")
        else:
            print(f"Overview table not found on {overview_url}"); continue
        discovered_race_targets_for_year.sort(key=lambda x: x[0])
        race_count = len(discovered_race_targets_for_year)
        print(f"Found {race_count} races for {year_to_process}, type '{result_type_name}'. Processing in Race ID order.")
        for i, (race_id_val, specific_url_to_process) in enumerate(discovered_race_targets_for_year):
            if requests_made_this_call >= max_requests_per_type :
                print(f"Request limit ({max_requests_per_type}) reached for {result_type_name}. Stopping."); break
            if specific_url_to_process in visited_specific_urls_this_call: continue
            time.sleep(REQUEST_DELAY_SECONDS)
            html_specific = get_rendered_html_selenium(specific_url_to_process, DEFAULT_WAIT_ELEMENT)
            requests_made_this_call += 1
            visited_specific_urls_this_call.add(specific_url_to_process)
            if html_specific:
                parsed_data = parse_function(html_specific, specific_url_to_process, result_type_name, column_mapping) if column_mapping else parse_function(html_specific, specific_url_to_process)
                if parsed_data: collected_data_for_this_task.extend(parsed_data)
    return collected_data_for_this_task

if __name__ == "__main__":
    print("="*40 + f"\n F1 Results Scraper by Type\n" + "="*40)
    print(f"Years: {START_YEAR}-{END_YEAR}, Output: {OUTPUT_DIR}, Headless: {RUN_HEADLESS}, Timeout: {SELENIUM_WAIT_TIMEOUT}s")
    print("-" * 40); start_run_time = time.time(); os.makedirs(OUTPUT_DIR, exist_ok=True)
    tasks = [
        ("/race-result.html", 'race', {'position': 0, 'driver_number': 1, 'driver': 2, 'team': 3, 'laps': 4, 'time_or_retired': 5, 'points': 6}, parse_results_table),
        ("/fastest-laps.html", 'fastest_lap', {'position': 0, 'driver_number': 1, 'driver': 2, 'team': 3, 'lap': 4, 'time_of_day': 5, 'lap_time': 6, 'avg_speed': 7}, parse_results_table),
        ("/qualifying.html", 'qualifying', {'position': 0, 'driver_number': 1, 'driver': 2, 'team': 3, 'q1_time': 4, 'q2_time': 5, 'q3_time': 6, 'laps': 7}, parse_results_table),
        ("/starting-grid.html", 'starting_grid', {'position': 0, 'driver_number': 1, 'driver': 2, 'team': 3, 'sg_time': 4}, parse_results_table),
        ("/pit-stop-summary.html", 'pit_stop', None, parse_pit_stop_summary),
        ("/practice-1.html", 'practice_1', {'position': 0, 'driver_number': 1, 'driver': 2, 'team': 3, 'lap_time': 4, 'gap': 5, 'laps': 6}, parse_results_table),
        ("/practice-2.html", 'practice_2', {'position': 0, 'driver_number': 1, 'driver': 2, 'team': 3, 'lap_time': 4, 'gap': 5, 'laps': 6}, parse_results_table),
        ("/practice-3.html", 'practice_3', {'position': 0, 'driver_number': 1, 'driver': 2, 'team': 3, 'lap_time': 4, 'gap': 5, 'laps': 6}, parse_results_table),
    ]
    total_rows_collected = 0
    for year in range(START_YEAR, END_YEAR + 1):
        print(f"\n{'='*20} Processing Year: {year} {'='*20}"); year_start_time = time.time(); year_rows_collected = 0
        for suffix, type_name, col_map, parse_func in tasks:
            task_start_time = time.time()
            data_for_type = crawl_single_result_type([year], suffix, type_name, col_map, parse_func)
            output_filename = os.path.join(OUTPUT_DIR, f"f1_{year}_{type_name}.csv"); save_to_csv(data_for_type, output_filename)
            task_end_time = time.time(); rows_in_task = len(data_for_type)
            print(f"----- Finished: {type_name} ({year}), Suffix: {suffix} -----")
            print(f"Collected {rows_in_task} rows. Time: {task_end_time - task_start_time:.2f}s. Saved: {output_filename}\n" + "-"*40)
            total_rows_collected += rows_in_task; year_rows_collected += rows_in_task
        year_end_time = time.time()
        print(f"\n{'='*20} Finished Year: {year} {'='*20}\nRows for {year}: {year_rows_collected}. Time: {year_end_time - year_start_time:.2f}s.")
    end_run_time = time.time()
    print("\n" + "="*40 + "\nAll Scraping Tasks Finished!\n" + f"Total rows: {total_rows_collected}. Total time: {end_run_time - start_run_time:.2f}s.\nData in: {OUTPUT_DIR}\n" + "="*40)