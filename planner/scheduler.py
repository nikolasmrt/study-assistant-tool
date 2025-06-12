from .db import conectar
from datetime import datetime
import matplotlib.pyplot as plt
import csv

def registrar_estudo(materia, duracao):
    data = datetime.now().strftime("%Y-%m-%d")
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO estudos (materia, duracao, data)
        VALUES (%s, %s, %s)
    """, (materia, duracao, data))
    conn.commit()
    conn.close()

def mostrar_grafico():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT materia, SUM(duracao)
        FROM estudos
        GROUP BY materia;
    """)
    resultados = cursor.fetchall()
    conn.close()

    if not resultados:
        print("Nenhum dado para exibir.")
        return

    materias = [linha[0] for linha in resultados]
    duracoes = [linha[1] for linha in resultados]

    plt.figure(figsize=(8, 6))
    plt.bar(materias, duracoes, color='skyblue')
    plt.xlabel("Matéria")
    plt.ylabel("Tempo total de estudo (min)")
    plt.title("Progresso por Matéria")
    plt.tight_layout()
    plt.show()

def exportar_csv(nome_arquivo="estudos_exportados.csv"):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM estudos")
    dados = cursor.fetchall()
    colunas = [i[0] for i in cursor.description]
    conn.close()

    with open(nome_arquivo, "w", newline='', encoding='utf-8') as f:
        escritor = csv.writer(f)
        escritor.writerow(colunas)
        escritor.writerows(dados)

def limpar_dados():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM estudos")
    conn.commit()
    conn.close()
    print("📂 Todos os registros de estudo foram apagados.")

def zerar_tempos():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE estudos SET duracao = 0")
    conn.commit()
    conn.close()
    print("⏰ Todos os tempos de estudo foram zerados.")

def recomendar_estudo():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT materia, AVG(duracao) as media
        FROM estudos
        GROUP BY materia
        ORDER BY media ASC
        LIMIT 1;
    """)
    resultado = cursor.fetchone()
    conn.close()

    if resultado:
        materia, media = resultado
        return f"📌 Recomendamos estudar mais '{materia}' (média de {int(media)} min)"
    else:
        return "Sem dados suficientes para recomendação."
