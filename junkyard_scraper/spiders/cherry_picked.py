import scrapy


class CherryPickedSpider(scrapy.Spider):
    name = "cherry_picked"
    allowed_domains = ["cherrypickedparts.com"]
    admin_url = "https://cherrypickedparts.com/wp-admin/admin-ajax.php"

    def start_requests(self):
        yield scrapy.FormRequest(
            url=self.admin_url,
            formdata={"action": "getMakes"},
            callback=self.parse_make,
        )

    def parse_make(self, response):
        all_makes = response.css("option span::text").getall()

        for make in all_makes:
            yield scrapy.FormRequest(
                url=self.admin_url,
                formdata={
                    "action": "getVehicles",
                    "makes": make,
                    "models": "0",
                    "years": "0",
                    "store": "0",
                    "beginDate": "",
                    "endDate": "",
                },
                callback=self.parse_inventory,
                cb_kwargs={"make": make},
            )

    def parse_inventory(self, response, make=None):
        def sel(nth):
            return f"descendant-or-self::td[{nth}]/text()"

        for row in response.css("table#vehicletable1 tbody tr"):
            year = row.xpath(sel(1)).get()
            model = row.xpath("descendant-or-self::td[2]/span/text()").get()
            arrival_date = row.xpath("descendant-or-self::td[3]/@data-value").get()
            yard_row = row.xpath(sel(4)).get()
            color = row.xpath(sel(5)).get()
            stock_number = row.xpath(sel(6)).get()
            odometer = None if row.xpath(sel(7)).get == "Unknown" else row.xpath(sel(7)).get()
            vin = row.xpath(sel(8)).get()

            yield {
                "year": year,
                "make": make,
                "model": model,
                "arrival_date": arrival_date,
                "row": yard_row,
                "color": color,
                "stock_number": stock_number,
                "odometer": odometer,
                "vin": vin,
            }
