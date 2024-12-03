import os.path
import re
from time import localtime, strftime
import asyncio
import aiofiles
import edge_tts
from utils import remove_punctuations
from edge_tts.submaker import mktimestamp
from xml.sax.saxutils import escape

limit = "18"
role = "zh-CN-YunxiNeural"
rate = "+30%"
volume = "+100%"


class CustomSubMaker(edge_tts.SubMaker):
    """重写此方法更好的支持中文"""

    def formatter(self, start_time: float, end_time: float, subdata: str) -> str:
        """
        formatter returns the timecode and the text of the subtitle.
        """
        # print(f"{start_time} to {mktimestamp(start_time)}")
        # print(print(f"{end_time} to {mktimestamp(end_time)}"))
        return (
            f"{mktimestamp(start_time)} --> {mktimestamp(end_time)}\n"
            f"{escape(subdata)}\r\n"
        )

    async def generate_cn_subs(self, text):

        PUNCTUATION = ["，", "。", "！", "？", "；", "：", "”", ",", "!"]

        def clause(self):
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
                    text_list.append(text[start:i])
                    start = i
                i += 1
            return text_list

        self.text_list = clause(self)
        if len(self.subs) != len(self.offset):
            raise ValueError("subs and offset are not of the same length")
        data = "WEBVTT\r\n\r\n"
        j = 0
        for text in self.text_list:
            try:
                start_time = self.offset[j][0]
            except IndexError:
                return data
            try:
                while self.subs[j + 1] in text:
                    j += 1
            except IndexError:
                pass

            # text = await self.remove_non_chinese_chars(text)
            text = remove_punctuations(text)
            data += self.formatter(start_time, self.offset[j][1], text)
            j += 1
        return data

    async def remove_non_chinese_chars(self, text):
        # 使用正则表达式匹配非中文字符和非数字
        pattern = re.compile(r"[^\u4e00-\u9fff0-9]+")
        # 使用空字符串替换匹配到的非中文字符和非数字
        cleaned_text = re.sub(pattern, "", text)
        return cleaned_text


async def create_caption_and_voice_files(
    content,
    audio_file_path,
    srt_file_path,
    voice_actor=role,
    rate=rate,
    volume=volume,
) -> None:
    """Create and update caption (.srt file) and voice (.mp3) for a content"""
    vtt_file_path = "temp.vtt"

    communicate = edge_tts.Communicate(
        text=content, voice=voice_actor, rate=rate, volume=volume
    )
    sub_maker = CustomSubMaker()

    async with aiofiles.open(audio_file_path, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                await file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                sub_maker.create_sub(
                    (chunk["offset"], chunk["duration"]),
                    chunk["text"],
                )

    async with aiofiles.open(vtt_file_path, "w", encoding="utf-8") as file:
        content_to_write = await sub_maker.generate_cn_subs(content)
        await file.write(content_to_write)

    # vtt -》 srt
    idx = 1  # 字幕序号
    with open(srt_file_path, "w", encoding="utf-8") as f_out:
        for line in open(vtt_file_path, encoding="utf-8"):
            if "-->" in line:
                f_out.write("%d\n" % idx)
                idx += 1
                line = line.replace(".", ",")  # 这行不是必须的，srt也能识别'.'
            if idx > 1:  # 跳过header部分
                f_out.write(line)

        # os.remove(vtt_file_path)


if __name__ == "__main__":
    content_file_path = r"E:\小說推文\大道至簡\short.txt"
    with open(content_file_path, "+r", encoding="utf_8_sig") as content_file:
        content = "\n".join(content_file.readlines())

    # content = "不怪韩风觉得诧异，今日在韩家书房内，通过典籍中的记载，韩风知道。"
    # print(content)
    folder_path = r"E:\voice_and_srt"
    name = "test"
    asyncio.run(
        create_caption_and_voice_files(
            content=content,
            audio_file_path=os.path.join(folder_path, f"{name}.mp3"),
            srt_file_path=os.path.join(folder_path, f"{name}.srt"),
        )
    )
