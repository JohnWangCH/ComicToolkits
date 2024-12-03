import asyncio
import os
from novel_crawler import get_content, Platform
from voice_caption_helper import create_caption_and_voice_files
from datetime import datetime
from video_helper import generate_video
import re


def text_file_exist(text_dir: str, chap_no: int, chap_id):
    filename_re = rf"{chap_no}_{chap_id}_(\d+)"
    for filename in os.listdir(text_dir):
        if re.search(filename_re, filename):
            return True
    return False


def get_next_chap_id(text_dir: str, chap_no: int, chap_id):
    filename_re = rf"{chap_no}_{chap_id}_(\d+)"
    for filename in os.listdir(text_dir):
        match = re.search(filename_re, filename)
        if match:
            return int(match.group(1))

    return None


if __name__ == "__main__":
    book_name = "quanqiugaowu-wojuexingtianfu-dadaozhijian"
    chap_no = 6
    chap_id = "6"
    dir_name = "大道至簡"
    total_count = 50
    base = 5

    voice_folder_path = rf"C:\voice_and_srt\{dir_name}"
    text_dir_path = f"E:\小說推文\{dir_name}"
    text_file_names = []
    start_time = datetime.now()

    if not os.path.exists(voice_folder_path):
        os.mkdir(voice_folder_path)
    if not os.path.exists(text_dir_path):
        os.mkdir(text_dir_path)

    while total_count != 0:
        count = base if total_count >= base else total_count
        print(f"----Crawl chap_{chap_no} content----")
        if not text_file_exist(
            text_dir=text_dir_path, chap_no=chap_no, chap_id=chap_id
        ):
            content, word_count, next_chap_id = get_content(
                platform=Platform.QUANBEN,
                book_id_or_name=book_name,
                start_chap_id=chap_id,
                count=base,
            )
            content_file_path = os.path.join(
                text_dir_path, f"{chap_no}_{chap_id}_{next_chap_id}.txt"
            )
            with open(
                content_file_path,
                "w",
                encoding="utf_8_sig",
            ) as text_file:
                text_file.write(content)
        else:
            next_chap_id = get_next_chap_id(
                text_dir=text_dir_path, chap_no=chap_no, chap_id=chap_id
            )
            print(f"    #chap_{chap_no} content exists, skip")

        text_file_names.append(f"{chap_no}_{chap_id}_{next_chap_id}.txt")

        print(f"----#chap_{chap_no} content Done----")
        total_count -= count
        chap_no += count
        if next_chap_id is None:
            print("No next chap")
            break
        else:
            chap_id = next_chap_id

    current_time = datetime.now()
    step1_time_diff = current_time - start_time
    start_time = current_time

    srt_file_paths = []
    audio_file_paths = []
    for file_name in text_file_names:
        # match = re.match(r"(\d+)_", file_name)
        # index = int(match.group(1))
        content_file_path = os.path.join(text_dir_path, file_name)

        with open(content_file_path, "+r", encoding="utf_8_sig") as content_file:
            content = "\n".join(content_file.readlines())

        audio_file_path = os.path.join(
            voice_folder_path, f"{file_name.replace('.txt','.mp3')}"
        )
        srt_file_path = os.path.join(
            voice_folder_path, f"{file_name.replace('.txt','.srt')}"
        )
        audio_file_paths.append(audio_file_path)
        srt_file_paths.append(srt_file_path)

        if not os.path.exists(audio_file_path) or not os.path.exists(srt_file_path):
            print(f"----Create voice file for #{file_name}----")
            asyncio.run(
                create_caption_and_voice_files(
                    content=content,
                    audio_file_path=audio_file_path,
                    srt_file_path=srt_file_path,
                )
            )
            print(f"----Voice file for #{file_name} created-----")

    current_time = datetime.now()
    step2_time_diff = current_time - start_time
    start_time = current_time

    imgs_path = r"E:\mjpics\剪映图片-大道至簡\%06d.png"
    video_dir_path = rf"C:\videos\{dir_name}"

    asyncio.run(
        generate_video(
            image_path=imgs_path,
            name=dir_name,
            video_dir_path=video_dir_path,
            audio_dir_path=voice_folder_path,
            audio_file_paths=audio_file_paths,
            srt_file_paths=srt_file_paths,
        )
    )

    step3_time_diff = datetime.now() - start_time
    time_diff = step1_time_diff + step2_time_diff + step3_time_diff
    print(f"(crawl novel) Seconds elapsed: {step1_time_diff.total_seconds()} seconds")
    print(
        f"(generate voice files) Seconds elapsed: {step2_time_diff.total_seconds()} seconds"
    )
    print(
        f"(generate video) Seconds elapsed: {step3_time_diff.total_seconds()} seconds"
    )
    print(f"Total Seconds elapsed: {time_diff}")
