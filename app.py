# app.py
from flask import Flask, request, render_template, send_file, redirect, url_for
import pandas as pd
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'xml', 'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return redirect(url_for('index'))

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # Processa os dados com base na extensão
    ext = filename.rsplit('.', 1)[1].lower()
    if ext in ['xlsx', 'xls']:
        df = pd.read_excel(filepath)
    elif ext == 'csv':
        df = pd.read_csv(filepath)
    else:
        return render_template('resultado.html', error='Formato ainda não suportado totalmente.')

    # Faz cálculos simples (para exemplo real, ajustar para estrutura do XML real depois)
    df['% PL'] = pd.to_numeric(df.get('% PL', 0), errors='coerce')
    df['Valor de Mercado'] = pd.to_numeric(df.get('Valor de Mercado', 0), errors='coerce')
    
    pl_total = df['Valor de Mercado'].sum()
    maior_ativo = df.loc[df['% PL'].idxmax()]['Nome do Ativo'] if '% PL' in df else 'Desconhecido'
    ativos_distintos = df['Nome do Ativo'].nunique() if 'Nome do Ativo' in df else len(df)

    por_tipo = df.groupby('Tipo de Ativo')['Valor de Mercado'].sum()
    por_tipo_percentual = (por_tipo / pl_total * 100).round(2).to_dict()

    resultado = {
        'PL Total': f"R$ {pl_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
        'Maior Ativo': maior_ativo,
        'Ativos Distintos': ativos_distintos,
        'Composição por Tipo': por_tipo_percentual,
        'Data': datetime.now().strftime('%d/%m/%Y')
    }

    return render_template('resultado.html', resultado=resultado)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)





  
