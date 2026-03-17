import json
import os
import pickle
import re
from datetime import datetime
from typing import Any, Dict, List, Union
from urllib import parse

from cloudscraper import CloudScraper, create_high_security_scraper, create_scraper
from fake_useragent import UserAgent

from .conf import CustomLogger, Logger
from .utilities import Categories, ProxyTypes, SearchTypes, CityLocationID


class AllFields:
    """Специальный класс, обозначающий, что нужно оставить все поля."""

    pass


class AvitoScraper:
    logger: Logger = CustomLogger("scrapper")._logger
    base_url: str = "https://www.avito.ru"
    cookie_file: str
    ALL_FIELDS = AllFields()

    # Внутренние методы

    def __init__(self, cookie_file_name: str = "avito_cookies.pkl"):
        self.cookie_file = cookie_file_name

    def __choose_numbers(
        self, keys: List[str], prompt: str = "Введите номера полей: "
    ) -> List[str]:
        while True:
            choice_input = input(prompt).strip()
            if not choice_input:
                print("Вы ничего не ввели. Попробуйте снова.")
                continue

            selected_indices = set()
            parts = choice_input.replace(" ", "").split(",")
            valid = True
            for part in parts:
                if "-" in part:
                    try:
                        start, end = map(int, part.split("-"))
                        if start < 1 or end > len(keys) or start > end:
                            print(f"Некорректный диапазон: {part}")
                            valid = False
                            break
                        selected_indices.update(range(start, end + 1))

                    except ValueError:
                        print(f"Некорректный диапазон: {part}")
                        valid = False
                        break

                else:
                    try:
                        num = int(part)
                        if 1 <= num <= len(keys):
                            selected_indices.add(num)
                        else:
                            print(
                                f"Число {num} вне допустимого диапазона (1-{len(keys)})"
                            )
                            valid = False
                            break

                    except ValueError:
                        print(f"Некорректное число: {part}")
                        valid = False
                        break

            if valid and selected_indices:
                return [keys[i - 1] for i in sorted(selected_indices)]
            print("Попробуйте ещё раз.")

    def __choose_fields(
        self, sample: Any, indent: int = 0, path: str = ""
    ) -> Union[AllFields, Dict]:
        prefix = "  " * indent
        if isinstance(sample, dict):
            keys = list(sample.keys())
            print(f"\n{prefix}Ключ '{path}' (словарь). Доступные поля:")
            self.__print_keys_with_index(keys, indent)
            answer = (
                input(f"{prefix}Хотите выбрать поля из этого словаря 0 Да/1 Нет: ")
                .strip()
                .lower()
            )
            if answer != "0":
                return self.ALL_FIELDS

            selected_keys = self.__choose_numbers(
                keys, f"{prefix}Введите номера полей: "
            )
            selector = {}
            for key in selected_keys:
                sub_sample = sample.get(key)
                if sub_sample is not None and (
                    isinstance(sub_sample, dict)
                    or (
                        isinstance(sub_sample, list)
                        and sub_sample
                        and isinstance(sub_sample[0], dict)
                    )
                ):
                    sub_selector = self.__choose_fields(
                        sub_sample, indent + 1, path + "." + key if path else key
                    )
                    selector[key] = sub_selector
                else:
                    selector[key] = self.ALL_FIELDS

            return selector

        elif isinstance(sample, list) and sample and isinstance(sample[0], dict):
            print(
                f"\n{prefix}Ключ '{path}' (список словарей). Выбор полей для элементов списка:"
            )
            element_selector = self.__choose_fields(sample[0], indent + 1, path + "[]")
            return element_selector

        else:
            return self.ALL_FIELDS

    def __apply_selector(self, value: Any, selector: Union[AllFields, Dict]) -> Any:
        if isinstance(selector, AllFields):
            return value

        if isinstance(value, dict) and isinstance(selector, dict):
            result = {}
            for key, sub_selector in selector.items():
                if key in value:
                    result[key] = self.__apply_selector(value[key], sub_selector)
            return result

        if isinstance(value, list) and value and isinstance(value[0], dict):
            return [self.__apply_selector(item, selector) for item in value]
        return value

    def __filter_items(
        self, items: List[Dict], top_selectors: Dict[str, Union[AllFields, Dict]]
    ) -> List[Dict]:
        result = []
        for item in items:
            new_item = {}
            for key, selector in top_selectors.items():
                if key in item:
                    new_item[key] = self.__apply_selector(item[key], selector)
            result.append(new_item)
        return result

    def __print_keys_with_index(self, keys: List[str], indent: int = 0) -> None:
        prefix = "  " * indent
        for idx, key in enumerate(keys, 1):
            print(f"{prefix}{idx}. {key}")

    def __get_sample_for_key(self, items: List[Dict], key: str) -> Any:
        for item in items:
            val = item.get(key)
            if val is not None and (
                isinstance(val, dict)
                or (isinstance(val, list) and val and isinstance(val[0], dict))
            ):
                return val
        return None

    # Методы для работы с прокси

    def __load_proxies(self, filename: str) -> Dict | None:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            return

    def __test_proxies(self, scraper: CloudScraper) -> bool:
        if not self.proxies:
            print("Прокси не настроены.")
            return False

        try:
            response = scraper.get("https://httpbin.org/ip", timeout=10)
            if response.status_code != 200:
                print(f"Прокси не работает, статус: {response.status_code}")
                return False

            ip = response.json().get("origin")
            print(f"Прокси работает. Ваш внешний IP: {ip}")

            response = scraper.get(self.base_url, timeout=20)
            if response.status_code != 200:
                print(
                    f"Прокси не работает для авито, статус: {response.status_code}\n(429 ошибка вероятно ошибка настроек scraper а не прокси)"
                )
                return False
            print("Прокси прошел проверку основной страницей")
            return True

        except Exception as e:
            print(f"Ошибка при тестировании прокси: {e}")
            return False

    def proxies_number_by_type(self, filename: str = "proxy_file.json"):
        data: dict[str, list[int]] = self.__load_proxies(filename)
        for proxies in data.keys():
            print(f"Кол-во прокси с протоколом {proxies}: {len(data.get(proxies))}")

    def set_proxy(
        self,
        scraper: CloudScraper,
        filename: str = "proxy_file.json",
        proxy_type: ProxyTypes = ProxyTypes.HTTPS.value,
    ) -> bool:
        proxies: dict[str, list[str]] = self.__load_proxies(filename)
        if not proxies:
            print("Прокси не найдены")
            return False

        for proxy in proxies.get(proxy_type):
            scraper.proxies = f"{proxy_type}://{proxy}"
            result = self.__test_proxies(scraper)
            if result:
                return True
        print("Прокси не прошли проверку")
        return False

    # Методы для работы с куки файлами и заголовками

    def __save_cookies(self, scraper: CloudScraper):
        with open(self.cookie_file, "wb") as f:
            pickle.dump(scraper.cookies.get_dict(), f)

    def __load_cookies(self, scraper: CloudScraper):
        if os.path.exists(self.cookie_file):
            with open(self.cookie_file, "rb") as f:
                cookies = pickle.load(f)
                scraper.cookies.update(cookies)

    def __load_user_agents(self, filename: str = "User-Agent.json") -> list[str]:
        if not os.path.exists(filename):
            return []

        try:
            with open(filename, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

        if not isinstance(data, dict):
            return []
        user_agents = data.get("UserAgent")

        if isinstance(user_agents, list):
            return [str(ua) for ua in user_agents if isinstance(ua, str)]

        if isinstance(user_agents, str):
            return [user_agents]

        return []

    def __save_user_agents(self, ua: str, filename: str = "User-Agent.json"):
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as file:
                    data = json.load(file)
            except (json.JSONDecodeError, FileNotFoundError):
                data = {}
        else:
            data = {}

        if not isinstance(data, dict):
            data = {}

        user_agents = data.get("UserAgent")
        if not isinstance(user_agents, list):
            if isinstance(user_agents, str):
                user_agents = [user_agents]
            else:
                user_agents = []

        if ua not in user_agents:
            user_agents.append(ua)

        data["UserAgent"] = user_agents
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def headers_cookies_get_and_save(self, scraper: CloudScraper):
        response = scraper.get(self.base_url)
        if response.status_code != 200:
            print(
                f"Куки не получены, заголовки не прошли, ошибка: {response.reason} {response.status_code}\nВозможно стоит подождать или изменить настройки скрапера"
            )
            return None

        print("Запрос успешен, сохраняем куки и заголовки")
        self.__save_cookies(scraper)
        self.__save_user_agents(scraper.headers.get('User-Agent'))

    # Запросы и скрапер

    def create_scraper(
        self,
        delay: int = 15,
        stealth_min: float = 3.0,
        stealth_max: float = 6.0,
        high_security: bool = False,
        user_agent_num: int = 0,
    ) -> CloudScraper:
        if high_security:
            scraper = create_high_security_scraper(
                delay=delay,
                browser="chrome",
                debug=False,  # Отладка
                enable_stealth=True,
                stealth_options={
                    "min_delay": stealth_min,
                    "max_delay": stealth_max,
                    "human_like_delays": True,
                    "randomize_headers": True,
                    "browser_quirks": True,
                },
            )

        else:
            scraper = create_scraper(
                interpreter="hybrid",  # js2py nodejs, hybrid но нужен playwright
                delay=delay,
                browser="chrome",
                debug=False,  # Отладка
                enable_stealth=True,
                stealth_options={
                    "min_delay": stealth_min,
                    "max_delay": stealth_max,
                    "human_like_delays": True,
                    "randomize_headers": True,
                    "browser_quirks": True,
                },
            )

        ua = self.__load_user_agents()[user_agent_num]
        if not ua:
            user_agent = UserAgent()
            ua = user_agent.random
        scraper.headers.update({
            "User-Agent": ua,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": f"{self.base_url}/",
            "Origin": self.base_url,
            "DNT": "1",
        })
        self.logger.info(
            f"\nUser-Agent: {ua}\nscraper interpreter: {scraper.interpreter=}"
        )
        self.__load_cookies(scraper)
        return scraper

    def get_city_id_multi(self, city_name: str, scraper: CloudScraper) -> List[Dict]:
        encoded_city = parse.quote(city_name)
        url = "https://www.avito.ru/web/1/slocations?q=" + encoded_city

        response = scraper.get(url, timeout=15)
        if response.status_code != 200:
            self.logger.error(
                f"{response.status_code} {response.reason}\n{response.headers}"
            )
            print(
                f"{response.status_code=} {response.reason}, исправьте настройки cloudscraper или используемые прокси"
            )
            return []
        self.logger.info(f"status code: {response.status_code}\n{response.headers}")
        self.__save_cookies(scraper)

        data = response.json()
        locations = data.get("result", {}).get("locations", [])

        cities_list = []
        for loc in locations:
            if "parent" in loc:
                city_id = loc["id"]
                city_name_found = loc.get("names", {}).get("1")
                region_id = loc["parent"].get("id")
                region_name = loc["parent"].get("names", {}).get("1")
                cities_list.append(
                    {
                        "city_id": city_id,
                        "city_name": city_name_found,
                        "region_id": region_id,
                        "region_name": region_name,
                    }
                )

            elif "from" in loc:
                from_data = loc["from"]
                city_name_found = from_data.get("name")
                region_name = loc.get("names", {}).get("1")
                city_id = loc["id"]
                cities_list.append(
                    {
                        "city_id": city_id,
                        "city_name": city_name_found,
                        "region_id": None,
                        "region_name": region_name,
                    }
                )

        if not cities_list:
            self.logger.info(f'Города по запросу "{city_name}" не найдены')
            print(f'Города по запросу "{city_name}" не найдены')
        return cities_list

    def get_items(self, url: str, scraper: CloudScraper, filename: str = "output.json"):
        response = scraper.get(url, timeout=20)
        if response.status_code != 200:
            self.logger.error(
                f"{response.status_code} {response.reason}\n{response.headers}"
            )
            print(
                f"{response.status_code=} {response.reason}, исправьте настройки cloudscraper или используемые прокси"
            )
            return
        print("Данные получены успешно")
        self.logger.info(f"status code: {response.status_code}\n{response.headers}")
        self.__save_cookies(scraper)

        data: dict = response.json()
        items: dict[dict] = data.get("catalog").get("items")

        if not items:
            self.logger.error(data.get("catalog"))
            print("Нет товаров для обработки. Завершение.")
            return

        ordered_keys = []
        seen = set()
        for item in items:
            for key in item.keys():
                if key not in seen:
                    seen.add(key)
                    ordered_keys.append(key)

        print(f"\nНайдено товаров: {len(items)}")
        print(f"Всего различных полей верхнего уровня: {len(ordered_keys)}")
        self.__print_keys_with_index(ordered_keys)

        top_selected = self.__choose_numbers(
            ordered_keys,
            "Введите номера полей верхнего уровня для сохранения\nПример 5-6, 11-12, 15, 24: ",
        )
        print(f"\nВыбраны поля верхнего уровня: {', '.join(top_selected)}")

        top_selectors = {}
        for key in top_selected:
            sample = self.__get_sample_for_key(items, key)
            if sample is not None:
                print(f"\n--- Настройка для ключа '{key}' ---")
                selector = self.__choose_fields(sample, indent=0, path=key)
                top_selectors[key] = selector

            else:
                top_selectors[key] = self.ALL_FIELDS

        filtered_items = self.__filter_items(items, top_selectors)

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(filtered_items, f, ensure_ascii=False, indent=2)
        print(f"\nСохранено {len(filtered_items)} записей в файл {filename}")

    def get_more_data(
        self, url: str, scraper: CloudScraper, filename: str = "output.json"
    ):
        response = scraper.get(self.base_url + url, timeout=20)
        if response.status_code != 200:
            self.logger.error(
                f"\n{self.base_url + url=}\n{response.status_code} {response.reason}\n{response.headers}"
            )
            print(
                f"{response.status_code=} {response.reason}, не получилось обратиться к странице."
            )
            choose = input("Продолжить? 0 Да/1 Нет: ")
            if choose != "0":
                exit()
            return

        pattern = r'window\.__staticRouterHydrationData\s*=\s*JSON\.parse\(\s*"((?:\\"|[^"])*)"\s*\);'
        match = re.search(pattern, response.text, re.DOTALL)
        if not match:
            return

        json_string = json.loads('"' + match.group(1) + '"')
        data: dict = json.loads(json_string)

        try:
            info: list[dict[str, int | str]] = (
                data.get("loaderData")
                .get("catalog-or-main-or-item")
                .get("buyerItem")
                .get("ga")
            )

        except (KeyError, TypeError, AttributeError) as e:
            self.logger.warning(f"Ошибка извлечения ga для {url}: {e}", exc_info=True)
            print(
                "Не удалось извлечь данные (возможно, объявление закрыто или удалено)"
            )
            return

        record = {"url": url, "ga": info}

        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)

            except json.JSONDecodeError:
                existing_data = []

        else:
            existing_data = []

        if not isinstance(existing_data, list):
            existing_data = []

        existing_data.append(record)

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)

        print(f"Данные для {url} добавлены в файл {filename}")

    def create_url(
        self,
        categoryId: Categories,
        locationId: CityLocationID,
        radiusNumber: int | str = 0,
        searchId: SearchTypes = SearchTypes.DEFAULT.value,
        page_number: int = 0,
        params: list[str] = [],
        localPriority: int = 0,
    ) -> str:
        query_list: list[str] = [
            f"categoryId={categoryId}",
            f"locationId={locationId}",
            f"radius={radiusNumber}",
            f"s={searchId}",
            f"p={page_number}",
            f"localPriority={localPriority}",
        ]

        resultUrl = f"https://www.avito.ru/web/1/js/items?" + "&".join(query_list)
        return resultUrl

    def data_filter(
        self, filename: str = "output.json", time_interval: int = 172800
    ) -> bool:
        with open(filename, "r", encoding="utf-8") as file:
            data: list[dict] = json.load(file)
        if not data:
            return False

        items: list = []
        for item in data:
            order_time: int = item.get("allowTimeStamp")
            current_time = int(datetime.now().timestamp() * 1000)
            if (current_time - order_time) > time_interval:
                continue

            items.append(item)

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

        if len(data) < len(items):
            print(
                f"\nПри отсеве данных были удалены лишние записи ({len(items)}) позже указанного временного промежутка."
            )
            return True
        print(f"\nВсе объявления ({len(items)}) подпадают под временной промежуток")
        return False
