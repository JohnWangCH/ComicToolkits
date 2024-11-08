import os
import re

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


def remove_punctuation(text):
    # temp_text = re.sub(r'(\.|\?|!|,|;|:|")\1+', r"\1", text)
    punctuations_to_replace = "，。！？；!,…"
    # Avoids consecutive redundant punctuations
    temp_text = re.sub(f"([{punctuations_to_replace}]){{2,}}", r"\1", text)
    # Replace them with ','
    temp_text = re.sub(f"[{punctuations_to_replace}]", ",", temp_text)

    punctuations_to_remove = "：“”"
    # Removes others punctuation
    cleaned_text = re.sub(f"[{punctuations_to_remove}]", "", temp_text)

    return cleaned_text


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
                text_list.append(remove_punctuation(text[start:i].strip()))
                start = i
            i += 1
        return text_list

    text_list = clause()
    result = _combine_strings(text_list)
    return result


if __name__ == "__main__":

    # 測試抓取章節的函數
    content_file_path = os.path.join(
        "E:\小說推文\我有一尊煉妖壺", "chap_64091898_64106829.txt"
    )

    scene_file_path = os.path.join(
        "E:\小說推文\我有一尊煉妖壺", "chap_64091898_64106829_scene.txt"
    )

    with open(content_file_path, "+r", encoding="utf_8_sig") as content_file:
        content = content_file.read()

    lines = _split_2_line(content)

    with open(scene_file_path, "w", encoding="utf_8_sig") as scene_file:
        scene_file.writelines(lines)
