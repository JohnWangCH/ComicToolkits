import os
import cloudscraper

import requests
from lxml import etree
import requests.adapters
import time
from enum import Enum

header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
}


RETRY_COUNT = 5


# Define the platform enum
class Platform(Enum):
    ZONGHENG = "zongheng"
    BIGEE = "bigee"
    QUANBEN = "quanben"
    UUKANSHU = "uukanshu"

    def get_chapter_content(self, book_id_or_name, chap_id):
        if self == Platform.ZONGHENG:
            return zongheng_get_chapter_content(
                book_id=book_id_or_name, chap_id=chap_id
            )
        elif self == Platform.BIGEE:
            return bigee_get_chapter_content(book_id=book_id_or_name, chap_id=chap_id)
        elif self == Platform.QUANBEN:
            return quanben_get_chapter_content(
                book_name=book_id_or_name, chap_id=chap_id
            )
        elif self == Platform.UUKANSHU:
            return uukanshu_get_chapter_content(
                book_id=book_id_or_name, chap_id=chap_id
            )
        else:
            raise ValueError("Unsupported platform.")


# Unified get_content function
def get_content(
    platform: Platform,
    book_id_or_name,
    start_chap_id,
    count,
):
    content = ""
    chap_id = start_chap_id

    while chap_id is not None and count > 0:
        chap_id, chapter_content = platform.get_chapter_content(
            book_id_or_name, chap_id
        )
        content += chapter_content
        count -= 1

    return content, len(content), chap_id


def _get_response(chapter_url: str, retry_count=RETRY_COUNT):
    print(f"HTTP request to {chapter_url}")
    for attempt in range(retry_count):  # Explicit retry loop
        try:
            # Perform the request with an increased timeout of 20 seconds
            response = requests.get(chapter_url, headers=header)
            if response.status_code != 200:
                raise Exception(
                    f"Failed to load the chapter: {chapter_url}: [{response.status_code}]"
                )

            # 解析 HTML
            return response

        except requests.exceptions.Timeout:
            print(
                f"[Error]Timeout occurred. Retrying... (Attempt {attempt + 1}/{RETRY_COUNT})"
            )
        except Exception as e:
            print(
                f"[Error] Fail to fetch the response: {e} (Attempt {attempt + 1}/{RETRY_COUNT})"
            )

        # Backoff between retries
        time.sleep(2)  # Sleep for 2 seconds before the next retry

    print(f"Failed to get response from {chapter_url}, have retied {RETRY_COUNT} times")
    raise Exception(f"Failed to get response from: {chapter_url}")


BIGEE_BASE_URL = "https://www.bigee.cc"


def bigee_download_whole_book(en):
    li = en.xpath('//div[@class = "listmain"]//dl//dd')
    index = 0
    bookLen = len(li)
    for i in li:
        # 创建新的url请求
        try:
            # 解析dd 这里为什么不需要书写etreed对象获取呢？
            # 因为li数组本身就是一个解析后的etree元素列表，
            # 所以i本身就是一个etree元素，可以直接使用xpath

            # 这里注意使用[0] xpath解析获取到的都是数组形式
            bookWeb = i.xpath("./a/@href")[0]
            newUrl = BIGEE_BASE_URL + bookWeb
            note = requests.get(newUrl)
            note.encoding = "utf-8"
            noteText = etree.HTML(note.text).xpath('//div[@id="chaptercontent"]/text()')
            for t in noteText:
                with open("小说.txt", "a", encoding="utf-8") as file:
                    file.write(t)
                    file.write("\n")
            print(f"书本下载({index}/{bookLen})")
            index += 1
        except:
            print("章节下载失败")


def bigee_get_chapter_content(book_id, chap_id):
    url = f"{BIGEE_BASE_URL}{book_id}"
    response = requests.get(url, headers=header)
    response.encoding = "utf-8"
    webCode = response.text
    en = etree.HTML(webCode)
    # Download one chapter
    li = en.xpath(f'//div[@class = "listmain"]/dl/dd[{chap_id}]/a//@href')

    # 创建新的url请求
    newUrl = f"{BIGEE_BASE_URL}/" + li[0]

    note = requests.get(newUrl, headers=header)
    note.encoding = "utf-8"

    noteText = etree.HTML(note.text).xpath('//div[@id="chaptercontent"]/text()')
    return "\n".join(noteText[:-2])  # skip "請收藏本站..."


def bigee_download_chapter_2_file(en, chap_no):
    # Download one chapter
    li = en.xpath(f'//div[@class = "listmain"]/dl/dd[{chap_no}]/a//@href')

    # 创建新的url请求
    newUrl = f"{BIGEE_BASE_URL}" + li[0]
    print(f"newUrl: {newUrl}")
    response = _get_response(newUrl)
    response.encoding = "utf-8"

    noteText = etree.HTML(response.text).xpath('//div[@id="chaptercontent"]/text()')

    for t in noteText:
        with open(f"novels/{chap_no}.txt", "a", encoding="utf-8") as file:
            print(t)
            file.write("\n")
    print("成功下载")


def zongheng_get_chapter_content(book_id, chap_id):
    """
    根據 book_id 和 chap_no 取得章節內容
    """
    chapter_url = f"https://read.zongheng.com/chapter/{book_id}/{chap_id}.html"
    response = _get_response(chapter_url=chapter_url)
    # 解析 HTML
    noteText = etree.HTML(response.text).xpath('//div[@class="content"]/p/text()')
    next_id = etree.HTML(response.text).xpath("//a[@data-nextcid]/@data-nextcid")[0]
    return next_id, "\n".join(noteText)


def quanben_get_chapter_content(book_name, chap_id):
    chapter_url = f"https://www.quanben.io/n/{book_name}/{chap_id}.html"
    response = _get_response(chapter_url=chapter_url)
    # 解析 HTML
    noteText = etree.HTML(response.text).xpath('//div[@id="content"]/p/text()')
    next_href = etree.HTML(response.text).xpath('//a[@rel="next"]/@href')
    if next_href:
        next_id = next_href[0].split("/")[-1].split(".")[0]
    else:
        next_id = None

    return next_id, "\n".join(noteText)


def uukanshu_get_chapter_content(book_id, chap_id):
    chapter_url = f"https://uukanshu.cc/book/{book_id}/{chap_id}.html"

    scraper = cloudscraper.create_scraper(
        browser={
            "browser": "chrome",
            "platform": "windows",
        },
    )
    response = scraper.get(chapter_url)
    # print(response.text)
    # response = _get_response(chapter_url=chapter_url)
    # 解析 HTML

    note_text = etree.HTML(response.text).xpath('//div[@class="readcotent"]//text()')
    next_href = etree.HTML(response.text).xpath('//a[@id="linkNext"]/@href')
    if next_href:
        next_id = next_href[0].split("/")[-1].split(".")[0]
    else:
        next_id = None

    print(note_text)
    print(next_id)

    return next_id, "\n".join(note_text)


if __name__ == "__main__":

    # 測試抓取章節的函數
    output_file_path = "E:\小說推文\25032"
    book_id = "25032"
    # book_name = "quanqiugaowu-wojuexingtianfu-dadaozhijian"
    chap_no = 1
    chap_id = "16025806"

    # book_id = "1257162"  # 替換為實際的 book_id
    # chap_no = "70696892"  # 替換為實際的 chap_no
    count = 1

    content, word_count, next_chap_id = get_content(
        platform=Platform.UUKANSHU,
        book_id_or_name=book_id,
        start_chap_id=chap_id,
        count=count,
    )

    # Write files
    # with open(
    #     os.path.join(output_file_path, f"{chap_no}_{chap_id}_{next_chap_id}.txt"),
    #     "w",
    #     encoding="utf_8_sig",
    # ) as text_file:
    #     text_file.write(content)

    print(f"total words: {word_count}")
