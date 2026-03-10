import sqlite3
from datetime import datetime
import calendar
import json
import os

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('financas.db')
        self.cursor = self.conn.cursor()
        self.criar_tabelas()
        self.verificar_e_atualizar_schema()
    
    def criar_tabelas(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS salarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mes_ano TEXT NOT NULL,
                valor REAL NOT NULL,
                data_recebimento TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                cor TEXT DEFAULT '#3498db',
                ativo INTEGER DEFAULT 1
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS despesas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                valor REAL NOT NULL,
                tipo TEXT NOT NULL,
                mes_ano TEXT NOT NULL,
                dia_vencimento INTEGER,
                data_vencimento TEXT,
                data_pagamento TEXT,
                status TEXT DEFAULT 'pendente',
                parcela_atual INTEGER,
                total_parcelas INTEGER,
                id_despesa_original INTEGER,
                ativo INTEGER DEFAULT 1,
                categoria_id INTEGER,
                FOREIGN KEY(categoria_id) REFERENCES categorias(id)
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS orcamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                categoria_id INTEGER NOT NULL,
                mes_ano TEXT NOT NULL,
                limite REAL NOT NULL,
                FOREIGN KEY(categoria_id) REFERENCES categorias(id),
                UNIQUE(categoria_id, mes_ano)
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS metas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                valor_alvo REAL NOT NULL,
                valor_atual REAL DEFAULT 0,
                data_limite TEXT,
                data_criacao TEXT DEFAULT (date('now')),
                ativo INTEGER DEFAULT 1
            )
        ''')
        self.conn.commit()
        print("✅ Banco de dados inicializado.")
        self.inserir_categorias_padrao()
    
    def inserir_categorias_padrao(self):
        self.cursor.execute("SELECT COUNT(*) FROM categorias WHERE ativo = 1")
        if self.cursor.fetchone()[0] == 0:
            categorias = [
                ('Alimentação', '#e74c3c'),
                ('Transporte', '#3498db'),
                ('Saúde', '#2ecc71'),
                ('Lazer', '#f39c12'),
                ('Moradia', '#9b59b6'),
                ('Educação', '#1abc9c'),
                ('Outros', '#95a5a6')
            ]
            self.cursor.executemany("INSERT INTO categorias (nome, cor) VALUES (?, ?)", categorias)
            self.conn.commit()
            print("✅ Categorias padrão inseridas.")
    
    def verificar_e_atualizar_schema(self):
        self.cursor.execute("PRAGMA table_info(despesas)")
        colunas = [info[1] for info in self.cursor.fetchall()]
        if 'categoria_id' not in colunas:
            print("🔄 Adicionando coluna categoria_id à tabela despesas...")
            self.cursor.execute("ALTER TABLE despesas ADD COLUMN categoria_id INTEGER REFERENCES categorias(id)")
            self.conn.commit()
            print("✅ Coluna categoria_id adicionada.")
        if 'dia_vencimento' not in colunas:
            print("🔄 Adicionando coluna dia_vencimento à tabela despesas...")
            self.cursor.execute("ALTER TABLE despesas ADD COLUMN dia_vencimento INTEGER")
            self.conn.commit()
            print("✅ Coluna dia_vencimento adicionada.")
    
    def get_salario(self, mes_ano):
        self.cursor.execute('SELECT valor FROM salarios WHERE mes_ano = ?', (mes_ano,))
        row = self.cursor.fetchone()
        return row[0] if row else 0.0
    
    def set_salario(self, mes_ano, valor):
        self.cursor.execute('SELECT id FROM salarios WHERE mes_ano = ?', (mes_ano,))
        row = self.cursor.fetchone()
        if row:
            self.cursor.execute('''
                UPDATE salarios SET valor = ?, data_recebimento = ? WHERE mes_ano = ?
            ''', (valor, datetime.now().strftime('%Y-%m-%d'), mes_ano))
        else:
            self.cursor.execute('''
                INSERT INTO salarios (mes_ano, valor, data_recebimento)
                VALUES (?, ?, ?)
            ''', (mes_ano, valor, datetime.now().strftime('%Y-%m-%d')))
        self.conn.commit()
    
    def get_despesas_mes(self, mes_ano):
        self.cursor.execute('''
            SELECT d.*, c.nome as categoria_nome, c.cor as categoria_cor
            FROM despesas d
            LEFT JOIN categorias c ON d.categoria_id = c.id
            WHERE d.mes_ano = ? AND d.ativo = 1
            ORDER BY d.data_vencimento
        ''', (mes_ano,))
        return self.cursor.fetchall()
    
    def get_categorias(self):
        self.cursor.execute("SELECT id, nome, cor FROM categorias WHERE ativo = 1 ORDER BY nome")
        return self.cursor.fetchall()
    
    def add_categoria(self, nome, cor='#3498db'):
        self.cursor.execute("SELECT id FROM categorias WHERE nome = ? AND ativo = 0", (nome,))
        inativa = self.cursor.fetchone()
        if inativa:
            self.cursor.execute("UPDATE categorias SET ativo = 1, cor = ? WHERE id = ?", (cor, inativa[0]))
            self.conn.commit()
            return True
        try:
            self.cursor.execute("INSERT INTO categorias (nome, cor) VALUES (?, ?)", (nome, cor))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def update_categoria(self, id_categoria, nome, cor):
        self.cursor.execute("SELECT id FROM categorias WHERE nome = ? AND ativo = 1 AND id != ?", (nome, id_categoria))
        if self.cursor.fetchone():
            return False
        self.cursor.execute("UPDATE categorias SET nome = ?, cor = ? WHERE id = ?", (nome, cor, id_categoria))
        self.conn.commit()
        return True
    
    def delete_categoria(self, id_categoria):
        self.cursor.execute("SELECT COUNT(*) FROM despesas WHERE categoria_id = ? AND ativo = 1", (id_categoria,))
        count = self.cursor.fetchone()[0]
        if count > 0:
            return False
        self.cursor.execute("UPDATE categorias SET ativo = 0 WHERE id = ?", (id_categoria,))
        self.conn.commit()
        return True
    
    def _calcular_proximo_mes(self, ano, mes):
        """Calcula o próximo mês (sem usar dateutil)"""
        if mes == 12:
            return ano + 1, 1
        else:
            return ano, mes + 1
    
    def add_despesa(self, descricao, valor_parcela, tipo, mes_ano, dia_vencimento, parcelas=1, categoria_id=None):
        print(f"➕ add_despesa: {descricao}, R$ {valor_parcela:.2f} por parcela, {tipo}, mês {mes_ano}, dia {dia_vencimento}, parcelas={parcelas}, categoria={categoria_id}")

        # Despesas variáveis são criadas como uma única parcela no mês atual e já pagas
        if tipo == 'variavel':
            parcelas = 1
            status_inicial = 'pago'
            data_pagamento = datetime.now().strftime('%Y-%m-%d')
        else:
            status_inicial = 'pendente'
            data_pagamento = None

        ano, mes = map(int, mes_ano.split('-'))

        for i in range(1, parcelas + 1):
            # Calcular o ano e mês para esta parcela
            ano_parcela, mes_parcela = ano, mes
            for _ in range(i-1):
                ano_parcela, mes_parcela = self._calcular_proximo_mes(ano_parcela, mes_parcela)

            mes_parcela_str = f'{ano_parcela:04d}-{mes_parcela:02d}'
            data_parcela = self._obter_data_valida(ano_parcela, mes_parcela, dia_vencimento)

            # Para despesas fixas/parceladas, a descrição pode incluir o número da parcela
            descricao_parcela = descricao
            if parcelas > 1:
                descricao_parcela = f"{descricao} ({i}/{parcelas})"

            self.cursor.execute('''
                INSERT INTO despesas
                (descricao, valor, tipo, mes_ano, dia_vencimento, data_vencimento,
                 parcela_atual, total_parcelas, status, data_pagamento, categoria_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (descricao_parcela, valor_parcela, tipo, mes_parcela_str,
                  dia_vencimento, data_parcela.strftime('%Y-%m-%d'),
                  i if parcelas > 1 else None,
                  parcelas if parcelas > 1 else None,
                  status_inicial, data_pagamento, categoria_id))
            print(f"   Parcela {i}/{parcelas} criada em {mes_parcela_str} com status {status_inicial}")

        self.conn.commit()
    
    def _obter_data_valida(self, ano, mes, dia):
        ultimo_dia = calendar.monthrange(ano, mes)[1]
        dia_ajustado = min(dia, ultimo_dia)
        return datetime(ano, mes, dia_ajustado)
    
    def pagar_despesa(self, id_despesa):
        print(f"\n⚙️ Database: pagar despesa {id_despesa}")
        self.cursor.execute('''
            UPDATE despesas SET status = 'pago', data_pagamento = ?
            WHERE id = ? AND ativo = 1
        ''', (datetime.now().strftime('%Y-%m-%d'), id_despesa))
        self.conn.commit()
        linhas = self.cursor.rowcount
        print(f"   Linhas afetadas: {linhas}")
        return linhas > 0
    
    def excluir_despesa(self, id_despesa):
        print(f"\n🗑️ Database: excluir despesa {id_despesa}")
        self.cursor.execute('UPDATE despesas SET ativo = 0 WHERE id = ?', (id_despesa,))
        self.conn.commit()
        print(f"   Linhas afetadas: {self.cursor.rowcount}")

    def export_to_json(self, filepath):
        dados = {
            'salarios': [],
            'categorias': [],
            'despesas': [],
            'orcamentos': [],
            'metas': []
        }
        self.cursor.execute("SELECT * FROM salarios")
        colunas = [desc[0] for desc in self.cursor.description]
        for row in self.cursor.fetchall():
            dados['salarios'].append(dict(zip(colunas, row)))
        self.cursor.execute("SELECT * FROM categorias")
        colunas = [desc[0] for desc in self.cursor.description]
        for row in self.cursor.fetchall():
            dados['categorias'].append(dict(zip(colunas, row)))
        self.cursor.execute("SELECT * FROM despesas")
        colunas = [desc[0] for desc in self.cursor.description]
        for row in self.cursor.fetchall():
            dados['despesas'].append(dict(zip(colunas, row)))
        self.cursor.execute("SELECT * FROM orcamentos")
        colunas = [desc[0] for desc in self.cursor.description]
        for row in self.cursor.fetchall():
            dados['orcamentos'].append(dict(zip(colunas, row)))
        self.cursor.execute("SELECT * FROM metas")
        colunas = [desc[0] for desc in self.cursor.description]
        for row in self.cursor.fetchall():
            dados['metas'].append(dict(zip(colunas, row)))
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        return True

    def import_from_json(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        self.cursor.execute("PRAGMA foreign_keys = OFF")
        self.conn.commit()
        try:
            self.cursor.execute("DELETE FROM despesas")
            self.cursor.execute("DELETE FROM orcamentos")
            self.cursor.execute("DELETE FROM metas")
            self.cursor.execute("DELETE FROM categorias")
            self.cursor.execute("DELETE FROM salarios")
            
            for item in dados.get('salarios', []):
                placeholders = ', '.join(['?'] * len(item))
                colunas = ', '.join(item.keys())
                self.cursor.execute(f"INSERT INTO salarios ({colunas}) VALUES ({placeholders})", list(item.values()))
            for item in dados.get('categorias', []):
                placeholders = ', '.join(['?'] * len(item))
                colunas = ', '.join(item.keys())
                self.cursor.execute(f"INSERT INTO categorias ({colunas}) VALUES ({placeholders})", list(item.values()))
            for item in dados.get('despesas', []):
                placeholders = ', '.join(['?'] * len(item))
                colunas = ', '.join(item.keys())
                self.cursor.execute(f"INSERT INTO despesas ({colunas}) VALUES ({placeholders})", list(item.values()))
            for item in dados.get('orcamentos', []):
                placeholders = ', '.join(['?'] * len(item))
                colunas = ', '.join(item.keys())
                self.cursor.execute(f"INSERT INTO orcamentos ({colunas}) VALUES ({placeholders})", list(item.values()))
            for item in dados.get('metas', []):
                placeholders = ', '.join(['?'] * len(item))
                colunas = ', '.join(item.keys())
                self.cursor.execute(f"INSERT INTO metas ({colunas}) VALUES ({placeholders})", list(item.values()))
            self.conn.commit()
        finally:
            self.cursor.execute("PRAGMA foreign_keys = ON")
            self.conn.commit()
        return True

    # ---------- MÉTODOS PARA ORÇAMENTOS ----------
    def get_orcamento(self, categoria_id, mes_ano):
        self.cursor.execute("SELECT limite FROM orcamentos WHERE categoria_id = ? AND mes_ano = ?", (categoria_id, mes_ano))
        row = self.cursor.fetchone()
        return row[0] if row else 0.0

    def set_orcamento(self, categoria_id, mes_ano, limite):
        self.cursor.execute('''
            INSERT OR REPLACE INTO orcamentos (categoria_id, mes_ano, limite)
            VALUES (?, ?, ?)
        ''', (categoria_id, mes_ano, limite))
        self.conn.commit()

    def get_todos_orcamentos_mes(self, mes_ano):
        self.cursor.execute('''
            SELECT c.id, c.nome, c.cor, COALESCE(o.limite, 0) as limite
            FROM categorias c
            LEFT JOIN orcamentos o ON c.id = o.categoria_id AND o.mes_ano = ?
            WHERE c.ativo = 1
            ORDER BY c.nome
        ''', (mes_ano,))
        return self.cursor.fetchall()

    def get_total_gasto_por_categoria_mes(self, mes_ano):
        self.cursor.execute('''
            SELECT categoria_id, SUM(valor) as total
            FROM despesas
            WHERE mes_ano = ? AND ativo = 1 AND status = 'pago'
            GROUP BY categoria_id
        ''', (mes_ano,))
        return {row[0]: row[1] for row in self.cursor.fetchall()}

    # ---------- MÉTODOS PARA METAS ----------
    def get_metas(self):
        self.cursor.execute("SELECT id, nome, valor_alvo, valor_atual, data_limite FROM metas WHERE ativo = 1 ORDER BY data_limite")
        return self.cursor.fetchall()

    def add_meta(self, nome, valor_alvo, data_limite):
        self.cursor.execute('''
            INSERT INTO metas (nome, valor_alvo, data_limite)
            VALUES (?, ?, ?)
        ''', (nome, valor_alvo, data_limite))
        self.conn.commit()
        return self.cursor.lastrowid

    def update_meta(self, id_meta, nome, valor_alvo, data_limite):
        self.cursor.execute('''
            UPDATE metas SET nome = ?, valor_alvo = ?, data_limite = ?
            WHERE id = ?
        ''', (nome, valor_alvo, data_limite, id_meta))
        self.conn.commit()

    def update_meta_valor(self, id_meta, valor_atual):
        self.cursor.execute('UPDATE metas SET valor_atual = ? WHERE id = ?', (valor_atual, id_meta))
        self.conn.commit()

    def delete_meta(self, id_meta):
        self.cursor.execute('UPDATE metas SET ativo = 0 WHERE id = ?', (id_meta,))
        self.conn.commit()

    def add_to_meta(self, id_meta, valor):
        self.cursor.execute('UPDATE metas SET valor_atual = valor_atual + ? WHERE id = ?', (valor, id_meta))
        self.conn.commit()