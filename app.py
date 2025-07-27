# app.py
from flask import Flask, request, render_template, send_file
import pandas as pd
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # Processamento fictício para exemplo
    df_resultado = pd.DataFrame({
        'Indicador': ['PL Total', 'Rentabilidade Mês', 'Stress Selic -2%'],
        'Valor': ['R$ 25.000.000,00', '1,43%', '-3,28%']
    })

    output_path = os.path.join(UPLOAD_FOLDER, 'resultado.xlsx')
    df_resultado.to_excel(output_path, index=False)

    return send_file(output_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=False, use_reloader=True)
  
