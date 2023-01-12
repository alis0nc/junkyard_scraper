from datetime import datetime
import scrapy


class PartsGaloreSpider(scrapy.Spider):
    name = "parts_galore"
    allowed_domains = ["www.parts-galore.com"]
    start_urls = ["https://www.parts-galore.com/inventory/"]

    def parse(self, response):
        def sel(nth):
            return f"descendant-or-self::td[{nth}]/text()"

        for row in response.css("table#alldata tbody tr"):
            year = row.xpath(sel(1)).get()
            make = row.xpath(sel(2)).get()
            model = row.xpath(sel(3)).get()
            vin = row.xpath(sel(4)).get()
            color = row.xpath(sel(5)).get()
            arrival_date = datetime.strptime(row.xpath(sel(6)).get(), "%Y-%m-%d")
            yard_row = row.xpath(sel(7)).get()

            assert row.xpath("@data-make").get().lower() == make.lower()
            assert row.xpath("@data-model").get().lower() == model.lower()

            yield {
                "year": year,
                "make": make,
                "model": model,
                "vin": vin,
                "row": yard_row,
                "color": color,
                "arrival_date": arrival_date,
            }
