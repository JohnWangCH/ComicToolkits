import os
from utils import get_clean_sentences

min_words = 20
max_words = 40


def _combine_strings(strings):
    combined = []
    current_srt = ""
    for s in strings:
        if min_words <= len(current_srt + s) <= max_words:
            combined.append(current_srt + s + "\n")
            current_srt = ""
        elif len(current_srt) > max_words:
            combined.append(current_srt + "\n")
            current_srt = s
        else:
            current_srt += s
    if current_srt:
        combined.append(current_srt + "\n")
    return combined


def _split_2_line(text) -> list[str]:
    PUNCTUATION = ["，", "。", "！", "？", "；", "：", "”", "“", ",", "!", "…"]

    def clause():
        start = 0
        i = 0
        text_list = []
        while i < len(text):
            if text[i] in PUNCTUATION:
                try:
                    while text[i] in PUNCTUATION:
                        i += 1
                except IndexError:
                    pass
                text_list.append(get_clean_sentences(text[start:i].strip()))
                start = i
            i += 1
        return text_list

    text_list = clause()
    result = _combine_strings(text_list)
    return result


if __name__ == "__main__":
    file_path = "E:\小說推文\我有一尊煉妖壺"
    file_name = "chap_64106829_64132649"
    # 測試抓取章節的函數
    content_file_path = os.path.join(file_path, f"{file_name}.txt")

    scene_file_path = os.path.join(file_path, f"{file_name}_scene.txt")

    with open(content_file_path, "+r", encoding="utf_8_sig") as content_file:
        content = content_file.read()

    lines = _split_2_line(content)

    with open(scene_file_path, "w", encoding="utf_8_sig") as scene_file:
        scene_file.writelines(lines)
