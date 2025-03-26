from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import os
from PIL import Image
import shutil
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = './uploads'
OUTPUT_FOLDER = os.path.join(UPLOAD_FOLDER, 'output')  # 定义输出文件夹

# 创建上传和输出文件夹（如果它们不存在）
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(OUTPUT_FOLDER):
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

        # 清理上传目录中的内容，但不删除output文件夹
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    if file_path != OUTPUT_FOLDER:  # 确保不删除output文件夹
                        shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')

        # 保存上传的文件
        files = request.files.getlist("files[]")
        image_paths = []
        for file in files:
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            image_paths.append(filepath)

        # 图片拼接逻辑
        images = [Image.open(path) for path in image_paths]
        images = resize_images(images, scale)
        
        # 使用时间戳生成唯一的文件名
        base_filename = "concatenated_image.png"
        output_filename = datetime.now().strftime("%Y%m%d_%H%M%S_") + base_filename
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)  # 设置拼接图片的保存路径为output文件夹
        concatenate_images(rows, cols, image_paths=image_paths, scale=scale).save(output_path)

        return redirect(url_for('result', filename=output_filename))

@app.route('/result/<filename>')
def result(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)  # 从output文件夹提供结果图片

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
            new_im.paste(images[idx], (x_offset, y_offset))
            x_offset += images[idx].size[0] + gap
            if j == cols - 1:  # 如果到达一行的末尾
                x_offset = 0
                y_offset += images[idx].size[1] + gap
    return new_im

if __name__ == '__main__':
    app.run(debug=True)