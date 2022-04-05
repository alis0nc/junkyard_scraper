"""Parses the inventory page of US Auto Supply (Sterling Heights, MI)"""
from datetime import datetime
import scrapy


class UsAutoSpider(scrapy.Spider):
    """Parses the inventory page of US Auto Supply (Sterling Heights, MI)"""

    name = "us_auto"
    allowed_domains = ["usautosupplymi.com"]
    start_urls = [
        "https://usautosupplymi.com/upull/sterling-heights/sterling-heights-inventory/",
    ]

    def parse(self, response):
        def sel(data_label):
            return f'td[data-label="{data_label}"]::text'

        for row in response.css("table#vehicles tr"):
            if row.css("th"):
                continue  # discard the header row
            yield {
                "year": row.css(sel("Year")).get(),
                "make": row.css(sel("Make")).get(),
                "model": row.css(sel("Model")).get(),
                "color": row.css(sel("Color")).get(),
                "us_auto_reference": row.css(sel("Reference")).get(),
                "row": row.css(sel("Row")).get(),
                "arrival_date": datetime.strptime(row.css(sel("Arrived")).get(), "%m/%d/%y"),
                "stock_number": row.css("td[style]::text").get(),
                "photo": response.urljoin(row.css("td[style] a::attr(href)").get())
                if row.css("td[style] a::attr(href)")
                else None,
            }
