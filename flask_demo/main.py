from flask import Flask, render_template, send_from_directory
import subprocess
import os

app = Flask(__name__)

DEFAULT_IMAGE = 'default.jpg'
RESULT_IMAGE = 'result.jpg'

# 確保預設圖片存在
if not os.path.exists(DEFAULT_IMAGE):
    # 您可以替換成您實際的預設圖片
    with open(DEFAULT_IMAGE, 'w') as f:
        f.write('') # 創建一個空的預設檔案

@app.route('/')
def index():
    return render_template('index.html', image_filename=DEFAULT_IMAGE)

@app.route('/capture')
def capture():
    subprocess.run(['python', 'webcam.py'])
    return render_template('index.html', image_filename=RESULT_IMAGE)

@app.route('/images/<filename>')
def get_image(filename):
    return send_from_directory('.', filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)