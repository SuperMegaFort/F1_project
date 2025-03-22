import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy_splash import SplashRequest  


class F1ResultsCrawler(CrawlSpider):
    name = "f1_results_crawler"
    allowed_domains = ["www.formula1.com"]
    start_urls = ["https://www.formula1.com/en/results/2024/races"]

    rules = (
        Rule(LinkExtractor(
            allow=r'/en/results/\d{4}/races/\d+/[^/]+/race-result\.html',
            # restrict_xpaths='//div[@class="resultsarchive-wrapper"]'  # You can add this back *after* you confirm Splash is working
        ), callback='parse_race_result', follow=True),
        # Optional: Rule for other years (remove if not needed)
        Rule(LinkExtractor(allow=r'/en/results/\d{4}/races\.html'), follow=True),
    )

    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(url, self.parse, args={'wait': 0.5}) # Use SplashRequest

    def parse(self, response):
        #This parse is only used for the start_url, so that the rules will work
        #After the rule match, parse_race_result will be called.
        pass


    def parse_race_result(self, response):
        """
        Parse la page de résultats d'une course individuelle.
        """

        # Extraire l'année et le nom de la course
        year = response.url.split('/')[-4]
        race_name = response.xpath("//h1[@class='ResultsArchiveTitle']/text()").get()
        if race_name:
             race_name = race_name.strip()


        # --- TABLEAU DES RÉSULTATS PRINCIPAUX ---
        table = response.xpath("//table[contains(@class, 'resultsarchive-table')]")

        if not table:
             self.logger.warning(f"Tableau de résultats non trouvé sur {response.url}")
             return

        rows = table.xpath(".//tr")[1:]  # Exclure l'en-tête
        for row in rows:
            position = row.xpath("./td[2]/text()").get().strip()
            driver_number = row.xpath("./td[3]/text()").get().strip()

            driver_name_span = row.xpath("./td[4]/span[contains(@class, 'hide-for-mobile')]/text()").get()
            driver_surname_span = row.xpath("./td[4]/span[contains(@class, 'hide-for-tablet')]/text()").get()
            driver_name = ""
            if driver_name_span:
                driver_name += driver_name_span.strip()
            if driver_surname_span:
                driver_name += " " + driver_surname_span.strip()


            driver_code = row.xpath("./td[4]/span[not(contains(@class,'hide-for'))]/text()").get()
            if driver_code is not None:
                driver_code.strip()

            team = row.xpath("./td[5]/text()").get().strip()
            laps = row.xpath("./td[6]/text()").get().strip()
            time_or_retired = row.xpath("./td[7]/text()").get().strip()
            points = row.xpath("./td[8]/text()").get().strip()

            yield {
                'year': year,
                'race_name': race_name,
                'result_type': 'race',
                'position': position,
                'driver_number': driver_number,
                'driver_name': driver_name,
                'driver_code': driver_code,
                'team': team,
                'laps': laps,
                'time_or_retired': time_or_retired,
                'points': points,
                'url': response.url,
            }


        # --- EXTRACTION DES MEILLEURS TOURS ---
        fastest_laps_table = response.xpath("//table[contains(@class, 'fastest-laps')]")
        if fastest_laps_table:
            rows = fastest_laps_table.xpath(".//tr")[1:]
            for row in rows:
                position = row.xpath("./td[2]/text()").get().strip()
                driver_number = row.xpath("./td[3]/text()").get().strip()
                driver_name_fastest = row.xpath("./td[4]//span[contains(@class, 'hide-for-mobile')]/text()").get()
                driver_surname = row.xpath("./td[4]//span[contains(@class, 'hide-for-tablet')]/text()").get()

                driver_name = ""

                if driver_name_fastest:
                    driver_name += driver_name_fastest.strip()
                if driver_surname:
                    driver_name += " "+ driver_surname.strip()

                team = row.xpath("./td[5]/text()").get().strip()
                lap = row.xpath("./td[6]/text()").get().strip()
                time_of_day = row.xpath("./td[7]/text()").get().strip()
                time = row.xpath("./td[8]/text()").get().strip()
                avg_speed = row.xpath("./td[9]/text()").get().strip()

                yield {
                    'year': year,
                    'race_name': race_name,
                    'result_type': 'fastest_lap',
                    'position': position,
                    'driver_number': driver_number,
                    'driver_name': driver_name,
                    'team': team,
                    'lap': lap,
                    'time_of_day': time_of_day,
                    'time': time,
                    'avg_speed': avg_speed,
                    'url': response.url
                }
        else:
            self.logger.warning(f"Aucun tableau de meilleurs tours trouvé pour {response.url}")