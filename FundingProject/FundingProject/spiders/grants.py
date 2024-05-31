import scrapy
from pymongo import MongoClient
from pathlib import Path
from datetime import datetime
import certifi
from urllib.parse import quote_plus

class GrantsSpider(scrapy.Spider):
    name = "grants"
    allowed_domains = ["find-government-grants.service.gov.uk"]
    start_urls = ["https://www.find-government-grants.service.gov.uk/grants"]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Escape username and password for MongoDB URI
        username = quote_plus('sam007')
        password = quote_plus('Das@007')
        self.client = MongoClient(
            f'mongodb+srv://{username}:{password}@das.nfmj12w.mongodb.net/',
            tlsCAFile=certifi.where()
        )

        self.db = self.client['DAS']
        self.collection = self.db['GOV_UK_funding']

    def closed(self, reason):
        # Close MongoDB connection when spider is closed
        self.client.close()

    def parse(self, response):

        # Extracting the grants
        grants = response.css('ul.grants_list li')

        for grant in grants:
            title = grant.css('h2 a::text').get()
            link = response.urljoin(grant.css('h2 a::attr(href)').get())
            description = grant.css('p.govuk-body::text').get()
            location = grant.xpath('.//dt[contains(text(), "Location")]/following-sibling::dd[1]/text()').get()
            funding_organisation = grant.xpath('.//dt[contains(text(), "Funding organisation")]/following-sibling::dd[1]/text()').get()
            who_can_apply = grant.xpath('.//dt[contains(text(), "Who can apply")]/following-sibling::dd[1]/text()').get()
            amount = grant.xpath('.//dt[contains(text(), "How much you can get")]/following-sibling::dd[1]/text()').get()
            total_size = grant.xpath('.//dt[contains(text(), "Total size of grant scheme")]/following-sibling::dd[1]/text()').get()
            opening_date = grant.xpath('.//dt[contains(text(), "Opening date")]/following-sibling::dd[1]/time/@datetime').get()
            closing_date = grant.xpath('.//dt[contains(text(), "Closing date")]/following-sibling::dd[1]/time/@datetime').get()

            # Transform dates to ISO format if necessary
            opening_date = self.format_date(opening_date)
            closing_date = self.format_date(closing_date)

            # Check if item already exists in the database
            existing_item = self.collection.find_one({'link': link})
            if not existing_item:
                data = {
                    'title': title,
                    'link': link,
                    'description': description,
                    'location': location,
                    'funding_organisation': funding_organisation,
                    'who_can_apply': who_can_apply,
                    'amount': amount,
                    'total_size': total_size,
                    'opening_date': opening_date,
                    'closing_date': closing_date
                }
                self.collection.insert_one(data)

                yield data

        # Extract pagination links and follow them
        next_page = response.css('li.moj-pagination__item--next a::attr(href)').get()
        if next_page:
            yield scrapy.Request(url=response.urljoin(next_page), callback=self.parse)

    @staticmethod
    def format_date(date_str):
        if date_str:
            try:
                return datetime.fromtimestamp(int(date_str) / 1000).isoformat()
            except ValueError:
                pass  # Handle the case where the date format is not as expected
        return None
