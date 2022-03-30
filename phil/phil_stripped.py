#!/usr/bin/env python3
from urllib.request import urlopen
from urllib.parse import quote, unquote
from urllib.error import URLError, HTTPError
import re


def get_content(name):
    """
    Функция возвращает содержимое вики-страницы name из русской Википедии.
    В случае ошибки загрузки или отсутствия страницы возвращается None.
    """
    try:
        with urlopen("http://ru.wikipedia.org/wiki/" + quote(name)) as page:
            return page.read().decode("utf-8", errors="ignore")
    except (URLError, HTTPError):
        return None


def extract_content(page):
    """
    Функция принимает на вход содержимое страницы и возвращает 2-элементный
    tuple, первый элемент которого — номер позиции, с которой начинается
    содержимое статьи, второй элемент — номер позиции, на котором заканчивается
    содержимое статьи.
    Если содержимое отсутствует, возвращается (0, 0).
    """
    start = re.search(r'<div id="mw-content-text"', page).start()
    finish = re.search(r'<div id="mw-navigation">', page).start()
    return (start, finish - 1) if (start != -1 and finish != -1) else None


def extract_links(page, begin, end):
    """
    Функция принимает на вход содержимое страницы и начало и конец интервала,
    задающего позицию содержимого статьи на странице и возвращает все имеющиеся
    ссылки на другие вики-страницы без повторений и с учётом регистра.
    """
    return set(map(unquote, re.findall(r"[\"']/wiki/([\w%]+?)[\"']",
                                       page[begin:end],
                                       re.IGNORECASE)))


def find_chain(start, finish):
    """
    Функция принимает на вход название начальной и конечной статьи и возвращает
    список переходов, позволяющий добраться из начальной статьи в конечную.
    Первым элементом результата должен быть start, последним — finish.
    Если построить переходы невозможно, возвращается None.
    """
    if start == finish:
        return [start]

    transitions = []
    name = start

    while finish not in transitions:
        page = get_content(name)
        if page is None:
            return None
        transitions.append(name)

        links = extract_links(page, *extract_content(page))
        if finish in links:
            return transitions + [finish]
        name = get_next_page_name(links, transitions)


def get_next_page_name(links: list, transitions: list) -> str:
    for link in links:
        if link not in transitions:
            return link


def main():
    pass


if __name__ == '__main__':
    main()
