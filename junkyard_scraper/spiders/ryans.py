from datetime import datetime
import scrapy


class RyansSpider(scrapy.Spider):
    name = "ryans"
    allowed_domains = ["ryanspickapart.com"]
    start_urls = ["http://ryanspickapart.com/Home/Inventory"]

    def parse(self, response):
        # first, get a list of all makes
        all_makes = response.css("select#car-make option::attr(value)").getall()
        assert all_makes[0] == ""
        all_makes.pop(0)

        for make in all_makes:
            yield scrapy.FormRequest.from_response(
                response,
                formdata={"VehicleMake": make, "VehicleModel": ""},
                callback=self.parse_inventory,
            )

    def parse_inventory(self, response):
        def sel(nth):
            return f"descendant-or-self::td[{nth}]/text()"

        for row in response.css("table.table tr"):
            if row.css("th"):
                continue  # skip header row
            year = row.xpath(sel(1)).get()
            make = row.xpath(sel(2)).get()
            model = row.xpath(sel(3)).get()
            color = row.xpath(sel(4)).get()
            yard_row = row.xpath(sel(5)).get()
            arrival_date = datetime.strptime(row.xpath(sel(6)).get(), "%m/%d/%Y")
            stock_number = row.xpath(sel(7)).get()

            yield {
                "year": year,
                "make": make,
                "model": model,
                "color": color,
                "row": yard_row,
                "arrival_date": arrival_date,
                "stock_number": stock_number,
            }
