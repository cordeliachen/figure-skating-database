from urllib.request import Request
import scrapy
from bs4 import BeautifulSoup
from scrapy.linkextractors import LinkExtractor


class IsuSpider(scrapy.Spider):
    name = "isu"

    def start_requests(self):
        yield scrapy.Request("https://www.isu.org/figure-skating/entries-results/fsk-results", self.parse)

    def parse(self, response):
        le = LinkExtractor("http://results.isu.org/.*")
        links = le.extract_links(response)
        yield response.follow_all(links.url, self.parse_comp)

    def parse_comp(self, response):
        le = LinkExtractor(".*\.pdf")
        files = le.extract_links(response)
