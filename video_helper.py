import json
import os
import random
import re
from datetime import datetime
import subprocess
import asyncio


imagemagick_path = "C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"
stroke_color = "yellow"
stroke_width = 1.2
kerning = 1
width = 1280
height = 720
animation_speed = 1.2

if imagemagick_path:
    os.environ["IMAGEMAGICK_BINARY"] = rf"{imagemagick_path}"


async def generate_video(
    image_path: str,
    name: str,
    video_dir_path: str,
    audio_dir_path: str,
    audio_file_paths: list[str] = None,
    srt_file_paths: list[str] = None,
):
    """Generate video by merging all video related materials (incl. pictures, audio files) to a video.

    Args:
        picture_dir_path (str): path of the directory that contains all pictures
        name (str): the novel name
        video_dir_path (str): path of the directory for the output video
        audio_dir_path (str): path of the directory that contains all audio files
        audio_file_paths (list[str]): list of audio files, Default None
        srt_file_paths (list[str]): list of srt files, Default None
    """

    def extract_number(filename):
        match = re.search(r"(\d+)", filename)
        if match:
            return int(match.group(0))
        return 0  # 如果文件名中没有数字，则默认为 0

    # picture_path_list = sorted(
    #     [
    #         os.path.join(picture_dir_path, name)
    #         for name in os.listdir(picture_dir_path)
    #         if name.endswith(".png")
    #     ],
    #     key=lambda x: extract_number(os.path.basename(x)),
    # )
    audio_file_paths = (
        sorted(
            [
                os.path.join(audio_dir_path, name)
                for name in os.listdir(audio_dir_path)
                if name.endswith(".mp3")
            ],
            key=lambda x: extract_number(os.path.basename(x)),
        )
        if audio_file_paths is None
        else audio_file_paths
    )
    srt_file_paths = (
        sorted(
            [
                os.path.join(audio_dir_path, name)
                for name in os.listdir(audio_dir_path)
                if name.endswith(".srt")
            ],
            key=lambda x: extract_number(os.path.basename(x)),
        )
        if srt_file_paths is None
        else srt_file_paths
    )
    video_list_file_path = os.path.join(video_dir_path, f"{name}.txt")
    output_video_path = os.path.join(video_dir_path, f"{name}.mp4")

    if os.path.isfile(video_list_file_path):
        os.remove(video_list_file_path)
    # if os.path.exists(video_dir_path):
    #     filelist = os.listdir(video_dir_path)
    #     if len(filelist) != 0:  # 开始删除所有文件
    #         for file in filelist:
    #             os.remove(os.path.join(video_dir_path, file))
    #     os.rmdir(video_dir_path)

    for index, audio_file_path in enumerate(audio_file_paths, start=1):
        video_path = os.path.join(video_dir_path, f"{index}.mp4")
        if os.path.exists(video_path):
            print(f"{index}.mp4 exists, skip.")
            continue
        duration = await get_media_length(audio_file_path)
        print(f"duration: {duration}")
        os.makedirs(video_dir_path, exist_ok=True)
        # r"E:\mjpics\剪映图片-大道至簡\%05d.png"
        _create_animated_segment(
            image_path,
            audio_file_path,
            duration,
            animation_speed,
            _get_random_action(),
            video_path,
        )
        # clip.write_videofile(video_path, fps=24, audio_codec="aac")
        _add_caption(video_path, srt_file_paths[index - 1])

        # update video list
        with open(video_list_file_path, "a", encoding="utf-8") as f:
            f.write(f"file '{video_path}'\n")
        print(f"-----------生成第{index}段视频-----------")
    print("-----------开始合成视频-----------")
    _concat_videos(video_list_file_path, output_video_path)

    # include bgm
    print("-----------整合bgm-----------")
    # await _add_bgm(output_video_path, "bgm//3.mp3")


# $获取媒体文件长度
async def get_media_length(file_path):
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            file_path,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return float(result.stdout)


# 获取音频文件的详细信息（比特率、采样率、声道数）
async def get_audio_details(file_path):
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "a:0",
        "-show_entries",
        "stream=bit_rate,sample_rate,channels",
        "-of",
        "json",
        file_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    metadata = json.loads(result.stdout)
    details = {
        "bit_rate": int(metadata["streams"][0]["bit_rate"]),
        "sample_rate": int(metadata["streams"][0]["sample_rate"]),
        "channels": int(metadata["streams"][0]["channels"]),
    }
    return details


# 循环BGM以匹配主音轨长度，然后与主音轨混合
async def _add_bgm(video_file, bgm_file):
    print("start merging bgm into video ...")
    # await merge_bgm("bgm")
    main_db = "15"
    bgm_db = "0"
    video_dir = os.path.dirname(video_file)
    tmp_video_file = os.path.join(video_dir, "tmp_bgm.mp4")
    converted_bgm = os.path.join(video_dir, "bgm_converted.mp3")

    main_length = await get_media_length(video_file)
    bgm_length = await get_media_length(bgm_file)
    main_volume = f"{main_db}dB"
    bgm_volume = f"{bgm_db}dB"
    # 计算BGM需要循环的次数
    loop_count = int(main_length // bgm_length) + 1 if bgm_length < main_length else 1

    # 如果需要，循环BGM
    if loop_count > 1:
        with open("looped_bgm_list.txt", "w", encoding="utf-8") as loop_file:
            for _ in range(loop_count):
                loop_file.write(f"file '{bgm_file}'\n")
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                "looped_bgm_list.txt",
                "-c",
                "copy",
                "looped_bgm.mp3",
            ],
            check=True,
        )
        looped_bgm = "looped_bgm.mp3"
        os.remove("looped_bgm_list.txt")
    else:
        looped_bgm = bgm_file

    audio_details = await get_audio_details(video_file)

    # 采样率、声道和比特率
    sample_rate = str(audio_details["sample_rate"])
    channels = str(audio_details["channels"])
    # bitrate = str(audio_details["bit_rate"])

    # 转换循环后的BGM为单声道，采样率调整为24kHz
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            looped_bgm,
            "-ac",
            str(channels),
            "-ar",
            str(sample_rate),
            converted_bgm,
        ],
        check=True,
    )

    subprocess.run(
        [
            "ffmpeg",
            "-i",
            video_file,
            "-i",
            converted_bgm,
            "-filter_complex",
            f"[0:a]volume={main_volume}[a0];[1:a]volume={bgm_volume}[a1];[a0][a1]amerge=inputs=2[a]",
            "-map",
            "0:v",
            "-map",
            "[a]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-ac",
            "2",
            tmp_video_file,
        ],
        check=True,
    )

    # 清理临时文件
    # os.remove(converted_bgm)
    if loop_count > 1:
        os.remove("looped_bgm.mp3")
    os.replace(tmp_video_file, video_file)


def _get_random_action():
    actions = ["shrink", "left_move", "right_move", "up_move", "down_move"]
    return random.choice(actions)


def _create_animated_segment(
    image_path, audio_path, duration, multiple, action, output_file
):
    initial_zoom = 1.0
    zoom_steps = (multiple - initial_zoom) / (25 * duration)
    l_r_move = (width * multiple - width - 25) / (25 * duration)
    u_d_move = (height * multiple - height - 25 - 25) / (25 * duration)
    if action == "shrink":
        scale = (
            f"scale=-2:ih*10,zoompan=z='if(lte(zoom,{initial_zoom}),{multiple},max(zoom-{zoom_steps},1))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=25*"
            + str(duration)
            + f":s={width}x{height}"
        )
    elif action == "left_move":
        scale = (
            f"scale=-2:ih*10,zoompan='{multiple}':x='if(lte(on,-1),(iw-iw/zoom)/2,x+{l_r_move * 10})':y='if(lte(on,1),(ih-ih/zoom)/2,y)':d=25*"
            + str(duration)
            + f":s={width}x{height}"
        )
    elif action == "right_move":
        scale = (
            f"scale=-2:ih*10,zoompan='{multiple}':x='if(lte(on,1),(iw/zoom)/2,x-{l_r_move * 10})':y='if(lte(on,1),(ih-ih/zoom)/2,y)':d=25*"
            + str(duration)
            + f":s={width}x{height}"
        )
    elif action == "up_move":
        scale = (
            f"scale=-2:ih*10,zoompan='{multiple}':x='if(lte(on,1),(iw-iw/zoom)/2,x)':y='if(lte(on,-1),(ih-ih/zoom)/2,y+{u_d_move * 10})':d=25*"
            + str(duration)
            + f":s={width}x{height}"
        )

    elif action == "down_move":
        scale = (
            f"scale=-2:ih*10,zoompan='{multiple}':x='if(lte(on,1),(iw-iw/zoom)/2,x)':y='if(lte(on,1),(ih/zoom)/2,y-{u_d_move * 10})':d=25*"
            + str(duration)
            + f":s={width}x{height}"
        )
    else:
        scale = f"scale=-2:ih*10,zoompan=z='min(zoom+{zoom_steps},{multiple})*if(gte(zoom,1),1,0)+if(lt(zoom,1),1,0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=25*{duration}:s={width}x{height}"

    # scale = f"hwupload_cuda,{scale}"
    scale = f"format=nv12,hwupload_cuda,scale_cuda=1080:-1"

    # Constructing the FFmpeg command

    cmd = [
        "ffmpeg",
        "-framerate",
        "0.25",  # Every image shows up for 4s
        "-y",
        "-loop",
        "1",
        "-t",
        str(duration),
        "-i",
        image_path,
        "-i",
        audio_path,
        "-filter_complex",
        scale,
        "-c:v",
        "h264_nvenc",
        "-preset",
        "p1",
        "-cq",
        "30",  # Use constant quality
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-r",  # output framerate
        "30",
        output_file,
    ]
    # ffmpeg -loop 1 -i background.jpg -i audio.mp3 -vf "subtitles=subtitle.srt" -c:v h264_nvenc -preset fast -c:a aac -b:a 192k -shortest output.mp4

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")


def _concat_videos(video_list_file_path: str, out_path: str):
    subprocess.run(
        [
            "ffmpeg",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            f"{video_list_file_path}",
            "-c",
            "copy",
            f"{out_path}",
        ]
    )


def _add_caption(video_path, srt_path):
    """Add captions to the video file.
    Args:
        video_path (str): the original video file (w/o caption)
        srt_path (str): the caption file path
    """
    fontsize = 20
    fontcolor = "FFFFFF"
    fontfile = "simhei.ttf"
    position = "Alignment=2,MarginV=50"

    out_path = os.path.join(os.path.dirname(video_path), "tmp.mp4")
    # 构建字体样式字符串，只包含颜色和大小
    style = f"FontName={fontfile.split('.')[0]},Fontsize={fontsize},PrimaryColour=&H{fontcolor},Bold=1,{position}"

    # 构建 FFmpeg 命令，不再设置字体文件路径
    if os.name == "nt":
        # 由于绝对路径下win会报错 所以转换成相对路径
        proj_path = os.path.abspath("./")
        out_path = os.path.relpath(out_path, proj_path).replace("\\", "/")
        video_path = os.path.relpath(video_path, proj_path).replace("\\", "/")
        srt_path = os.path.relpath(srt_path, proj_path).replace("\\", "/")

    cmd = [
        "ffmpeg",
        "-i",
        video_path,  # Input video file
        "-vf",
        f"subtitles='{srt_path}':force_style='{style}'",  # Apply subtitles with specified style
        "-c:v",
        "h264_nvenc",  # Use NVIDIA NVENC for hardware-accelerated video encoding
        "-preset",
        "fast",  # Use a fast encoding preset
        "-c:a",
        "copy",  # Copy audio stream without re-encoding
        out_path,  # Output file path
    ]

    subprocess.run(cmd, check=True)
    os.replace(out_path, video_path)  # 用输出文件替换原始文件


if __name__ == "__main__":
    start_time = datetime.now()
    asyncio.run(
        generate_video(
            audio_dir_path=r"C:\voice_and_srt\大道至簡",
            image_path=r"E:\mjpics\剪映图片-大道至簡\*.png",
            name="test",
            video_dir_path=r"C:\videos\大道至簡",
        )
    )

    # _add_caption(
    #     video_path=r"C:\videos\大道至簡\1.mp4",
    #     srt_path=r"C:\voice_and_srt\大道至簡\0.srt",
    # )
    end_time = datetime.now()
    time_diff = end_time - start_time
    print(f"Time difference: {time_diff}")
    print(f"Seconds elapsed: {time_diff.total_seconds()} seconds")
