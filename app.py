import sys
import sqlite3
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFileDialog,
                             QLabel, QLineEdit, QPushButton, QGridLayout, QMessageBox, QTableWidget, QTableWidgetItem)


class EstoqueApp(QWidget):
    def __init__(self):
        super().__init__()
        self.conn = sqlite3.connect('estoque.db')
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.init_ui()

    # Cria as tabelas de produtos e categorias no banco de dados se não existirem.
    def create_tables(self):
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS categorias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS produtos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    quantidade INTEGER NOT NULL CHECK(quantidade >= 0),
                    preco REAL NOT NULL CHECK(preco >= 0),
                    categoria_id INTEGER,
                    FOREIGN KEY (categoria_id) REFERENCES categorias (id)
                )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            self.show_popup("Erro", f"Erro ao criar tabelas: {e}")

    # Inicializa a interface do usuário.
    def init_ui(self):
        self.setWindowTitle("Controle de Estoque")
        self.setGeometry(100, 100, 800, 600)

        # Centraliza a janela
        self.center()

        layout = QVBoxLayout()

        title = QLabel("Controle de Estoque")
        title.setStyleSheet("font-size: 24px; color: black;")
        layout.addWidget(title)

        input_layout = QGridLayout()
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("ID do Produto (para atualização)")
        self.id_input.setMinimumSize(200, 40)  # Aumenta o tamanho do campo
        input_layout.addWidget(self.id_input, 0, 0)

        self.nome_input = QLineEdit()
        self.nome_input.setPlaceholderText("Nome do Produto")
        self.nome_input.setMinimumSize(200, 40)  # Aumenta o tamanho do campo
        input_layout.addWidget(self.nome_input, 0, 1)

        self.quantidade_input = QLineEdit()
        self.quantidade_input.setPlaceholderText("Quantidade")
        self.quantidade_input.setMinimumSize(
            200, 40)  # Aumenta o tamanho do campo
        input_layout.addWidget(self.quantidade_input, 1, 0)

        self.preco_input = QLineEdit()
        self.preco_input.setPlaceholderText("Preço do Produto")
        self.preco_input.setMinimumSize(200, 40)  # Aumenta o tamanho do campo
        input_layout.addWidget(self.preco_input, 1, 1)

        self.categoria_input = QLineEdit()
        self.categoria_input.setPlaceholderText("Categoria do Produto")
        self.categoria_input.setMinimumSize(
            200, 40)  # Aumenta o tamanho do campo
        input_layout.addWidget(self.categoria_input, 2, 0)

        layout.addLayout(input_layout)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Pesquisar por ID ou Nome")
        self.search_input.setMinimumSize(400, 40)  # Aumenta o tamanho do campo
        layout.addWidget(self.search_input)

        search_button = QPushButton("Pesquisar")
        search_button.setMinimumSize(150, 40)  # Aumenta o tamanho do botão
        layout.addWidget(search_button)
        search_button.clicked.connect(self.search_products)

        button_layout = QHBoxLayout()

        add_button = QPushButton("Adicionar Produto")
        add_button.setMinimumSize(150, 40)  # Aumenta o tamanho do botão
        button_layout.addWidget(add_button)
        add_button.clicked.connect(self.add_product)

        update_button = QPushButton("Atualizar Produto")
        update_button.setMinimumSize(150, 40)  # Aumenta o tamanho do botão
        button_layout.addWidget(update_button)
        update_button.clicked.connect(self.update_product)

        delete_all_button = QPushButton("Excluir Todos os Produtos")
        delete_all_button.setMinimumSize(150, 40)  # Aumenta o tamanho do botão
        button_layout.addWidget(delete_all_button)
        delete_all_button.clicked.connect(self.delete_all_products)

        delete_item_button = QPushButton("Excluir Produto Selecionado")
        delete_item_button.setMinimumSize(
            150, 40)  # Aumenta o tamanho do botão
        button_layout.addWidget(delete_item_button)
        delete_item_button.clicked.connect(self.delete_product)

        add_categoria_button = QPushButton("Adicionar Categoria")
        add_categoria_button.setMinimumSize(
            150, 40)  # Aumenta o tamanho do botão
        button_layout.addWidget(add_categoria_button)
        add_categoria_button.clicked.connect(self.add_categoria)

        # Botões para gerar relatórios
        generate_csv_button = QPushButton("Gerar CSV")
        generate_csv_button.setMinimumSize(
            150, 40)  # Aumenta o tamanho do botão
        button_layout.addWidget(generate_csv_button)
        generate_csv_button.clicked.connect(self.generate_csv)

        generate_pdf_button = QPushButton("Gerar PDF")
        generate_pdf_button.setMinimumSize(
            150, 40)  # Aumenta o tamanho do botão
        button_layout.addWidget(generate_pdf_button)
        generate_pdf_button.clicked.connect(self.generate_pdf)

        layout.addLayout(button_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Nome", "Quantidade", "Preço", "Categoria"])
        self.table.setMinimumSize(600, 300)  # Aumenta o tamanho da tabela
        layout.addWidget(self.table)

        self.setLayout(layout)

    # Centraliza a janela na tela.
    def center(self):
        qr = self.frameGeometry()
        cp = QApplication.desktop().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # Adiciona um novo produto ao banco de dados.
    def add_product(self):
        nome = self.nome_input.text()
        quantidade = self.quantidade_input.text()
        preco = self.preco_input.text()
        categoria = self.categoria_input.text()

        if not nome or not quantidade or not preco:
            self.show_popup("Erro", "Por favor, preencha todos os campos.")
            return

        self.cursor.execute(
            'SELECT id FROM categorias WHERE nome = ?', (categoria,))
        categoria_id = self.cursor.fetchone()

        if categoria_id is None:
            self.show_popup(
                "Erro", "A categoria não existe. Por favor, adicione a categoria primeiro.")
            return

        try:
            self.cursor.execute('''
                INSERT INTO produtos (nome, quantidade, preco, categoria_id)
                VALUES (?, ?, ?, ?)
            ''', (nome, quantidade, preco, categoria_id[0]))
            self.conn.commit()
            self.load_products()
            self.clear_inputs()
            self.show_popup("Sucesso", "Produto adicionado com sucesso.")
        except sqlite3.Error as e:
            self.show_popup("Erro", f"Erro ao adicionar produto: {e}")

    # Carrega todos os produtos do banco de dados.
    def load_products(self):
        self.cursor.execute('''
            SELECT produtos.id, produtos.nome, produtos.quantidade, produtos.preco, categorias.nome
            FROM produtos
            LEFT JOIN categorias ON produtos.categoria_id = categorias.id
        ''')
        results = self.cursor.fetchall()
        self.load_table(results)

    # Carrega os dados na tabela.
    def load_table(self, results):
        self.table.setRowCount(0)
        for row in results:
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            for column, data in enumerate(row):
                self.table.setItem(row_position, column,
                                   QTableWidgetItem(str(data)))

    # Limpa os campos de entrada.
    def clear_inputs(self):
        self.id_input.clear()
        self.nome_input.clear()
        self.quantidade_input.clear()
        self.preco_input.clear()
        self.categoria_input.clear()

    # Exibe uma janela pop-up com uma mensagem.
    def show_popup(self, title, message):
        msg = QMessageBox()
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec_()

    # Pesquisa produtos com base no termo de pesquisa.
    def search_products(self):
        search_term = self.search_input.text()
        if not search_term:
            self.load_products()
            return

        self.cursor.execute('''
            SELECT produtos.id, produtos.nome, produtos.quantidade, produtos.preco, categorias.nome
            FROM produtos
            LEFT JOIN categorias ON produtos.categoria_id = categorias.id
            WHERE produtos.id = ? OR produtos.nome LIKE ?
        ''', (search_term, f'%{search_term}%'))
        results = self.cursor.fetchall()
        if not results:  # Verifica se não encontrou resultados
            self.show_popup("Resultado da Pesquisa",
                            "Nenhum produto encontrado.")
        else:
            self.load_table(results)

    # Atualiza um produto existente no banco de dados.
    def update_product(self):
        product_id = self.id_input.text()
        nome = self.nome_input.text()
        quantidade = self.quantidade_input.text()
        preco = self.preco_input.text()
        categoria = self.categoria_input.text()

        if not product_id or not nome or not quantidade or not preco:
            self.show_popup("Erro", "Por favor, preencha todos os campos.")
            return

        self.cursor.execute(
            'SELECT id FROM categorias WHERE nome = ?', (categoria,))
        categoria_id = self.cursor.fetchone()

        if categoria_id is None:
            self.show_popup(
                "Erro", "A categoria não existe. Por favor, adicione a categoria primeiro.")
            return

        try:
            self.cursor.execute('''
                UPDATE produtos
                SET nome = ?, quantidade = ?, preco = ?, categoria_id = ?
                WHERE id = ?
            ''', (nome, quantidade, preco, categoria_id[0], product_id))
            self.conn.commit()
            self.load_products()
            self.clear_inputs()
            self.show_popup("Sucesso", "Produto atualizado com sucesso.")
        except sqlite3.Error as e:
            self.show_popup("Erro", f"Erro ao atualizar produto: {e}")

    # Exclui um produto selecionado da tabela.
    def delete_product(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            self.show_popup(
                "Erro", "Por favor, selecione um produto para excluir.")
            return

        product_id = self.table.item(selected_row, 0).text()
        try:
            self.cursor.execute(
                'DELETE FROM produtos WHERE id = ?', (product_id,))
            self.conn.commit()
            self.load_products()
            self.show_popup("Sucesso", "Produto excluído com sucesso.")
        except sqlite3.Error as e:
            self.show_popup("Erro", f"Erro ao excluir produto: {e}")

    # Exclui todos os produtos do banco de dados.
    def delete_all_products(self):
        try:
            self.cursor.execute('DELETE FROM produtos')
            self.conn.commit()
            self.load_products()
            self.show_popup("Sucesso", "Todos os produtos foram excluídos.")
        except sqlite3.Error as e:
            self.show_popup("Erro", f"Erro ao excluir produtos: {e}")

    # Adiciona uma nova categoria ao banco de dados.
    def add_categoria(self):
        categoria = self.categoria_input.text()
        if not categoria:
            self.show_popup(
                "Erro", "Por favor, preencha o campo de categoria.")
            return

        try:
            self.cursor.execute('''
                INSERT INTO categorias (nome) VALUES (?)
            ''', (categoria,))
            self.conn.commit()
            self.show_popup("Sucesso", "Categoria adicionada com sucesso.")
        except sqlite3.Error as e:
            self.show_popup("Erro", f"Erro ao adicionar categoria: {e}")

    # Gera um arquivo CSV com os produtos.
    def generate_csv(self):
        self.cursor.execute('''
            SELECT produtos.id, produtos.nome, produtos.quantidade, produtos.preco, categorias.nome
            FROM produtos
            LEFT JOIN categorias ON produtos.categoria_id = categorias.id
        ''')
        results = self.cursor.fetchall()

        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Salvar CSV", "", "CSV Files (*.csv);;All Files (*)", options=options)
        if file_name:  # Verifica se o usuário selecionou um arquivo
            with open(file_name, 'w') as f:
                for row in results:
                    f.write(','.join(map(str, row)) + '\n')
            self.show_popup("Sucesso", "Arquivo CSV gerado com sucesso.")

    # Gera um relatório em PDF com os produtos.
    def generate_pdf(self):
        self.cursor.execute('''
            SELECT produtos.id, produtos.nome, produtos.quantidade, produtos.preco, categorias.nome
            FROM produtos
            LEFT JOIN categorias ON produtos.categoria_id = categorias.id
        ''')
        results = self.cursor.fetchall()

        pdf_file = 'relatorio_produtos.pdf'
        c = canvas.Canvas(pdf_file, pagesize=letter)
        c.drawString(100, 750, "Relatório de Produtos")
        c.drawString(
            100, 730, "ID    Nome    Quantidade    Preço    Categoria")

        y = 710
        for row in results:
            c.drawString(100, y, f"{row[0]}    {row[1]}    {
                         row[2]}    {row[3]}    {row[4]}")
            y -= 20

        c.save()
        self.show_popup("Sucesso", "Relatório PDF gerado com sucesso.")

 # Executa o aplicativo
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EstoqueApp()
    window.show()
    sys.exit(app.exec_())
