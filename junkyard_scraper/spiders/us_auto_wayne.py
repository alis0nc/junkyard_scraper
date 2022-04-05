"""Parses the inventory page of US Auto Supply (Wayne, MI)"""
from datetime import datetime
import re
import scrapy


class UsAutoWayneSpider(scrapy.Spider):
    """Parses the inventory page of US Auto Supply (Wayne, MI)"""

    name = "us_auto_wayne"
    allowed_domains = ["usautosupplymi.com"]
    start_urls = [
        "https://usautosupplymi.com/upull/wayne/wayne-inventory/",
    ]

    def parse(self, response):
        def sel(data_label):
            return f'td[data-label="{data_label}"]::text'

        for row in response.css("table#vehiclesw tr"):
            if row.css("th"):
                continue  # discard the header row
            image_url = row.css("td[style] a::attr(href)")
            stock_number_regex = re.compile(r"STK[0-9]+", re.IGNORECASE)
            stock_number_match = stock_number_regex.search(image_url.get()) if image_url else None
            yield {
                "year": row.css(sel("Year")).get(),
                "make": row.css(sel("Make")).get(),
                "model": row.css(sel("Model")).get(),
                "color": row.css(sel("Color")).get(),
                "us_auto_reference": row.css(sel("Reference")).get(),
                "row": row.css(sel("Row")).get(),
                "arrival_date": datetime.strptime(row.css(sel("Arrived")).get(), "%m/%d/%y"),
                "stock_number": stock_number_match.group()
                if image_url and stock_number_match
                else None,
                "photo": response.urljoin(image_url.get()) if image_url else None,
            }
