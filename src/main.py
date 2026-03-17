import json
from time import sleep

from cloudscraper import CloudScraper

from .conf import CustomLogger, Logger
from .scraper import AvitoScraper
from .utilities import Categories, SearchTypes, ProxyTypes, CityLocationID


class CLI:
    logger: Logger = CustomLogger("CLI")._logger

    # Внутренние методы

    def __init__(self): ...

    def __choose_category(self) -> int:
        for index, type in enumerate(Categories):
            print(f"{index} --- {type.value.name}")

        types = list(Categories)
        choose = int(input("Выберите категорию из указанных выше: "))

        answer = input("Выбрать подкатегорию 0 Да/1 Нет: ")
        if answer != "0":
            return types[int(choose)].value.category_id

        subs = types[int(choose)].value.subs_list
        if not subs:
            print("Подкатегории отсутствуют")
            return types[int(choose)].value.category_id

        for index in range(len(subs)):
            print(f"{index} --- {subs[index].name}")

        subcategory = int(input("Выберите подкатегорию по номеру: "))
        return subs[subcategory].category_id

    def __choose_popular_cities(self):
        for index, type in enumerate(CityLocationID):
            print(f"{index} --- {type.name}")

        types = list(CityLocationID)
        choose = int(input("Выберите город из указанных выше: "))

        return types[int(choose)].value

    def __choose_city_url(self, cities: list[dict]) -> str:
        index: int = 0
        for city in cities:
            print(f"{index} --- {city.get('city_name')}     {city.get('region_name')}")
            index += 1

        choosen: int = int(input("Выберите город по номеру: "))

        return cities[choosen].get("city_id")

    def __choose_search_type(self):
        for index, type in enumerate(SearchTypes):
            print(f"{index} --- {type.name}")
        types = list(SearchTypes)
        choose = int(input("Выберите сортировку по номеру: "))

        return types[int(choose)].value

    def __choose_params(self, categoryId: int) -> list:
        url = f"https://www.avito.ru/web/1/js/items?categoryId={categoryId}"
        print("Доделать позже")

    # Входные точки

    def cookie_test(self, scraper: CloudScraper, avitoScraper: AvitoScraper):
        avitoScraper.headers_cookies_get_and_save(scraper)

    def item_parser(
        self,
        scraper: CloudScraper,
        avitoScraper: AvitoScraper,
        searchId: SearchTypes = SearchTypes.DEFAULT.value,
        page: int = 0,
    ):
        categoryId = self.__choose_category()

        choose = input(
            "\n0 - выбрать из 10 миллиоников\n1 - Найти город через авито\nПо умолчанию поиск через авито: "
        )
        if choose != "0":
            info: list[dict] = avitoScraper.get_city_id_multi(
                input("Введите название города: "), scraper
            )
            if not info:
                exit()
            locationId = self.__choose_city_url(info)

        else:
            locationId = self.__choose_popular_cities()

        if searchId == SearchTypes.DEFAULT.value:
            searchId = self.__choose_search_type()

        else:
            pass
        # params = self.choose_params()

        url = avitoScraper.create_url(
            categoryId=categoryId,
            locationId=locationId,
            searchId=searchId,
            page_number=page,
        )
        self.logger.info(url)
        avitoScraper.get_items(url, scraper, filename=f"output_{page}.json")
        self.logger.info(f"Файл output_{page}.json успешно создан")

    def item_enricher(
        self,
        scraper: CloudScraper,
        avitoScraper: AvitoScraper,
        filename: str = "output.json",
    ):
        with open(filename, "r", encoding="utf-8") as file:
            items: list[dict] = json.load(file)

        for item in items:
            avitoScraper.get_more_data(item.get("urlPath"), scraper)
            print("\nПерерыв перед следующим запросом")
            sleep(3)

    def proxy_manage(
        self,
        scraper: CloudScraper,
        avitoScraper: AvitoScraper,
    ):
        print(f"\nКакой тип прокси использовать?")
        avitoScraper.proxies_number_by_type()
        for index, type in enumerate(ProxyTypes):
            print(f"{index} --- {type.name}")

        types = list(ProxyTypes)
        choose = int(input("Выберите тип прокси из указанных выше: "))
        avitoScraper.set_proxy(scraper, proxy_type=types[int(choose)].value)


if __name__ == "__main__":
    try:
        avitoScraper = AvitoScraper()
        cli = CLI()
        scraper = avitoScraper.create_scraper(
            high_security=True
        )  # high_security = true Для улучшенного скрапера но для работы обязательно: `playwright install chromium`

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
                    cli.item_enricher(scraper, avitoScraper)

                elif choose == "2":
                    filtrated: bool = False
                    page: int = 0
                    while not filtrated:
                        cli.item_parser(
                            scraper,
                            avitoScraper,
                            searchId=SearchTypes.DATE.value,
                            page=page,
                        )
                        filtrated = avitoScraper.data_filter(
                            filename=f"output_{page}.json"
                        )
                        page += 1
                        sleep(3)

                elif choose == "9":
                    continue

            elif choose == "1":
                cli.proxy_manage(scraper, avitoScraper)

            elif choose == "2":
                cli.cookie_test(scraper, avitoScraper)

            else:
                print("\nВыберите корректное число.")
                continue

    except KeyboardInterrupt:
        print("\nВыход")
