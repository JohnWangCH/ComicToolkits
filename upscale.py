import time
import os
import glob
import torch
from PIL import Image
from RealESRGAN import RealESRGAN

# 设置设备为 GPU（如果可用），否则为 CPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 检查 CUDA 是否可用，并打印可用 GPU 的数量
if torch.cuda.is_available():
    print("CUDA is available. Number of GPUs:", torch.cuda.device_count())
else:
    print("CUDA is not available.")

# 初始化 RealESRGAN 模型，并加载预训练权重
model = RealESRGAN(device, scale=4)
model.load_weights("weights/RealESRGAN_x2.pth", download=True)


# 定义函数从文件夹中获取图像文件
def get_images_from_folder(folder_path, extensions=None):
    # 如果没有指定扩展名，使用默认的图像扩展名
    if extensions is None:
        extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
    image_files = []
    # 遍历所有指定扩展名的图像文件并添加到列表中
    for ext in extensions:
        image_files.extend(glob.glob(os.path.join(folder_path, "*" + ext)))
    return image_files


# 定义函数对图像进行超分辨率处理并保存
def get_save_images_x2(images, folder_path_output):
    for image_ in images:
        start_time = time.time()  # 记录开始时间
        path_to_image = image_
        image = Image.open(path_to_image).convert("RGB")  # 打开图像并转换为 RGB 模式

        sr_image = model.predict(image)  # 使用模型预测高分辨率图像
        img_dir = image_.split("\\")  # 分割图像路径以获取文件名
        sr_image.save(f"{folder_path_output}/{img_dir[-1]}")  # 保存处理后的图像
        end_time = time.time()  # 记录结束时间
        print(f"{end_time - start_time}秒")  # 打印处理时间


# 主程序入口
if __name__ == "__main__":
    print("main")
    folder_path = r"E:\mjpics\剪映图片-tiktokio.com_meuo4MN6LSS9we9H50v2"  # 文件夹路径
    images_ = get_images_from_folder(folder_path)  # 获取文件夹中的图像文件
    get_save_images_x2(images_, folder_path)
