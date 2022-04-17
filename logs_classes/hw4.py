#!/usr/bin/env python3
import re
import unittest
from typing import Union
from datetime import datetime, date
from collections import defaultdict
from abc import ABC, abstractmethod


class BaseStat(ABC):
    """Абстрактный класс статистики."""

    @abstractmethod
    def update(self):
        """Обновление статистики."""
        pass

    # @property
    @abstractmethod
    def value(self):
        """Получение значения статистики."""
        pass


class SlowestPageStat(BaseStat):
    def __init__(self):
        self._max_time = 0
        self._value = ""

    def update(self, time, page):
        if time >= self._max_time:
            self._value = page
            self._max_time = time

    def value(self):
        return self._value


class FastestPageStat(BaseStat):
    def __init__(self):
        self._min_time = 10**10
        self._value = ""

    def update(self, time, page):
        if time <= self._min_time:
            self._value = page
            self._min_time = time

    def value(self):
        return self._value


class SlowestAveragePageStat(BaseStat):
    def __init__(self):
        self._pages = defaultdict(Page)

    def update(self, time, page):
        self._pages[page].add_time(time)

    def value(self):
        return Page.max(self._pages) if self._pages else ""


class MostPopularPageStat(BaseStat):
    def __init__(self):
        self._pages = defaultdict(int)

    def update(self, page):
        self._pages[page] += 1

    def value(self):
        return lexicographic_min(self._pages)


class MostActiveСlientStat(BaseStat):
    def __init__(self):
        self._clients = defaultdict(int)

    def update(self, client):
        self._clients[client] += 1

    def value(self):
        return lexicographic_min(self._clients)


class MostPopularBrowserStat(BaseStat):
    def __init__(self):
        self._browsers = defaultdict(int)

    def update(self, browser):
        self._browsers[browser] += 1

    def value(self):
        return lexicographic_min(self._browsers)


class MostActiveСlientByDayStat(BaseStat):
    def __init__(self, date: datetime.date):
        self._date = date
        self._clients = defaultdict(int)

    def update(self, date, client):
        if self._date != date:
            return
        self._clients[client] += 1

    def value(self):
        return {self._date: lexicographic_min(self._clients)}


class Page():
    def __init__(self) -> None:
        self._total_time = 0
        self._count = 0
        self._avg_time = 0

    def add_time(self, time: int) -> None:
        """Добавляет время обработки новой страницы."""
        self._total_time += time
        self._count += 1
        self.calculate_avg_time()

    def calculate_avg_time(self) -> float:
        """Пересчитывает среднее время."""
        self._avg_time = self._total_time / self._count

    def avg_time(self) -> float:
        """Возвращет среднее время обработки."""
        return self._avg_time

    @staticmethod
    def max(pages: dict) -> str:
        """Возвращает имя страницы с максимальным средним временем
           обработки."""
        pages_avg_time = pages.values()
        pages_names = pages.keys()
        max_avg_time = max(pages_avg_time, key=lambda x: x.avg_time())
        for name in pages_names:
            if abs(pages[name].avg_time() - max_avg_time.avg_time()) < 0.1**10:
                return name


class Parser:
    """Класс парсера логов."""

    PATTERN = re.compile(
        r"(?P<IP>(\d{1,3}\.){3}\d{1,3})\s-\s-\s"
        r'\[(?P<date>.+)\]\s"(GET|PUT|POST|HEAD|OPTIONS|DELETE)\s'
        r'(?P<page>(\S+)).\S+" \d+ \d+ "\S+\s"'
        r'(?P<User_Agent>(.+))"(\s(?P<time>(\d+)))?'
    )

    @classmethod
    def parse(cls, line: str) -> Union[dict, None]:
        """Разбивает лог на элементы."""
        data = re.match(cls.PATTERN, line)
        if not data:
            return None
        return cls.type_conversion(data.groupdict())

    def type_conversion(group: dict) -> dict:
        """Приводит элементы лога к нужным типам."""
        group["date"] = datetime.strptime(
            group["date"], "%d/%b/%Y:%H:%M:%S %z").date()
        if group['time']:
            group["time"] = int(group["time"])
        return group


class Statistics:
    def __init__(self) -> None:
        self._fastest_page = FastestPageStat()
        self._slowest_page = SlowestPageStat()
        self._slowest_average_page = SlowestAveragePageStat()
        self._most_popular_page = MostPopularPageStat()
        self._most_active_client = MostActiveСlientStat()
        self._most_popular_browser = MostPopularBrowserStat()
        self._most_active_client_by_day = MostActiveСlientByDayStat(
            date(2012, 7, 8))

    def add_line(self, line: str) -> None:
        """Обрабатывает строку лога."""
        grouped_data = Parser.parse(line)
        if grouped_data:
            self.update(grouped_data)

    def update(self, group: dict) -> None:
        """Обновляет статистику."""
        if group['time']:
            self._fastest_page.update(group["time"], group["page"])
            self._slowest_page.update(group["time"], group["page"])
            self._slowest_average_page.update(group["time"], group["page"])

        self._most_popular_page.update(group["page"])
        self._most_active_client.update(group["IP"])
        self._most_popular_browser.update(group["User_Agent"])
        self._most_active_client_by_day.update(group["date"], group["IP"])

    def results(self) -> dict:
        """Возвращает итоговую статистику."""
        return {
            "FastestPage": self._fastest_page.value(),
            "MostActiveClient": self._most_active_client.value(),
            "MostActiveClientByDay": self._most_active_client_by_day.value(),
            "MostPopularBrowser": self._most_popular_browser.value(),
            "MostPopularPage": self._most_popular_page.value(),
            "SlowestAveragePage": self._slowest_average_page.value(),
            "SlowestPage": self._slowest_page.value(),
        }


def lexicographic_min(data: dict):
    """Возращает лексикографически наименьший ключ словаря
       с макимальным значением."""
    if not data:
        return ""
    max_value = max(data.values())
    for key in sorted(data.keys()):
        if data[key] == max_value:
            return key


def make_stat() -> Statistics:
    """Возвращает класс статистики."""
    return Statistics()


class LogStatTests(unittest.TestCase):
    def test_logs_without_time(self):
        test_method = make_stat()
        test_method.add_line(
            '192.168.74.82 - - [08/Jul/2012:06:31:57 +0600]'
            ' "GET /style-menu-top.css HTTP/1.1" 304 211'
            ' "http://callider/menu-top.php" "Mozilla/5.0 (compatible; MSIE'
            ' 9.0; Windows NT 6.1; WOW64; Trident/5.0)"'
        )

        test_method.add_line(
            '192.168.74.83 - - [08/Jul/2012:06:31:57 +0600]'
            ' "GET /img/graph.png HTTP/1.1" 304 211'
            ' "http://callider/menu-top.php" "Mozilla/5.0 (compatible; MSIE'
            ' 9.0; Windows NT 6.1; WOW64; Trident/5.0)"'
        )

        test_method.add_line(
            '192.168.74.82 - - [09/Jul/2012:06:31:57 +0600]'
            ' "GET /img/graph.png HTTP/1.1" 304 211'
            ' "http://callider/menu-top.php" "Mozilla/5.0 (compatible; MSIE'
            ' 9.0; Windows NT 6.1; WOW64; Trident/5.0)"'
        )

        expected = {
            'FastestPage': '',
            'MostActiveClient': '192.168.74.82',
            'MostActiveClientByDay': {date(2012, 7, 8): '192.168.74.82'},
            'MostPopularBrowser': 'Mozilla/5.0 (compatible; MSIE'
                                  ' 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
            'MostPopularPage': '/img/graph.png',
            'SlowestAveragePage': '',
            'SlowestPage': ''}

        self.assertDictEqual(test_method.results(), expected)

    def test_incorrect_logs(self):
        test_method = make_stat()
        test_method.add_line(
            '192.fdfdfdfdfdfdfdfdf'
            ' "fdfledfdfdffdfdfdfdfdf/1.1" 304 211'
            ' "http://callider/mefdfdfdfdfdfible; MSIE'
            ' 9.0; Winfdfdfdfdfdf5.0)"'
        )

        test_method.add_line(
            '192.168.74.83 - - [08/Jul/2012:06:31:57 +0600]'
            ' "GET /img/graph.png HTTP/1.1" 304 211'
            ' "http://callider/menu-top.php" "Mozilla/5.0 (compatible; MSIE'
            ' 9.0; Windows NT 6.1; WOW64; Trident/5.0)" 123'
        )

        test_method.add_line(
            '192.168.74.82 - - [09/Jul/2012:06:31:57 +0600]'
            ' "GET /img/r.png HTTP/1.1" 304 211'
            ' "http://callider/menu-top.php" "Mozilla/5.0 (compatible; MSIE'
            ' 9.0; Windows NT 6.1; WOW64; Trident/5.0)" 321'
        )

        expected = {
            'FastestPage': '/img/graph.png',
            'MostActiveClient': '192.168.74.82',
            'MostActiveClientByDay': {date(2012, 7, 8): '192.168.74.83'},
            'MostPopularBrowser': 'Mozilla/5.0 (compatible; MSIE'
                                  ' 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
            'MostPopularPage': '/img/graph.png',
            'SlowestAveragePage': '/img/r.png',
            'SlowestPage': '/img/r.png'}

        self.assertDictEqual(test_method.results(), expected)

    def test_lexicographic_order(self):
        test_method = make_stat()
        test_method.add_line(
            '192.168.74.82 - - [08/Jul/2012:06:31:57 +0600]'
            ' "GET /vfdh.css HTTP/1.1" 304 211'
            ' "http://callider/menu-top.php" "Mozilla/5.0 (compatible; MSIE'
            ' 9.0; Windows NT 6.1; WOW64; Trident/5.0)"'
        )

        test_method.add_line(
            '192.168.74.80 - - [08/Jul/2012:06:31:57 +0600]'
            ' "GET /bca.png HTTP/1.1" 304 211'
            ' "http://callider/menu-top.php" "Mozilla/5.0 (compatible; MSIE'
            ' 9.0; Windows NT 6.1; WOW64; Trident/5.0)" 123'
        )

        test_method.add_line(
            '192.168.74.83 - - [09/Jul/2012:06:31:57 +0600]'
            ' "GET /abc.png HTTP/1.1" 304 211'
            ' "http://callider/menu-top.php" "Mozilla/5.0 (compatible; MSIE'
            ' 9.0; Windows NT 6.1; WOW64; Trident/5.0)" 321'
        )

        actual = test_method.results()

        self.assertEqual(actual["MostPopularPage"], "/abc.png")
        self.assertEqual(actual["MostActiveClient"], "192.168.74.80")

    def test_empty_logs(self):
        test_method = make_stat()

        expected = {
            'FastestPage': '',
            'MostActiveClient': '',
            'MostActiveClientByDay': {date(2012, 7, 8): ''},
            'MostPopularBrowser': '',
            'MostPopularPage': '',
            'SlowestAveragePage': '',
            'SlowestPage': ''}

        self.assertDictEqual(test_method.results(), expected)


if __name__ == '__main__':
    unittest.main()
