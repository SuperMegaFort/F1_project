import requests
from scrapy.linkextractors import LinkExtractor
from scrapy.http import HtmlResponse

def test_link_extractor(allow_regex):  # Pass the regex as an argument
    url = "https://www.formula1.com/en/results/2024/races"
    response = requests.get(url)
    response.raise_for_status() # Raise an exception for bad status codes
    print(f"Response status code: {response.status_code}")  # Should be 200
    print(f"Response encoding: {response.encoding}")
    # print(response.text)  # Uncomment to print the *entire* HTML (can be very long!)  

    scrapy_response = HtmlResponse(url=url, body=response.content, encoding='utf-8')

    # Create the LinkExtractor with the given regex
    link_extractor = LinkExtractor(allow=allow_regex)

    links = link_extractor.extract_links(scrapy_response)

    for link in links:
        print(link.url)
    print(f"--- Regex: {allow_regex} - Found {len(links)} links ---") # Print the regex and count

if __name__ == "__main__":
    # Test different regular expressions, starting simple and getting more specific:
    test_link_extractor(r'race-result\.html')  # Very broad - any link with race-result.html
    test_link_extractor(r'/race-result\.html')  # Links starting with /race-result.html
    test_link_extractor(r'/[^/]+/race-result\.html')  # Links with one segment before race-result.html
    test_link_extractor(r'/\d+/[^/]+/race-result\.html')  # ...with a number before the segment
    test_link_extractor(r'/races/\d+/[^/]+/race-result\.html') # ... with /races/
    test_link_extractor(r'/en/results/\d{4}/races/\d+/[^/]+/race-result\.html')  # Your original (corrected) regex