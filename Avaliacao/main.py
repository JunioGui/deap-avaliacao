from flask import Flask, render_template_string, request, redirect, url_for, jsonify, send_file
import sqlite3
from datetime import datetime
import pandas as pd

app = Flask(__name__)

# Configurar banco de dados
def init_db():
    conn = sqlite3.connect('feedback.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_atendido TEXT,
            nome_atendente TEXT,
            nota INTEGER,
            comentario TEXT,
            data_hora TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Página do formulário
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        nome_atendido = request.form.get('nome_atendido')
        nome_atendente = request.form.get('nome_atendente')
        nota = int(request.form.get('nota'))
        comentario = request.form.get('comentario')
        data_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = sqlite3.connect('feedback.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO feedback (nome_atendido, nome_atendente, nota, comentario, data_hora)
            VALUES (?, ?, ?, ?, ?)
        ''', (nome_atendido, nome_atendente, nota, comentario, data_hora))
        conn.commit()
        conn.close()

        return redirect(url_for('confirmacao'))

    # Formulário HTML
    form_html = '''
    <h2>Sistema de Avaliação de Atendimento</h2>
    <form method="POST">
        Nome (opcional): <input type="text" name="nome_atendido"><br><br>
        Nome do atendente: <input type="text" name="nome_atendente" required><br><br>
        Nota (1 a 5): <input type="number" name="nota" min="1" max="5" required><br><br>
        Comentário:<br><textarea name="comentario"></textarea><br><br>
        <button type="submit">Enviar</button>
    </form>
    '''
    return render_template_string(form_html)

# Página de confirmação
@app.route('/confirmacao')
def confirmacao():
    return "<h2>Obrigado pelo seu feedback!</h2><a href='/'>Voltar</a>"

# Exportar dados para Excel
@app.route('/exportar_excel')
def exportar_excel():
    conn = sqlite3.connect('feedback.db')
    df = pd.read_sql_query('SELECT nome_atendido, nome_atendente, nota, comentario, data_hora FROM feedback', conn)
    conn.close()
    arquivo = 'feedback_exportado.xlsx'
    df.to_excel(arquivo, index=False)
    return send_file(arquivo, as_attachment=True)

# API para dados do gráfico
@app.route('/grafico_dados')
def grafico_dados():
    conn = sqlite3.connect('feedback.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT nome_atendente, AVG(nota) as media
        FROM feedback
        GROUP BY nome_atendente
    ''')
    dados = cursor.fetchall()
    conn.close()

    nomes = [d[0] for d in dados]
    medias = [d[1] for d in dados]
    return jsonify({'nomes': nomes, 'medias': medias})

# Página de relatórios
@app.route('/relatorios')
def relatorios():
    atendente_filtro = request.args.get('atendente', '')

    conn = sqlite3.connect('feedback.db')
    cursor = conn.cursor()

    if atendente_filtro:
        cursor.execute('''
            SELECT nome_atendido, nome_atendente, nota, comentario, data_hora
            FROM feedback
            WHERE nome_atendente LIKE ?
            ORDER BY id DESC
        ''', ('%' + atendente_filtro + '%',))
    else:
        cursor.execute('SELECT nome_atendido, nome_atendente, nota, comentario, data_hora FROM feedback ORDER BY id DESC')

    dados = cursor.fetchall()
    conn.close()

    relatorio_html = '''
    <h2>Relatório de Avaliações</h2>
    <form method="get">
        <input type="text" name="atendente" placeholder="Filtrar por atendente" value="{{ atendente_filtro }}">
        <button type="submit">Filtrar</button>
        <a href="/exportar_excel"><button type="button">Exportar para Excel</button></a>
    </form>
    <canvas id="graficoNotas"></canvas>
    <table border="1" cellpadding="5" cellspacing="0">
        <tr>
            <th>Atendido</th>
            <th>Atendente</th>
            <th>Nota</th>
            <th>Comentário</th>
            <th>Data/Hora</th>
        </tr>
        {% for dado in dados %}
        <tr>
            <td>{{ dado[0] or 'Anônimo' }}</td>
            <td>{{ dado[1] }}</td>
            <td>{{ dado[2] }}</td>
            <td>{{ dado[3] }}</td>
            <td>{{ dado[4] }}</td>
        </tr>
        {% endfor %}
    </table>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        fetch('/grafico_dados')
            .then(response => response.json())
            .then(data => {
                const ctx = document.getElementById('graficoNotas').getContext('2d');
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: data.nomes,
                        datasets: [{
                            label: 'Média das Notas',
                            data: data.medias,
                            backgroundColor: 'rgba(75, 192, 192, 0.6)'
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: { y: { beginAtZero: true, max: 5 } }
                    }
                });
            });
    </script>
    '''
    return render_template_string(relatorio_html, dados=dados, atendente_filtro=atendente_filtro)

if __name__ == '_main_':
    init_db()
    app.run(host='0.0.0.0', port=3000)