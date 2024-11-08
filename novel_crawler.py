import os

import requests
from lxml import etree

BASE_NOVEL_URL = "https://www.bigee.cc"
novelStyes = ["xuanhuan", "wuxia", "dushi", "wangyou"]

header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}


def download_whole_bool(en):
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
            newUrl = BASE_NOVEL_URL + bookWeb
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


def get_hot_novels(style_index: int) -> dict:
    url = f"{BASE_NOVEL_URL}/{novelStyes[style_index]}"
    response = requests.get(url, headers=header)
    response.encoding = "utf-8"
    webCode = response.text
    novel_names = etree.HTML(webCode).xpath("//div[@class='hot']//dl/dt/a/text()")
    novel_urls = etree.HTML(webCode).xpath("//div[@class='hot']//dl/dt/a/@href")
    return dict(zip(novel_names, novel_urls))


def download_chapter(book_url, chap_no, base_url=BASE_NOVEL_URL):

    url = f"{base_url}{book_url}"
    response = requests.get(url, headers=header)
    response.encoding = "utf-8"
    webCode = response.text
    en = etree.HTML(webCode)
    # Download one chapter
    li = en.xpath(f'//div[@class = "listmain"]/dl/dd[{chap_no}]/a//@href')

    # 创建新的url请求
    newUrl = f"{base_url}/" + li[0]

    note = requests.get(newUrl, headers=header)
    note.encoding = "utf-8"

    noteText = etree.HTML(note.text).xpath('//div[@id="chaptercontent"]/text()')
    return "\n".join(noteText[:-2])  # skip "請收藏本站..."


def download_chapter_2_file(en, chap_no):
    # Download one chapter
    li = en.xpath(f'//div[@class = "listmain"]/dl/dd[{chap_no}]/a//@href')

    # 创建新的url请求
    newUrl = f"{BASE_NOVEL_URL}" + li[0]
    print(f"newUrl: {newUrl}")

    note = requests.get(newUrl, headers=header)
    note.encoding = "utf-8"

    noteText = etree.HTML(note.text).xpath('//div[@id="chaptercontent"]/text()')

    for t in noteText:
        with open(f"novels/{chap_no}.txt", "a", encoding="utf-8") as file:
            print(t)
            file.write("\n")
    print("成功下载")


# 定義小說內容頁與章節 URL 模板
zongheng_novel_detail_url_template = "https://www.zongheng.com/detail/{book_id}"
zongheng_chapter_url_template = (
    "https://read.zongheng.com/chapter/{book_id}/{chap_no}.html"
)


def zongheng_get_content(book_id, start_chap_no, count):
    content = ""
    chap_no = start_chap_no
    while chap_no is not None and count > 0:
        chap_no, chapter_content = zongheng_get_chapter_content(book_id, chap_no)
        content += chapter_content
        count = count - 1
    return content, content.__len__(), chap_no


def zongheng_get_chapter_content(book_id, chap_no):
    """
    根據 book_id 和 chap_no 取得章節內容
    """
    # novel_detail_url_template = "https://www.zongheng.com/detail/{book_id}"
    chapter_url_template = "https://read.zongheng.com/chapter/{book_id}/{chap_no}.html"
    chapter_url = chapter_url_template.format(book_id=book_id, chap_no=chap_no)

    # 發送請求獲取章節網頁
    response = requests.get(chapter_url)

    if response.status_code != 200:
        raise Exception(f"Failed to load the chapter: {chapter_url}")

    # 解析 HTML
    noteText = etree.HTML(response.text).xpath('//div[@class="content"]/p/text()')
    next_id = etree.HTML(response.text).xpath("//a[@data-nextcid]/@data-nextcid")[0]
    return next_id, "\n".join(noteText)


if __name__ == "__main__":

    # 測試抓取章節的函數
    book_id = "1091501"  # 替換為實際的 book_id
    chap_no = "64091898"  # 替換為實際的 chap_no
    count = 5

    output_file_path = "E:\小說推文\我有一尊煉妖壺"
    content, word_count, next_chap_no = zongheng_get_content(
        book_id=book_id, start_chap_no=chap_no, count=count
    )

    # Write files
    with open(
        os.path.join(output_file_path, f"chap_{chap_no}_{next_chap_no}.txt"),
        "w",
        encoding="utf_8_sig",
    ) as text_file:
        text_file.write(content)

    print(f"total words: {word_count}")
