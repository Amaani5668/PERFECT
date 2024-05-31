import scrapy
from pymongo import MongoClient
from pathlib import Path
from urllib.parse import quote_plus
import certifi

class FundsSpider(scrapy.Spider):
    name = "funds"
    allowed_domains = ["ukri.org"]
    start_urls = ["https://ukri.org"]

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
        self.collection = self.db['UKRI_fundings']

    def closed(self, reason):
        # Close MongoDB connection when spider is closed
        self.client.close()

    def start_requests(self):
        urls = [
            "https://www.ukri.org/opportunity/?keywords&filter_council%5B0%5D=814&filter_council%5B1%5D=816&filter_council%5B2%5D=818&filter_council%5B3%5D=820&filter_council%5B4%5D=822&filter_council%5B5%5D=824&filter_council%5B6%5D=826&filter_council%5B7%5D=828&filter_council%5B8%5D=830&filter_council%5B9%5D=1730&filter_status%5B0%5D=open&filter_status%5B1%5D=upcoming&filter_order=publication_date&filter_submitted=true",
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        page = response.url.split("/")[-2]
        filename = f"funding-{page}.html"
        Path(filename).write_bytes(response.body)
        self.log(f"Saved file {filename}")
        opportunities = response.css('div.opportunity')

        for opportunity in opportunities:
            title = opportunity.css('h3.entry-title a::text').get()
            link = opportunity.css('h3.entry-title a::attr(href)').get()
            description = opportunity.css('div.entry-content p::text').get()
            status = opportunity.css('dd span.opportunity-status__flag::text').get()
            funders = opportunity.css('dd a.ukri-funder__link::text').get()
            co_funders = opportunity.css('div.govuk-table__row:nth-child(3) dd.opportunity-cells::text').get()
            funding_type = opportunity.xpath('.//dt[contains(text(), "Funding type:")]/following-sibling::dd[1]/descendant-or-self::text()').get()
            total_fund = opportunity.xpath('.//dt[contains(text(), "Total fund:")]/following-sibling::dd[1]/descendant-or-self::text()').get()
            publication_date = opportunity.xpath('.//dt[contains(text(), "Publication date:")]/following-sibling::dd[1]/descendant-or-self::text()').get()
            opening_date = opportunity.xpath('.//dt[contains(text(), "Opening date:")]/following-sibling::dd[1]/time/@datetime').get()
            closing_date = opportunity.xpath('.//dt[contains(text(), "Closing date:")]/following-sibling::dd[1]/time/@datetime').get()

            # Check if item already exists in the database
            existing_item = self.collection.find_one({'link': link})
            if not existing_item:
                # Store the data in MongoDB
                data = {
                    'title': title,
                    'link': link,
                    'description': description,
                    'status': status,
                    'funders': funders,
                    'co_funders': co_funders,
                    'funding_type': funding_type,
                    'total_fund': total_fund,
                    'publication_date': publication_date,
                    'opening_date': opening_date,
                    'closing_date': closing_date
                }
                self.collection.insert_one(data)

                yield data

        # Extract pagination links and follow them
        next_page = response.css('a.next.page-numbers::attr(href)').get()
        if next_page:
            yield scrapy.Request(url=next_page, callback=self.parse)
