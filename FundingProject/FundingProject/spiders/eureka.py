import scrapy
from pymongo import MongoClient
from pathlib import Path
from urllib.parse import quote_plus
import certifi

class EurekaSpider(scrapy.Spider):
    name = 'eureka'
    allowed_domains = ['eurekanetwork.org']
    start_urls = [
        'https://eurekanetwork.org/opencalls/?category%5B0%5D=clusters&category%5B1%5D=eurostars&category%5B2%5D=globalstars&category%5B3%5D=innowwide&category%5B4%5D=network-projects&time=open-soon',
        'https://eurekanetwork.org/opencalls/?category%5B0%5D=clusters&category%5B1%5D=eurostars&category%5B2%5D=globalstars&category%5B3%5D=innowwide&category%5B4%5D=network-projects'
    ]

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
        self.collection = self.db['Eureka_fundings']

    def closed(self, reason):
        # Close MongoDB connection when spider is closed
        self.client.close()

    def parse(self, response):
        # Determine the status of the calls
        status = 'Coming Soon' if 'open-soon' in response.url else 'Open Call'

        # Save the HTML file
        page = response.url.split("?")[-1]
        filename = f"funding-{page}.html"
        Path(filename).write_bytes(response.body)
        self.log(f"Saved file {filename}")

        # Extract each call container
        call_containers = response.xpath('//div[contains(@class, "bg-white") and contains(@class, "group")]')
        
        for container in call_containers:
            item = {
                'url': container.xpath('.//a/@href').get(),
                'title': container.xpath('.//h2/text()').get(),
                'deadline': container.xpath('.//div[contains(text(), "Deadline")]/text()').get().replace('Deadline', '').strip() if container.xpath('.//div[contains(text(), "Deadline")]/text()') else None,
                'description': container.xpath('.//div[contains(@class, "paragraph-sm")]/text()').get(),
                'country': self.extract_country(container),
                'status': status
            }

            # Check if the item already exists in the database
            if not self.collection.find_one({'url': item['url']}):
                # Save item to MongoDB if it doesn't already exist
                self.collection.insert_one(item)
                yield item

        # Follow pagination links
        next_page = response.css('a.next.page-numbers::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def extract_country(self, container):
        # Additional logic to extract country information from multiple elements
        possible_country_elements = container.xpath('.//p[contains(text(), "country")]//text() | .//li[contains(text(), "country")]//text()')
        countries = ['Germany', 'Israel', 'UK', 'Canada', 'France', 'Spain']

        for element in possible_country_elements:
            text = element.get()
            for country in countries:
                if country in text:
                    return country
        
        # If no country is found in the possible elements, return 'Unknown'
        return 'Unknown'
