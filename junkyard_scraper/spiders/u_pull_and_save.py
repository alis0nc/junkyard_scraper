import json
import logging
import requests
import scrapy


class UPullAndSaveSpider(scrapy.Spider):
    name = "u_pull_and_save"
    allowed_domains = ["www.u-pullandsave.com"]
    api_base_url = "https://api.u-pullandsave.com/vehicles"
    model_cache_filename = "u_pull_and_save_models.json"
    stores = [105, 110]

    def start_requests(self):
        # First, check for the cached all_models.json
        try:
            with open(self.model_cache_filename, "r") as model_cache:
                # do the requests
                self.log("Cache found, starting requests for makes and models", logging.INFO)
                all_models = json.load(model_cache)
                for make, models in all_models.items():
                    self.log(f"Searching all {make} models")
                    for model, model_info in models.items():
                        newest_valid_year = model_info["valid_years"][0]
                        for store_num in self.stores:
                            yield scrapy.Request(
                                url=f"https://www.u-pullandsave.com/used-car-parts?year={newest_valid_year}&make={make}&model={model}&store={store_num}&searchType=vehicle",
                                callback=self.parse,
                                cb_kwargs={
                                    "make": make,
                                    "model": model,
                                    "store": store_num,
                                },
                            )
        except FileNotFoundError:
            # generate the year/make/model cache
            self.generate_ymm_cache()

    def parse(self, response, make, model, store):
        not_found_text = response.css("table tbody tr td p::text").get()
        if not_found_text:
            not_found_text = not_found_text.strip()
            assert not_found_text[0:40] == "We don't have any in stock at this time."
            return

        def sel(nth):
            return f"descendant-or-self::td[{nth}]/text()"

        for row in response.css("table tbody tr"):
            detail_url = response.urljoin(row.css("td a::attr(href)").get())
            stock_number = row.css("td a::text").get().strip()
            parsed_year = row.xpath(sel(2)).get().strip()
            parsed_make = row.xpath(sel(3)).get().strip()
            parsed_model = row.xpath(sel(4)).get().strip()
            engine = row.xpath(sel(5)).get().strip()
            body_type = row.xpath(sel(6)).get().strip()
            color = row.xpath(sel(7)).get().strip()
            yard_row = row.xpath(sel(8)).get().strip()
            yield scrapy.Request(
                url=detail_url,
                callback=self.parse_detail,
                cb_kwargs={
                    "data_from_table": {
                        "stock_number": stock_number,
                        "year": parsed_year,
                        "make": make,
                        "model": parsed_model,
                        "engine": engine,
                        "body_type": body_type,
                        "color": color,
                        "row": yard_row,
                        "store": store,
                    }
                },
            )

    def parse_detail(self, response, data_from_table):
        def sel(dd):
            return f"//*/text()[normalize-space(.)='{dd}']/../../span[position()=2]/text()"

        assert data_from_table["stock_number"] == response.xpath(sel("Stock Number")).get().strip()
        assert data_from_table["row"] == response.xpath(sel("Row")).get().strip()
        mileage = response.xpath(sel("Mileage")).get().strip()
        body_style = response.xpath(sel("Body Style")).get().strip()
        trim_level = response.xpath(sel("Trim Level")).get().strip()
        vin = response.xpath(sel("VIN")).get().strip()
        status = response.xpath(sel("Status")).get().strip()
        location = response.xpath(sel("Location")).get().strip()
        detail_color = response.xpath(sel("Color")).get()
        detail_images = response.css("div.agile__slides--regular div img::attr(src)").getall()
        yield {
            **data_from_table,
            "odometer": mileage,
            "body_style": body_style,
            "trim_level": trim_level,
            "vin": vin,
            "status": status,
            "location": location,
            "detail_images": detail_images,
        }

    def generate_ymm_cache(self):
        self.log("Generating year/make/model cache", logging.INFO)
        all_models = {}
        years = [y["modelYear"] for y in requests.get(self.api_base_url + "/years").json()]
        for year in years:
            makes_for_year = [
                m["vehicleMake"] for m in requests.get(self.api_base_url + f"/make/{year}").json()
            ]
            for make in makes_for_year:
                if make not in all_models:
                    all_models[make] = {}
                models_for_make_and_year = {
                    m["hollanderModel"]: m
                    for m in requests.get(self.api_base_url + f"/model/{year}/{make}").json()
                }

                def add_valid_year(make, model_key, year):
                    if "valid_years" not in all_models[make][model_key]:
                        all_models[make][model_key]["valid_years"] = [year]
                    else:
                        all_models[make][model_key]["valid_years"].append(year)

                for model_key, model in models_for_make_and_year.items():
                    if model_key not in all_models[make]:
                        all_models[make][model_key] = model
                    add_valid_year(make, model_key, year)
        with open(self.model_cache_filename, "w") as model_cache:
            json.dump(all_models, model_cache)
