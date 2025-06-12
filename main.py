import customtkinter as ctk
from tkinter import messagebox
from planner.scheduler import registrar_estudo, mostrar_grafico, exportar_csv, limpar_dados, zerar_tempos, recomendar_estudo



# Criando a interface
app = ctk.CTk()
app.title("Organizador de Estudos")
app.geometry("650x350")
app.grid_columnconfigure((0, 1), weight=1)
app.grid_rowconfigure((4, 5, 6), weight=1)


# Layout da interface
titulo = ctk.CTkLabel(app, text="📚 Organizador de Estudos", font=("Arial", 20))
titulo.grid(row=0, column=0, columnspan=2, pady=10)

# Campo de entrada para matéria
label_materia = ctk.CTkLabel(app, text="Matéria:")
label_materia.grid(row=1, column=0, padx=10, pady=(10, 0))
entrada_materia = ctk.CTkEntry(app, width=300)
entrada_materia.grid(row=1, column=1, padx=10, pady=(10, 0))

# Campo de entrada para duração
label_duracao = ctk.CTkLabel(app, text="Duração (minutos):")
label_duracao.grid(row=2, column=0, padx=10, pady=(10, 0))
entrada_duracao = ctk.CTkEntry(app, width=300)
entrada_duracao.grid(row=2, column=1, padx=10, pady=(10, 0))

# Mensagem de status
mensagem = ctk.CTkLabel(app, text="", text_color="green")
mensagem.grid(row=3, column=0, columnspan=2, pady=5)

# Função para registrar estudo
def registrar():
    materia = entrada_materia.get()
    duracao = entrada_duracao.get()
    if materia and duracao.isdigit():
        registrar_estudo(materia, int(duracao))
        mensagem.configure(text="✅ Estudo registrado com sucesso!", text_color="green")
        entrada_materia.delete(0, 'end')
        entrada_duracao.delete(0, 'end')
    else:
        mensagem.configure(text="❌ Preencha corretamente os campos", text_color="red")

# Função para exportar os dados para CSV
def exportar():
    exportar_csv()
    messagebox.showinfo("Exportado", "📁 Dados exportados para estudos_exportados.csv")

# Função para limpar todos os dados
def limpar():
    limpar_dados()
    messagebox.showinfo("Limpeza", "📂 Todos os registros de estudo foram apagados.")

# Função para zerar os tempos de estudo
def zerar():
    zerar_tempos()
    messagebox.showinfo("Zerar Tempos", "⏰ Todos os tempos de estudo foram zerados.")

# Função para recomendar o próximo estudo
def mostrar_recomendacao():
    recomendacao = recomendar_estudo()
    messagebox.showinfo("Recomendação de Estudo", recomendacao)

# Função para definir o tamanho fixo dos botões
botao_largura = 300  # Tamanho fixo para largura dos botões
botao_altura = 40    # Tamanho fixo para altura dos botões

# Botões da interface - Organizados em uma grid 2x3
ctk.CTkButton(app, text="Registrar Estudo", command=registrar).grid(row=4, column=0, padx=10, pady=5, sticky="nsew")
ctk.CTkButton(app, text="Ver Gráfico de Progresso", command=mostrar_grafico).grid(row=4, column=1, padx=10, pady=5, sticky="nsew")
ctk.CTkButton(app, text="Exportar CSV", command=exportar).grid(row=5, column=0, padx=10, pady=5, sticky="nsew")
ctk.CTkButton(app, text="Limpar Dados", command=limpar).grid(row=5, column=1, padx=10, pady=5, sticky="nsew")
ctk.CTkButton(app, text="Zerar Tempos", command=zerar).grid(row=6, column=0, padx=10, pady=5, sticky="nsew")
ctk.CTkButton(app, text="📌 Ver Recomendação", command=mostrar_recomendacao).grid(row=6, column=1, padx=10, pady=5, sticky="nsew")

# Iniciar a interface
app.mainloop()
