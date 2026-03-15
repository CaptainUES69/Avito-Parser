from dataclasses import dataclass

from .conf import CustomLogger, Logger


@dataclass
class Subcategory:
    id: int
    name: str
    category_id: int
    params: dict[int, int]


@dataclass
class Category:
    id: int
    name: str
    category_id: int
    subs_list: list[Subcategory]


class Utilities:
    logger: Logger = CustomLogger("utility")._logger

    transport: Category
    realEstate: Category
    job: Category
    services: Category
    personal: Category
    home: Category
    parts: Category
    electronics: Category
    hobby: Category
    animals: Category
    business: Category

    categoryByName: dict[str, Category]
    searchFilters: dict[str, int]
    popularCities: dict[str, int]

    def __init__(self):
        self.transport = Category(
            id=25984,
            name="Транспорт",
            category_id=1,
            subs_list=[
                Subcategory(25985, "Автомобили", 9, {}),
                Subcategory(25986, "Мотоциклы и мототехника", 14, {}),
                Subcategory(26025, "Грузовики и спецтехника", 81, {}),
                Subcategory(26040, "Водный транспорт", 11, {}),
                Subcategory(25999, "Запчасти и аксессуары", 10, {}),
            ],
        )

        self.realEstate = Category(
            id=26113,
            name="Недвижимость",
            category_id=4,
            subs_list=[
                Subcategory(35451, "Купить жильё", 24, {201: 1059}),
                Subcategory(35452, "Путешествия", 24, {201: 1060, 504: 5257}),
                Subcategory(35453, "Снять долгосрочно", 24, {201: 1060, 504: 5256}),
                Subcategory(35454, "Коммерческая недвижимость", 42, {}),
                Subcategory(35455, "Земельные участки", 26, {}),
            ],
        )

        self.job = Category(
            id=26400,
            name="Работа",
            category_id=110,
            subs_list=[
                Subcategory(26427, "Ищу работу", 111, {}),
                Subcategory(26401, "Ищу сотрудника", 112, {}),
            ],
        )

        self.services = Category(id=26486, name="Услуги", category_id=114, subs_list=[])

        self.personal = Category(
            id=26127,
            name="Личные вещи",
            category_id=5,
            subs_list=[
                Subcategory(148043, "Как на праздник", 27, {156912: 3295178}),
                Subcategory(148044, "Деловой стиль", 27, {156912: 3295179}),
                Subcategory(148045, "Жизнь в движении", 27, {156912: 3295180}),
                Subcategory(148046, "Время отдохнуть", 27, {156912: 3295181}),
                Subcategory(148047, "Винтажные образы", 27, {156912: 3295182}),
                Subcategory(26128, "Одежда, обувь, аксессуары", 27, {}),
                Subcategory(26153, "Детская одежда и обувь", 29, {}),
                Subcategory(26173, "Товары для детей и игрушки", 30, {}),
                Subcategory(26187, "Красота и здоровье", 88, {}),
                Subcategory(26183, "Часы и украшения", 28, {}),
            ],
        )

        self.home = Category(
            id=26047,
            name="Для дома и дачи",
            category_id=2,
            subs_list=[
                Subcategory(26088, "Ремонт и строительство", 19, {}),
                Subcategory(26073, "Мебель и интерьер", 20, {}),
                Subcategory(26048, "Бытовая техника", 21, {}),
                Subcategory(26087, "Продукты питания", 82, {}),
                Subcategory(26097, "Растения", 106, {}),
                Subcategory(26084, "Посуда и товары для кухни", 87, {}),
            ],
        )

        self.parts = Category(
            id=30757,
            name="Запчасти и аксессуары",
            category_id=10,
            subs_list=[
                Subcategory(30773, "Запчасти", 10, {5: 18}),
                Subcategory(30774, "Шины, диски и колёса", 10, {5: 19}),
                Subcategory(30775, "Аудио- и видеотехника", 10, {5: 20}),
                Subcategory(30776, "Аксессуары", 10, {5: 4943}),
                Subcategory(30778, "Багажники и фаркопы", 10, {5: 4964}),
                Subcategory(30779, "Инструменты", 10, {5: 4963}),
                Subcategory(30780, "Прицепы", 10, {5: 4965}),
                Subcategory(30781, "Экипировка", 10, {5: 6416}),
                Subcategory(30782, "Масла и автохимия", 10, {5: 4942}),
                Subcategory(30783, "Противоугонные устройства", 10, {5: 4944}),
                Subcategory(30784, "GPS-навигаторы", 10, {5: 21}),
            ],
        )

        self.electronics = Category(
            id=26195,
            name="Электроника",
            category_id=6,
            subs_list=[
                Subcategory(26249, "Телефоны", 84, {}),
                Subcategory(26196, "Аудио и видео", 32, {}),
                Subcategory(26292, "Товары для компьютера", 101, {}),
                Subcategory(26216, "Игры, приставки и программы", 97, {}),
                Subcategory(26222, "Ноутбуки", 98, {}),
                Subcategory(26221, "Настольные компьютеры", 31, {}),
                Subcategory(26209, "Фототехника", 105, {}),
                Subcategory(26236, "Планшеты и электронные книги", 96, {}),
                Subcategory(26223, "Оргтехника и расходники", 99, {}),
            ],
        )

        self.hobby = Category(
            id=26315,
            name="Хобби и отдых",
            category_id=7,
            subs_list=[
                Subcategory(26316, "Билеты и путешествия", 33, {}),
                Subcategory(26339, "Велосипеды", 34, {}),
                Subcategory(26345, "Книги и журналы", 83, {}),
                Subcategory(26349, "Коллекционирование", 36, {}),
                Subcategory(26373, "Музыкальные инструменты", 38, {}),
                Subcategory(26324, "Охота и рыбалка", 102, {}),
                Subcategory(26325, "Спорт и отдых", 39, {}),
            ],
        )

        self.animals = Category(
            id=26098,
            name="Животные",
            category_id=35,
            subs_list=[
                Subcategory(26099, "Собаки", 89, {}),
                Subcategory(26100, "Кошки", 90, {}),
                Subcategory(26101, "Птицы", 91, {}),
                Subcategory(26102, "Аквариум", 92, {}),
                Subcategory(26103, "Другие животные", 93, {}),
                Subcategory(26112, "Товары для животных", 94, {}),
            ],
        )

        self.business = Category(
            id=26382,
            name="Бизнес и оборудование",
            category_id=8,
            subs_list=[
                Subcategory(26393, "Оборудование для бизнеса", 40, {}),
                Subcategory(82435, "Франшизы", 116, {820: 3267940}),
                Subcategory(26383, "Готовый бизнес", 116, {}),
                Subcategory(117602, "ПО для бизнеса", 116, {820: 3295065}),
            ],
        )

        self.categoryByName = {
            "Транспорт": self.transport,
            "Недвижимость": self.realEstate,
            "Работа": self.job,
            "Услуги": self.services,
            "Личные вещи": self.personal,
            "Для дома и дачи": self.home,
            "Запчасти и аксессуары": self.parts,
            "Электроника": self.electronics,
            "Хобби и отдых": self.hobby,
            "Животные": self.animals,
            "Готовый бизнес и оборудование": self.business,
        }

        self.searchFilters = {
            "По умолчанию": 101,
            "Дешевле": 1,
            "Дороже": 2,
            "По дате": 104,
        }

        self.popularCities = {
            "Москва": 637640,
            "Санкт-Петербург": 653240,
            "Новосибирск": 641780,
            "Екатеринбург": 654070,
            "Казань": 650400,
            "Нижний Новгород": 640860,
            "Челябинск": 661420,
            "Красноярск": 635320,
            "Самара": 653040,
            "Уфа": 646600,
        }
