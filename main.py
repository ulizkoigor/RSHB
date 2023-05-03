import requests
from bs4 import BeautifulSoup
from datetime import timedelta, datetime
import csv
import time
from selenium.webdriver.common.by import By
import re
import undetected_chromedriver
from fuzzywuzzy import fuzz
from calendar import monthrange
from lxml import etree

YEAR_PERIOD = 2023
MONTH_PERIOD = 4
DATE_START_PERIOD = datetime(YEAR_PERIOD, MONTH_PERIOD, 1, 00, 00, 00)
DATE_END_PERIOD = datetime(YEAR_PERIOD, MONTH_PERIOD, monthrange(YEAR_PERIOD, MONTH_PERIOD)[1], 23, 59, 59)


def parse_pg13():
    press_releases = []
    number_page = 0
    while True:
        number_page += 1
        print(f'https://pg13.ru/tags/aboutfinance/?page={number_page}')
        html = requests.get(f'https://pg13.ru/tags/aboutfinance/?page={number_page}')
        soup = BeautifulSoup(html.text, 'html.parser')
        web_elements = soup.find_all('a', class_=re.compile('news-line_newsLink'))
        for web_element in web_elements:
            link = f'https://pg13.ru{web_element.get("href")}'
            html = requests.get(link)
            soup = BeautifulSoup(html.text, 'html.parser')
            date_string_format = soup.find('span', itemprop='datePublished').get('content').replace(
                ' (Moscow Standard Time)', '')
            title = soup.find('h1', itemprop="headline").text
            date = datetime.strptime(date_string_format, '%a %b %d %Y %H:%M:%S %Z%z').replace(tzinfo=None)
            if date > DATE_END_PERIOD:
                continue
            if date < DATE_START_PERIOD:
                break
            press_releases.append({
                'date': date,
                'title': title,
                'link': link,
            })
            number_press_release = press_releases.index(press_releases[-1]) + 1
            print(f'{number_press_release:2} {date} {title} {link}')
        else:
            continue
        break
    return press_releases


def parse_saransk_news():
    press_releases = []
    site_sections = {"politics", "economy", "society", "sport", "incident", "culture", "other"}
    for site_section in site_sections:
        number_page = 0
        while True:
            number_page = number_page + 1
            print(
                f'http://saransk-news.net/{site_section}/2023/4/p/{number_page}')
            html = etree.HTML(requests.get(
                f'http://saransk-news.net/{site_section}/2023/4/p/{number_page}').text)
            web_elements = html.xpath('//div[@class="post"]')
            if len(web_elements) == 0:
                break
            for web_element in web_elements:
                title = web_element.xpath('.//div[@class="post_title"]/a/text()')[0]
                if pg13_includes(title):
                    link = web_element.xpath('.//div[@class="post_title"]/a/@href')[0]
                    html = etree.HTML(requests.get(link).text)
                    date_string_format = html.xpath('.//meta[@itemprop="dateModified"]/@content')[0]
                    date = datetime.strptime(date_string_format, '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=None)
                    press_releases.append({
                        'date': date,
                        'title': title,
                        'link': link,
                    })
                    number = press_releases.index(press_releases[-1]) + 1
                    print(f'{number} {date} {title} {link}')
    return {
        'site_name': 'Информационный портал "Новости Саранска" (saransk-news.net)',
        'press_releases': press_releases
    }


def parse_mordovmedia():
    press_releases = []
    sections = {"business", "culture", "medicine", "science", "society",
                "politics", "crime", "russia", "saransk",
                "agriculture", "sports", "transport", "economics"}
    for section in sections:
        page = 0
        while True:
            page = page + 1
            print(f'https://www.mordovmedia.ru/news/{section}/?p={page}')
            html = etree.HTML(requests.get(
                f'https://www.mordovmedia.ru/news/{section}/?p={page}').text)
            web_elements = html.xpath('//div[@class="news-content"]')
            for web_element in web_elements:
                if web_element.xpath('.//div[@class="wrapper"]'):
                    web_element = web_element.xpath('.//div[@class="wrapper"]')[0]
                title = web_element.xpath('.//h3/a/text()')[0]
                link = web_element.xpath('.//h3/a/@href')[0]
                date_string_format = web_element.xpath('.//meta[@itemprop="datePublished "]/@content')[0]
                date = datetime.strptime(date_string_format, '%Y-%m-%dT%H:%M:%S')
                if date > DATE_END_PERIOD:
                    continue
                if date < DATE_START_PERIOD:
                    break
                if pg13_includes(title):
                    press_releases.append({
                        'date': date,
                        'title': title,
                        'link': link
                    })
                    number = press_releases.index(press_releases[-1]) + 1
                    print(f'{number:2} {date} {title} {link}')
                    continue
                if re.search(r'[Рр][Сс][Хх][Бб]|[Рр]оссельхозбанк', title):
                    mordovmedia_additional_releases.append({
                        'date': date,
                        'title': title,
                        'link': link
                    })
            else:
                continue
            break
    return {
        'site_name': 'Информационный портал "Мордовмедиа" (MordovMedia.ru)',
        'press_releases': press_releases
    }


def parse_stolica_s():
    press_releases = []
    site_sections = {
                        'name': f'archives/date/{YEAR_PERIOD}',
                        'class': 'archive-item'
                    }, {
                        'name': 'partners',
                        'class': 'item-list'
                    }
    for site_section in site_sections:
        number_page = 0
        while True:
            number_page = number_page + 1
            print(f'https://stolica-s.su/{site_section.get("name")}/page/{number_page}')
            html = etree.HTML(requests.get(f'https://stolica-s.su/{site_section.get("name")}/page/{number_page}').text)
            web_elements = html.xpath(f'//div[contains(@class, "{site_section.get("class")}")]')
            for web_element in web_elements:
                date_string_format = web_element.xpath('.//time/@datetime')[0]
                date = datetime.strptime(date_string_format, '%Y-%m-%dT%H:%M:%S%z').replace(
                    tzinfo=None)
                if date > DATE_END_PERIOD:
                    continue
                if date < DATE_START_PERIOD:
                    break
                title = web_element.xpath('.//a/text()')[0]
                if pg13_includes(title):
                    link = web_element.xpath('.//a/@href')[0]
                    press_releases.append({
                        'date': date,
                        'title': title,
                        'link': link,
                    })
                    number = press_releases.index(press_releases[-1]) + 1
                    print(f'{number:2} {date} {title} {link}')
            else:
                continue
            break
    return {
        'site_name': 'Информационный портал "Столица С" (stolica-s.su)',
        'press_releases': press_releases
    }


def parse_izvmor():
    releases = []
    sections = {"novosti-partnerov", "novosti/obshchestvo", "novosti/kultura", "novosti/sport",
                "novosti/nauka-i-obrazovanie", "novosti/ekonomika", "novosti/proisshestviya",
                "novosti/kriminal", "biznes", "novosti/politika", "stati/banki-i-finansy"}
    for section in sections:
        print(f"https://izvmor.ru/category/{section}/")
        driver.get(f"https://izvmor.ru/category/{section}/")
        time.sleep(3)
        while True:
            xpath_query = "//div[@class='td-module-meta-info td-module-meta-info-bottom']"
            web_elements = driver.find_elements(By.XPATH, xpath_query)
            date_string_format = web_elements[-1].find_element(By.TAG_NAME, 'time').get_attribute('datetime')
            date_last_press_release = datetime.strptime(date_string_format, '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=None)
            if date_last_press_release > DATE_START_PERIOD:
                driver.find_element(By.CLASS_NAME, 'td-load-more-wrap').click()
                time.sleep(3)
                continue
            else:
                break
        for web_element in web_elements:
            date_string_format = web_element.find_element(By.TAG_NAME, 'time').get_attribute('datetime')
            date = datetime.strptime(date_string_format, '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=None)
            if date > DATE_END_PERIOD:
                continue
            if date < DATE_START_PERIOD:
                break
            title = web_element.find_element(By.TAG_NAME, 'h3').text
            link = web_element.find_element(By.TAG_NAME, 'a').get_attribute('href')
            if pg13_includes(title):
                releases.append({
                    'date': date,
                    'title': title,
                    'link': link
                })
                number = releases.index(releases[-1]) + 1
                print(f'{number:2} {date} {title} {link}')
    return {
        'site_name': 'Информационный портал "Известия Мордовии" (izvmor.ru)',
        'press_releases': releases
    }


def parse_info_rm():
    press_releases = []
    driver.get("https://www.info-rm.com/")
    time.sleep(3)
    site_sections = {"societyru", "incidentru", "ekonomikaru", "cultureru", "sportru"}
    for site_section in site_sections:
        number_page = 0
        while True:
            number_page += 1
            print(f"https://www.info-rm.com/{site_section}/?PAGEN_1={number_page}&SIZEN_1=20")
            driver.get(f"https://www.info-rm.com/{site_section}/?PAGEN_1={number_page}&SIZEN_1=20")
            time.sleep(1)
            html = etree.HTML(driver.page_source)
            web_elements = html.xpath('//div[@class="news-item"]')
            for web_element in web_elements:
                title = web_element.xpath('.//a[@class="title"]/text()')[0]
                link = web_element.xpath('.//a[@class="title"]/@href')[0]
                date_string_format = web_element.xpath('.//div[@class="news-date-time" or @class="date"]/text()')[0]
                date = corrector_date(date_string_format)
                if date > DATE_END_PERIOD:
                    continue
                if date < DATE_START_PERIOD:
                    break
                if pg13_includes(title):
                    press_releases.append({
                        'date': date,
                        'title': title,
                        'link': f'https://www.info-rm.com/{link}',
                    })
                    number = press_releases.index(press_releases[-1]) + 1
                    print(f'{number:2} {date} {title} https://www.info-rm.com/{link}')
            else:
                continue
            break
    return {
        'site_name': 'Информационный портал "Мордовия. Саранск. Новости. Самые оперативные" (info-rm.com)',
        'press_releases': press_releases
    }


def parse_saransk_bez_formata():
    press_releases = []
    driver.get("https://saransk.bezformata.com/daynews/")
    time.sleep(3)
    days_in_month = monthrange(YEAR_PERIOD, MONTH_PERIOD)[1]
    for day in range(1, days_in_month):
        number_page = 0
        while True:
            number_page += 1
            print(
                f"https://saransk.bezformata.com/daynews/?npage={number_page}&nday={day}&nmonth={MONTH_PERIOD}&nyear={YEAR_PERIOD}")
            driver.get(
                f"https://saransk.bezformata.com/daynews/?npage={number_page}&nday={day}&nmonth={MONTH_PERIOD}&nyear={YEAR_PERIOD}")
            time.sleep(1)
            html = etree.HTML(driver.page_source)
            web_elements = html.xpath('//article[@class="listtopicline"]')
            if len(web_elements) == 0:
                break
            for web_element in web_elements:
                title = web_element.xpath('.//h3[@itemprop="headline"]/text()')[0]
                link = web_element.xpath('.//a[@itemprop="url"]/@href')[0]
                date_string_format = web_element.xpath('.//meta[@itemprop="datePublished"]/@content')[0]
                date = datetime.strptime(date_string_format, '%Y-%m-%d')
                if pg13_includes(title):
                    press_releases.append({
                        'date': date,
                        'title': title,
                        'link': link,
                    })
                    number = press_releases.index(press_releases[-1]) + 1
                    print(f'{number:2} {date} {title} {link}')
    return {
        'site_name': 'Информационный портал "Саранск без формата" (saransk.bezformata.com)',
        'press_releases': press_releases
    }


def corrector_date(date_rus_format_string):
    pattern = '%d %B %Y, %H:%M'
    group1 = date_rus_format_string.split(',')
    if len(group1[0].split(' ')) == 2:
        group1[0] = f'{group1[0]} {YEAR_PERIOD}'
    date_rus_format_string = ','.join(group1)
    regex_find_month_rus = '[Яя][Нн][Вв][Аа][Рр][Яя]|[Фф][Ее][Вв][Рр][Аа][Лл][Яя]|[Мм][Аа][Рр][Тт][Аа]|[Аа][Пп][Рр][Ее][Лл][Яя]|[Мм][Аа][Яя]|[Ии][Юю][Нн][Яя]|[Ии][Юю][Лл][Яя]|[Аа][Вв][Гг][Уу][Сс][Тт][Аа]|[Сс][Ее][Нн][Тт][Яя][Бб][Рр][Яя]|[Оо][Кк][Тт][Яя][Бб][Рр][Яя]|[Нн][Оо][Яя][Бб][Рр][Яя]|[Дд][Ее][Кк][Аа][Бб][Рр][Яя]'
    list_of_month = {'января': 'January', 'февраля': 'February', 'марта': 'March', 'апреля': 'April', 'мая': 'May',
                     'июня': 'June', 'июля': 'July',
                     'августа': 'August', 'сентября': 'September', 'октября': 'October', 'ноября': 'November',
                     'декабря': 'December'}
    month_rus = re.search(rf'{regex_find_month_rus}', date_rus_format_string).group(0)
    month_eng = list_of_month[month_rus.lower()]
    date_eng_format_string = date_rus_format_string.replace(month_rus, month_eng)
    date_eng_format_object = datetime.strptime(date_eng_format_string, pattern)
    return date_eng_format_object


def pg13_includes(title):
    for pg13_press_release in pg13_press_releases:
        if fuzz.UQRatio(pg13_press_release.get('title'), title) >= 75:
            return True
    return False


def create_table():
    pg13_press_releases.reverse()
    with open('press_releases.csv', 'w', newline='') as file:
        writer = csv.writer(file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
        for press_release_pg13 in pg13_press_releases:
            writer.writerow([press_release_pg13['title'], 'Информационный портал "PRO Город. Саранск" (pg13.ru)',
                             press_release_pg13['link'], press_release_pg13['date'], '100'])
            for news_site in parsed_sites:
                for press_release in news_site.get('press_releases'):
                    ratio_press_release = fuzz.UQRatio(press_release_pg13['title'], press_release['title'])
                    if ratio_press_release >= 75:
                        writer.writerow([press_release['title'], news_site.get('site'), press_release['link'],
                                         press_release['date'], ratio_press_release])
                        break
                else:
                    writer.writerow([press_release_pg13['title'], news_site.get('site_name')])
        writer.writerow('')
        for press_release_more_mordovmedia in mordovmedia_additional_releases:
            writer.writerow(
                [press_release_more_mordovmedia['title'], 'Информационный портал "Мордовмедиа" (MordovMedia.ru)',
                 press_release_more_mordovmedia['link'],
                 press_release_more_mordovmedia['date'],
                 '100'])
        writer.writerow('')


def create_table_for_production():
    with open('press_releases_revers.csv', 'w', newline='') as file:
        writer = csv.writer(file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
        for press_release_pg13 in pg13_press_releases:
            writer.writerow(
                [press_release_pg13['title'], '', '', '', 'Информационный портал "PRO Город. Саранск" (pg13.ru)',
                 press_release_pg13['link']])
            for news_site in parsed_sites:
                for press_release in news_site.get('press_releases'):
                    ratio_press_release = fuzz.UQRatio(press_release_pg13['title'], press_release['title'])
                    if ratio_press_release >= 75:
                        writer.writerow(
                            [press_release['title'], '', '', '', news_site.get('site'), press_release['link']])
                        break
                else:
                    writer.writerow([press_release_pg13['title'], '', '', '', news_site.get('site_name')])
        writer.writerow('')
        for press_release_more_mordovmedia in mordovmedia_additional_releases:
            writer.writerow(
                [press_release_more_mordovmedia['title'], '', '', '',
                 'Информационный портал "Мордовмедиа" (MordovMedia.ru)',
                 press_release_more_mordovmedia['link']])
        writer.writerow('')


def check_words_rshb_or_rosselhozbank(title_press_release):
    if re.search(r'[Рр][Сс][Хх][Бб]|[Рр]оссельхозбанк', title_press_release):
        return True
    else:
        return False


if __name__ == '__main__':
    parsed_sites = []
    mordovmedia_additional_releases = []

    pg13_press_releases = parse_pg13()

    # parsed_sites.append(parse_saransk_news())
    # parsed_sites.append(parse_mordovmedia())
    # parsed_sites.append(parse_stolica_s())

    driver = undetected_chromedriver.Chrome()

    parsed_sites.append(parse_izvmor())
    parsed_sites.append(parse_info_rm())
    parsed_sites.append(parse_saransk_bez_formata())

    create_table()
    create_table_for_production()

    driver.quit()
