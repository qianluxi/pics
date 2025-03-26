from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import os
from PIL import Image
import shutil
from datetime import datetime

app = Flask(__name__)

# 使用绝对路径
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.getcwd(), 'uploads'))
OUTPUT_FOLDER = os.path.abspath(os.path.join(UPLOAD_FOLDER, 'output'))

# 创建上传和输出文件夹（如果它们不存在）
if not os.path.exists(UPLOAD_FOLDER):
    print(f"Creating upload folder: {UPLOAD_FOLDER}")
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(OUTPUT_FOLDER):
    print(f"Creating output folder: {OUTPUT_FOLDER}")
    os.makedirs(OUTPUT_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if request.method == 'POST':
        rows = int(request.form['rows'])
        cols = int(request.form['cols'])
        scale = float(request.form['scale'])

        # 清理上传目录中的内容，但不删除 output 文件夹
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path) and file_path != OUTPUT_FOLDER:  # 确保不删除 output 文件夹
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')

        # 保存上传的文件
        files = request.files.getlist("files[]")
        image_paths = []

        # 处理上传的文件
        for file in files:
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            image_paths.append(filepath)

        # 按 rows x cols 的方式分组拼接图片
        group_size = rows * cols  # 每组图片的数量
        num_groups = (len(image_paths) + group_size - 1) // group_size  # 计算需要的组数

        output_filenames = []  # 保存所有生成的拼接图文件名

        for i in range(num_groups):
            # 获取当前组的图片路径
            start_idx = i * group_size
            end_idx = start_idx + group_size
            group_image_paths = image_paths[start_idx:end_idx]

            # 如果最后一组图片不足，不补充图片，直接生成不完整的拼接图
            if len(group_image_paths) < group_size:
                print(f"Last group has only {len(group_image_paths)} images. Generating incomplete concatenated image.")

            # 拼接当前组的图片
            output_filename = datetime.now().strftime("%Y%m%d_%H%M%S_") + f"group_{i + 1}.png"
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)
            concatenate_images(rows, cols, image_paths=group_image_paths, scale=scale).save(output_path)
            output_filenames.append(output_filename)

        # 返回第一张拼接图的结果页面
        return redirect(url_for('result', filename=output_filenames[0]))

@app.route('/result/<filename>')
def result(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)  # 从 output 文件夹提供结果图片

def resize_images(images, scale):
    resized_images = [img.resize((int(img.size[0] * scale), int(img.size[1] * scale)), Image.LANCZOS) for img in images]
    return resized_images

def concatenate_images(rows, cols, image_paths, scale=1.0, gap=5):
    images = [Image.open(path) for path in image_paths]
    widths, heights = zip(*(i.size for i in images))
    max_width = max(widths)
    max_height = max(heights)
    total_width = max_width * cols + gap * (cols - 1)
    total_height = max_height * rows + gap * (rows - 1)
    new_im = Image.new('RGB', (total_width, total_height))
    x_offset = 0
    y_offset = 0
    for i in range(rows):
        for j in range(cols):
            idx = i * cols + j
            if idx < len(images):  # 确保不超出图片数量
                new_im.paste(images[idx], (x_offset, y_offset))
            x_offset += max_width + gap
            if j == cols - 1:  # 如果到达一行的末尾
                x_offset = 0
                y_offset += max_height + gap
    return new_im

if __name__ == '__main__':
    app.run(debug=True)