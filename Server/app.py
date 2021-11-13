import subprocess
import sys
import os
from flask import request, Flask, make_response, render_template

HOME = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__,
            instance_path=HOME,
            instance_relative_config=True,
            template_folder="../Static",
            static_folder="../Static",
            static_url_path='')

app.config['JSON_AS_ASCII'] = False

@app.route("/")
def homePage():
    return render_template('index.html')

@app.route('/api/zpy', methods=['POST', 'OPTIONS'])
def zpy():
    if request.method == 'POST':
        code = request.json['code']
        output = subprocess.check_output([sys.executable, '-c', code])
        print(output.decode().encode())
        response = make_response(output.decode())
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET,POST'
        response.headers['Access-Control-Allow-Headers'] = 'x-requested-with,content-type'
        return response
    else:
        # CORS跨域配置
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET,POST'
        response.headers['Access-Control-Allow-Headers'] = 'x-requested-with,content-type'
        return response


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
