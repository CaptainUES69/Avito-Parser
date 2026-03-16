import json
from time import sleep

from cloudscraper import CloudScraper

from .conf import CustomLogger
from .scraper import AvitoScraper
from .utilities import Utilities


class CLI:
    utility: Utilities

    def __init__(self):
        self.utility = Utilities()

    def choose_popular_cities(
        self,
    ):
        cities = list(self.utility.popularCities.keys())
        for index in range(len(cities)):
            print(f"{index} --- {cities[index]}")
        city = int(input("Выберите категорию по номеру: "))

        return self.utility.popularCities.get(cities[city])

    def choose_city_url(self, cities: list[dict]) -> str:
        index: int = 0
        for city in cities:
            print(f"{index} --- {city.get('city_name')}     {city.get('region_name')}")
            index += 1

        choosen: int = int(input("Выберите город по номеру: "))

        return cities[choosen].get("city_id")

    def choose_category(
        self,
    ) -> int:
        keys = list(self.utility.categoryByName.keys())
        for index in range(len(keys)):
            print(f"{index} --- {keys[index]}")
        category = int(input("Выберите категорию по номеру: "))

        answer = input("Выбрать подкатегорию 0 да/1 нет: ")
        if answer.lower() != "0":
            return self.utility.categoryByName.get(keys[category]).category_id

        subs = self.utility.categoryByName.get(keys[category]).subs_list
        if not subs:
            print("Подкатегории отсутствуют")
            return self.utility.categoryByName.get(keys[category]).category_id
        for index in range(len(subs)):
            print(f"{index} --- {subs[index].name}")

        subcategory = int(input("Выберите подкатегорию по номеру: "))
        return self.utility.categoryByName.get(keys[subcategory]).category_id

    def choose_search_type(
        self,
    ):
        keys = list(self.utility.searchFilters.keys())
        for index in range(len(keys)):
            print(f"{index} --- {keys[index]}")
        filter = int(input("Выберите сортировку по номеру: "))

        return self.utility.searchFilters.get(keys[filter])

    def choose_params(self, categoryId: int) -> list:
        url = f"https://www.avito.ru/web/1/js/items?categoryId={categoryId}"
        print("Доделать позже")

    def cookie_test(self, scraper: CloudScraper, avitoScraper: AvitoScraper):
        avitoScraper.get_and_save_cookies(scraper)

    def item_parser(
        self,
        scraper: CloudScraper,
        avitoScraper: AvitoScraper,
        searchId: int = 101,
        page: int = 0,
    ):
        categoryId = self.choose_category()

        choose = input(
            "\n0 - выбрать из 10 миллиоников\n1 - Найти город через авито\nПо умолчанию поиск через авито: "
        )
        if choose != "0":
            info: list[dict] = avitoScraper.get_city_id_multi(
                input("Введите название города: "), scraper
            )
            if not info:
                exit()
            locationId = self.choose_city_url(info)

        else:
            locationId = self.choose_popular_cities()

        if searchId == 101:
            searchId = self.choose_search_type()

        else:
            pass
        # params = self.choose_params()

        url = avitoScraper.create_url(
            categoryId=categoryId,
            locationId=locationId,
            searchId=searchId,
            page_number=page,
        )
        avitoScraper.get_items(url, scraper, filename=f"output_{page}.json")

    def item_enricher(
        self, url: str, scraper: CloudScraper, avitoScraper: AvitoScraper
    ):
        avitoScraper.get_more_data(url, scraper)



if __name__ == "__main__":
    try:
        utility = Utilities()
        avitoScraper = AvitoScraper()
        cli = CLI()
        scraper = avitoScraper.create_scraper(
            high_security=False
        )  # high_security = true Для улучшенного скрапера но ддля работы обязательно: `playwright install chromium`

        while True:
            choose = input(
                "\n0 --- Парсинг данных\n1 --- Настройки прокси\n2 --- Тест на доступность url\n\nВыберите опцию из указанных выше: "
            )
            if choose == "0":
                choose = input(
                    "\n0 --- Основной режим\n1 --- Дополнение напрямую через объявления\n2 --- Сбор данных с отсевом по дате\n9 --- Возврат\n\nВыберите опцию из указанных выше: "
                )
                if choose == "0":
                    cli.item_parser(scraper, avitoScraper)

                elif choose == "1":
                    with open("output.json", "r", encoding="utf-8") as file:
                        items: list[dict] = json.load(file)

                    for item in items:
                        cli.item_enricher(item.get("urlPath"), scraper, avitoScraper)
                        print("\nПерерыв перед следующим запросом")
                        sleep(3)

                elif choose == "2":
                    filtrated: bool = False
                    page: int = 0
                    while not filtrated:
                        cli.item_parser(
                            scraper,
                            avitoScraper,
                            searchId=utility.searchFilters.get("По дате"),
                            page=page,
                        )
                        filtrated = avitoScraper.data_filter(filename=f'output_{page}.json')
                        page += 1
                        sleep(3)

                elif choose == "9":
                    continue

            elif choose == "1":
                print("\nВ разработке...")

            elif choose == "2":
                cli.cookie_test(scraper, avitoScraper)

            else:
                print("\nВыберите корректное число.")
                continue

    except KeyboardInterrupt:
        print("\nВыход")
