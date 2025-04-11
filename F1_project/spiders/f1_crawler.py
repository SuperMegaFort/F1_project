import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import time

# --- Selenium Imports ---
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# --- Configuration ---
START_URL = "https://www.formula1.com/en/results.html/2023/races.html"
ALLOWED_DOMAIN = "www.formula1.com"

# *** UPDATED REGEX PATTERNS ***
# Match ".../YYYY/races/NUMBER/LOCATION/race-result" (NO .html at the end)
RACE_RESULT_PATTERN = re.compile(r'/en/results\.html/\d{4}/races/\d+/[^/]+/race-result$')
# Keep this pattern as overview URLs might still end with .html
RACES_OVERVIEW_PATTERN = re.compile(r'/en/results\.html/\d{4}/races\.html$')
REQUEST_DELAY_SECONDS = 1
# *** UPDATED Selenium Wait Target (using the table selector) ***
SELENIUM_WAIT_TIMEOUT = 20
# Default wait element (e.g., footer)
WAIT_FOR_ELEMENT_SELECTOR = "footer"
# Specific selector for the table containing race links on overview pages
OVERVIEW_TABLE_SELECTOR = "table.f1-table.f1-table-with-data"


# --- Selenium Options --- (Keep as before)
SELENIUM_OPTIONS = Options()
SELENIUM_OPTIONS.add_argument('--headless')
SELENIUM_OPTIONS.add_argument('--disable-gpu')
SELENIUM_OPTIONS.add_argument('--no-sandbox')
SELENIUM_OPTIONS.add_argument('--window-size=1920,1080')
SELENIUM_OPTIONS.add_argument('--disable-dev-shm-usage')
SELENIUM_OPTIONS.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36')


# --- Helper Functions ---

# get_rendered_html_selenium function (remains the same as previous version)
# It accepts wait_for_selector and timeout arguments
def get_rendered_html_selenium(url, wait_for_selector=WAIT_FOR_ELEMENT_SELECTOR, timeout=SELENIUM_WAIT_TIMEOUT):
    """
    Fetches and renders HTML content from a URL using Selenium WebDriver.
    Waits for a specific element to be present to ensure dynamic content loads.
    """
    print(f"Fetching and rendering (Selenium): {url}")
    driver = None
    service = None
    try:
        print("Setting up Chrome driver...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=SELENIUM_OPTIONS)
        driver.get(url)

        print(f"Waiting up to {timeout}s for element '{wait_for_selector}'...")
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_selector))
        )
        print("Element found, page likely loaded.")

        html_content = driver.page_source
        return html_content

    except Exception as e:
        print(f"Error fetching/rendering {url} with Selenium: {e}")
        return None
    finally:
        if driver:
            print("Closing Selenium WebDriver.")
            driver.quit()


# parse_race_result_bs function (remains the same as previous version)
# It uses the updated RACE_RESULT_PATTERN implicitly via the URL structure check
def parse_race_result_bs(html_content, url):
    """
    Parses the race result page using BeautifulSoup, adjusted for 7 columns,
    with robust error handling ensuring it always returns two lists.
    """
    # Initialize return values at the beginning
    race_results = []
    fastest_laps_data = []

    try: # Wrap the entire parsing logic in a try block
        if not html_content:
            print(f"Error: No HTML content received for {url} (parsing step)")
            # Return empty lists immediately if no HTML
            return [], [] # Already returning 2 values

        soup = BeautifulSoup(html_content, 'html.parser')

        print(f"--- Starting Parse for: {url} ---")

        # --- Extract metadata ---
        year = "Unknown Year" # Default value
        race_name = "Unknown Race" # Default value
        try: # Add specific try-except for metadata
            year_match = re.search(r'/en/results\.html/(\d{4})/', url)
            if year_match:
                year = year_match.group(1)

            title_tag = soup.select_one("h1.ResultsArchiveTitle") # Old selector
            if not title_tag:
                title_tag = soup.select_one("h1.f1-heading") # New selector fallback
            if title_tag:
                race_name = title_tag.get_text(strip=True)

            print(f"Year: {year}, Race Name: {race_name}")
        except Exception as e_meta:
            print(f"!!! ERROR extracting metadata for {url}: {e_meta}")
            # Keep default year/race_name assigned above

        # --- Main Results Table ---
        try: # Add specific try-except for main results table processing
            results_table = soup.select_one("table.resultsarchive-table") # Old selector
            if not results_table:
                # print("Warning: 'table.resultsarchive-table' not found, trying 'table.f1-table.f1-table-with-data'")
                results_table = soup.select_one("table.f1-table.f1-table-with-data") # New selector

            if results_table:
                tbody = results_table.select_one("tbody")
                rows = tbody.select("tr") if tbody else results_table.select("tr")
                if not tbody and rows: rows = rows[1:] # Skip header if no tbody

                print(f"Found {len(rows)} data rows in main results table. Processing...")
                rows_appended_count = 0

                for i, row in enumerate(rows):
                    # print(f"\n--- Processing Row {i+1}/{len(rows)} ---") # Verbose Debug
                    cols = row.select("td")
                    # print(f"  Number of columns found in this row: {len(cols)}") # Verbose Debug

                    # Use 7 columns check based on previous findings
                    if len(cols) < 7:
                        # print(f"  !!! Skipping row {i+1} due to insufficient columns ({len(cols)} found, expected 7+).") # Verbose Debug
                        continue

                    try: # Inner try-except for row processing (robustness)
                        # Extract data safely checking list bounds
                        position = cols[1].get_text(strip=True) if len(cols) > 1 else ''
                        driver_number = cols[2].get_text(strip=True) if len(cols) > 2 else ''
                        driver_cell = cols[3] if len(cols) > 3 else None
                        team = cols[4].get_text(strip=True) if len(cols) > 4 else ''
                        laps = cols[5].get_text(strip=True) if len(cols) > 5 else ''
                        time_or_retired = cols[6].get_text(strip=True) if len(cols) > 6 else ''

                        # Points column (cols[7]) is missing based on prior debug output
                        points = ''
                        # print(f"  Col 1 (Pos): '{position}' ... Col 6 (Time): '{time_or_retired}' | Points set to '{points}'") # Verbose Debug

                        # Driver Name/Code Extraction
                        driver_name = ''
                        driver_code = ''
                        if driver_cell:
                            # print(f"  Col 3 (Driver) HTML: {str(driver_cell)[:200]}...") # Verbose Debug
                            first_name_span = driver_cell.select_one("span.hide-for-mobile")
                            last_name_span = driver_cell.select_one("span.hide-for-tablet")
                            abbr_span = driver_cell.select_one("span.hide-for-desktop") # Check if this still works

                            driver_name = f"{first_name_span.get_text(strip=True) if first_name_span else ''} {last_name_span.get_text(strip=True) if last_name_span else ''}".strip()
                            driver_code = abbr_span.get_text(strip=True) if abbr_span else ''
                            # print(f"  Driver Name (spans): '{driver_name}'") # Verbose Debug
                            # print(f"  Driver Code (spans): '{driver_code}'") # Verbose Debug

                            # Fallback logic if specific spans failed
                            if not driver_name and not driver_code:
                                # print("  -> Specific driver spans failed, attempting fallback parsing...") # Verbose Debug
                                all_text = driver_cell.get_text(" ", strip=True)
                                # print(f"     Fallback text from cell: '{all_text}'") # Verbose Debug
                                parts = all_text.split()
                                if len(parts) >= 2:
                                    if len(parts[-1]) == 3 and parts[-1].isupper():
                                        driver_name = " ".join(parts[:-1])
                                        driver_code = parts[-1]
                                        # print(f"     Fallback success (Name+Code): Name='{driver_name}', Code='{driver_code}'") # Verbose Debug
                                    else:
                                        driver_name = all_text
                                        # print(f"     Fallback result (Assume Name only): Name='{driver_name}'") # Verbose Debug
                                elif len(parts) == 1:
                                    if len(parts[0]) == 3 and parts[0].isupper():
                                        driver_code = parts[0]
                                        # print(f"     Fallback result (Assume Code only): Code='{driver_code}'") # Verbose Debug
                                    else:
                                        driver_name = parts[0]
                                        # print(f"     Fallback result (Assume Name only): Name='{driver_name}'") # Verbose Debug
                        else:
                            print(f"  !!! Warning: Driver Cell (Col 3) not found in row {i+1}.")


                        # Append data if essential fields have values
                        if position and team:
                            result_data = {
                                'year': year, 'race_name': race_name, 'result_type': 'race',
                                'position': position, 'driver_number': driver_number, 'driver_name': driver_name,
                                'driver_code': driver_code, 'team': team, 'laps': laps,
                                'time_or_retired': time_or_retired,
                                'points': points, # Points set to ''
                                'url': url,
                            }
                            # print(f"  ==> Appending data for row {i+1}") # Verbose Debug
                            race_results.append(result_data)
                            rows_appended_count += 1
                        else:
                            # print(f"  !!! Skipping append for row {i+1} due to missing Pos or Team.") # Verbose Debug
                            pass

                    except Exception as e_row:
                        print(f"  !!! ERROR processing row {i+1} in main table: {e_row}")
                        # print(traceback.format_exc()) # Uncomment for deep debug
                        continue # Skip to next row

                print(f"Finished processing main table rows for {url}. Appended {rows_appended_count} rows.")
            else:
                print(f"Error: Main results table not found using known selectors on {url}")

        except Exception as e_main_table:
             print(f"!!! ERROR processing main results table section for {url}: {e_main_table}")
             print(traceback.format_exc()) # Show where this error happens

        # --- Fastest Laps Table ---
        try: # Add specific try-except for fastest laps table processing
            fl_selector = "table[class*='fastest-laps']:not(.resultsarchive-table):not(.f1-table-with-data)"
            fastest_laps_table = soup.select_one(fl_selector)

            if fastest_laps_table:
                print(f"Found separate fastest laps table ({fl_selector}) on {url}. Parsing...")
                fl_tbody = fastest_laps_table.select_one("tbody")
                fl_rows = fl_tbody.select("tr") if fl_tbody else fastest_laps_table.select("tr")
                if not fl_tbody and fl_rows: fl_rows = fl_rows[1:] # Skip header if no tbody

                print(f"Found {len(fl_rows)} rows in fastest laps table.")
                fl_rows_appended_count = 0

                for i, row in enumerate(fl_rows):
                    cols = row.select("td")
                    if len(cols) < 9: # Expect 9 cols based on original logic
                        # print(f"  !!! Skipping FL row {i+1} due to insufficient columns ({len(cols)} found, expected 9).") # Verbose Debug
                        continue

                    try: # Inner try-except for row processing
                        position = cols[1].get_text(strip=True)
                        driver_number = cols[2].get_text(strip=True)
                        driver_cell_fl = cols[3]
                        team = cols[4].get_text(strip=True)
                        lap = cols[5].get_text(strip=True)
                        time_of_day = cols[6].get_text(strip=True)
                        lap_time = cols[7].get_text(strip=True)
                        avg_speed = cols[8].get_text(strip=True)

                        # Driver Name/Code Extraction (FL Table)
                        driver_name_fl = ''
                        if driver_cell_fl:
                            # Assume similar structure, may need adjustment
                            first_name_span_fl = driver_cell_fl.select_one("span.hide-for-mobile")
                            last_name_span_fl = driver_cell_fl.select_one("span.hide-for-tablet")
                            driver_name_fl = f"{first_name_span_fl.get_text(strip=True) if first_name_span_fl else ''} {last_name_span_fl.get_text(strip=True) if last_name_span_fl else ''}".strip()
                            # Fallback
                            if not driver_name_fl:
                                all_text_fl = driver_cell_fl.get_text(" ", strip=True)
                                parts_fl = all_text_fl.split()
                                if len(parts_fl) > 0: driver_name_fl = " ".join(parts_fl)

                        # Append data
                        fastest_lap_entry = {
                            'year': year, 'race_name': race_name, 'result_type': 'fastest_lap',
                            'position': position, 'driver_number': driver_number, 'driver_name': driver_name_fl,
                            'team': team, 'lap': lap, 'time_of_day': time_of_day,
                            'time': lap_time, 'avg_speed': avg_speed, 'url': url
                        }
                        fastest_laps_data.append(fastest_lap_entry)
                        fl_rows_appended_count += 1

                    except Exception as e_fl_row:
                        print(f"  !!! ERROR processing Fastest Lap row {i+1}: {e_fl_row}")
                        # print(traceback.format_exc()) # Uncomment for deep debug
                        continue # Skip row on error

                print(f"Finished processing FL rows. Appended {fl_rows_appended_count} rows.")
            # else: # Reduce noise
                # print(f"Info: Separate fastest laps table ('{fl_selector}') not found on {url}.")

        except Exception as e_fl_table:
            print(f"!!! ERROR processing fastest laps table section for {url}: {e_fl_table}")
            print(traceback.format_exc())

    except Exception as e_global: # Catch any unexpected error during the whole parse
        print(f"!!! UNEXPECTED GLOBAL ERROR during parsing {url}: {e_global}")
        print(traceback.format_exc())
        # Lists initialized at start will be returned by finally

    finally:
        # This block ensures the function always returns a tuple of two lists
        print(f"--- Finished Parse Attempt for: {url} ---")
        # Return the lists, which contain data processed before any error might have occurred
        return race_results, fastest_laps_data


# --- Main Crawling Logic ---
def crawl_f1_results_bs(start_url):
    urls_to_visit = {start_url}
    visited_urls = set()
    all_race_results = []
    all_fastest_laps = []
    request_count = 0

    while urls_to_visit:
        if request_count > 0 :
            print(f"Waiting for {REQUEST_DELAY_SECONDS} seconds before next request...")
            time.sleep(REQUEST_DELAY_SECONDS)

        # Get the URL as it was found/queued
        current_url_from_queue = urls_to_visit.pop()
        request_count += 1

        # ---- Start Modification ----
        # Assume the target URL is the same initially
        target_url_to_fetch = current_url_from_queue
        is_potential_result_page = RACE_RESULT_PATTERN.search(current_url_from_queue)

        # If it looks like a result page URL (based on the pattern *without* .html)
        # ADD .html before attempting to fetch it.
        if is_potential_result_page:
            if not target_url_to_fetch.endswith('.html'):
                target_url_to_fetch += ".html"
                print(f"Appended .html for fetching result page: {target_url_to_fetch}")
        # ---- End Modification ----


        # --- Now use target_url_to_fetch for visiting ---
        if target_url_to_fetch in visited_urls:
            print(f"Skipping already visited: {target_url_to_fetch}")
            continue

        if ALLOWED_DOMAIN not in target_url_to_fetch:
            print(f"Skipping URL outside allowed domain: {target_url_to_fetch}")
            continue

        # Add the URL we are *actually* fetching to the visited set
        visited_urls.add(target_url_to_fetch)

        # Determine wait selector based on the *original* URL type from the queue
        wait_selector = OVERVIEW_TABLE_SELECTOR if RACES_OVERVIEW_PATTERN.search(current_url_from_queue) else WAIT_FOR_ELEMENT_SELECTOR
        # Fetch the potentially modified URL
        html = get_rendered_html_selenium(target_url_to_fetch, wait_for_selector=wait_selector)

        if not html:
            print(f"Skipping parsing for {target_url_to_fetch} due to fetch/render error.")
            continue

        current_soup = BeautifulSoup(html, 'html.parser')

        # --- Use original URL pattern match to decide *what* to parse ---
        # But pass the *fetched* URL (target_url_to_fetch) to the parser
        if is_potential_result_page: # Use the check from before modification
             print(f"Parsing Race Result page: {target_url_to_fetch}")
             # Pass the actual fetched URL to the parser
             race_results, fastest_laps = parse_race_result_bs(html, target_url_to_fetch)
             all_race_results.extend(race_results)
             all_fastest_laps.extend(fastest_laps)

        # --- Check original URL for overview page pattern ---
        elif RACES_OVERVIEW_PATTERN.search(current_url_from_queue):
             print(f"Processing overview page for links: {target_url_to_fetch}") # Log the URL we fetched
             links_found_matching_pattern = 0
             search_area = current_soup.select_one(OVERVIEW_TABLE_SELECTOR)

             if not search_area:
                 print(f"Error: Could not find the link container table ('{OVERVIEW_TABLE_SELECTOR}') on {target_url_to_fetch}.")
                 continue

             log_selector = OVERVIEW_TABLE_SELECTOR
             all_links_in_area = search_area.find_all('a', href=True)
             print(f"Found {len(all_links_in_area)} total links in search area '{log_selector}'.")

             for i, link in enumerate(all_links_in_area):
                 href = link['href']
                 # Construct absolute URL using the *fetched* URL (target_url_to_fetch) as base
                 absolute_link = urljoin(target_url_to_fetch, href)

                 # Check the absolute link against the original patterns (results *without* .html initially)
                 is_result_link_match = RACE_RESULT_PATTERN.search(absolute_link)
                 is_overview_link_match = RACES_OVERVIEW_PATTERN.search(absolute_link)

                 # Add the raw link (without .html appended yet) to the queue if it matches
                 if ALLOWED_DOMAIN in absolute_link and \
                    (is_result_link_match or is_overview_link_match) and \
                    absolute_link not in visited_urls and \
                    absolute_link not in urls_to_visit:

                     print(f"  MATCH FOUND & Queueing ({'Result' if is_result_link_match else 'Overview'}): {absolute_link}")
                     urls_to_visit.add(absolute_link) # Add the unmodified link
                     links_found_matching_pattern += 1

             print(f"Found and queued {links_found_matching_pattern} new relevant links from {target_url_to_fetch}")
        else:
             # Log based on the original URL from queue if it didn't match known patterns
             print(f"Skipping URL (doesn't match expected patterns based on original queue URL): {current_url_from_queue}")


    return all_race_results, all_fastest_laps

    # --- Execution ---
if __name__ == "__main__":
    print("Starting F1 Results Scraper using Selenium and BeautifulSoup...")
    print(f"Make sure you have installed: pip install beautifulsoup4 requests selenium webdriver-manager")
    print(f"Initial URL: {START_URL}")
    # Display current time using the provided context
    print(f"Script started around: {time.strftime('%Y-%m-%d %H:%M:%S')}") # Use standard time
    print("-" * 30)

    final_results, final_fastest_laps = crawl_f1_results_bs(START_URL)

    print("\n" + "=" * 30)
    print("Scraping Finished!")
    print(f"Total race results found: {len(final_results)}")
    print(f"Total fastest laps found: {len(final_fastest_laps)}")
    print("=" * 30 + "\n")

    # Example: Print the first few results if any were found
    if final_results:
        print("--- Example Race Results (First 5) ---")
        for result in final_results[:5]:
            print(result)
    else:
        print("--- No Race Results Found ---")


    if final_fastest_laps:
        print("\n--- Example Fastest Laps (First 5) ---")
        for lap in final_fastest_laps[:5]:
            print(lap)
    else:
        # This is expected behaviour for recent years on F1.com
        print("\n--- No Separate Fastest Lap Data Found (This might be normal) ---")