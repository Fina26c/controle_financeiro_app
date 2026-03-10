from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
from datetime import datetime, timedelta
from database import Database
from functools import partial
from telas import TelaSplash, TelaPrincipalScreen
import calendar
import os
import json
import hashlib

# Importações para gráficos
import matplotlib.pyplot as plt
from kivy_garden.matplotlib import FigureCanvasKivyAgg

# Importações para PDF
from fpdf import FPDF

# Importações para configurações e metas
from kivy.uix.checkbox import CheckBox
from kivy.uix.switch import Switch

# Tentar importar bibliotecas de biometria (opcional)
try:
    from android.permissions import Permission, request_permissions
    from android.biometric import BiometricManager
    HAS_BIOMETRIC = True
except:
    HAS_BIOMETRIC = False
    print("⚠️ Módulo de biometria não disponível")

# Cores - Tema Claro (Moderno)
COR_TEXTO = (0, 0, 0, 1)              # Preto
COR_TEXTO_CLARO = (1, 1, 1, 1)        # Branco
COR_TEXTO_SECUNDARIO = (0.3, 0.3, 0.3, 1)  # Cinza escuro
COR_TEXTO_LABEL = (1, 1, 1, 1)        # Branco para labels em fundo escuro

COR_FUNDO_TELA = (0.98, 0.98, 0.98, 1)  # Quase branco
COR_FUNDO_CARD = (0.92, 0.92, 0.92, 1)          # Cinza claro
COR_FUNDO_POPUP = (0.15, 0.15, 0.15, 1)   # Cinza bem escuro para popups
COR_FUNDO_INPUT = (0.25, 0.25, 0.25, 1)   # Cinza médio para inputs

COR_BOTAO_AZUL = (0.2, 0.5, 1, 1)      # Azul vibrante
COR_BOTAO_VERDE = (0.1, 0.7, 0.1, 1)   # Verde
COR_BOTAO_VERMELHO = (1, 0.3, 0.3, 1)  # Vermelho
COR_BOTAO_CINZA = (0.85, 0.85, 0.85, 1) # Cinza claro
COR_BOTAO_AMARELO = (1, 0.8, 0, 1)     # Amarelo

COR_BORDA = (0.3, 0.3, 0.3, 1)         # Cinza escuro para bordas
COR_SEPARADOR = (0.3, 0.3, 0.3, 1)     # Cinza escuro

# Cores para progresso
COR_PROGRESSO_BAIXO = (1, 0.3, 0.3, 1)      # Vermelho
COR_PROGRESSO_MEDIO = (1, 0.8, 0, 1)        # Amarelo
COR_PROGRESSO_ALTO = (0, 0.8, 0, 1)          # Verde
COR_PROGRESSO_CONCLUIDO = (0, 0.6, 1, 1)     # Azul

# Cores para orçamentos
COR_DENTRO = (0, 0.8, 0, 1)                  # Verde
COR_ATENCAO = (1, 0.8, 0, 1)                 # Amarelo
COR_ESTouRO = (1, 0.3, 0.3, 1)               # Vermelho
COR_SEM_ORCAMENTO = (0.5, 0.5, 0.5, 1)       # Cinza

# Cores para segurança
COR_SEGURANCA_ALTA = (0, 0.8, 0, 1)          # Verde
COR_SEGURANCA_MEDIA = (1, 0.8, 0, 1)         # Amarelo
COR_SEGURANCA_BAIXA = (1, 0.3, 0.3, 1)       # Vermelho


class GerenciadorConfiguracoes:
    """Classe para gerenciar as configurações do app"""
    def __init__(self, arquivo='config.json'):
        self.arquivo = arquivo
        self.config_padrao = {
            'tema': 'claro',
            'moeda': 'R$',
            'dia_fechamento': 5,
            'notificacoes': True
        }
        self.config = self.carregar()
    
    def carregar(self):
        """Carrega as configurações do arquivo"""
        if os.path.exists(self.arquivo):
            try:
                with open(self.arquivo, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self.config_padrao.copy()
        else:
            return self.config_padrao.copy()
    
    def salvar(self):
        """Salva as configurações no arquivo"""
        with open(self.arquivo, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
    
    def get(self, chave):
        """Retorna o valor de uma configuração"""
        return self.config.get(chave, self.config_padrao.get(chave))
    
    def set(self, chave, valor):
        """Define o valor de uma configuração"""
        self.config[chave] = valor
        self.salvar()


class GerenciadorSeguranca:
    """Classe para gerenciar a segurança do app (PIN + Biometria)"""
    
    def __init__(self, arquivo='seguranca.json'):
        self.arquivo = arquivo
        self.tentativas = 0
        self.bloqueado_ate = None
        self.config_padrao = {
            'pin_hash': None,
            'pin_ativado': False,
            'biometria_ativada': False,
            'tempo_bloqueio': 5,  # minutos
            'modo_visitante': False,
            'ultimo_acesso': None
        }
        self.config = self.carregar()
    
    def carregar(self):
        """Carrega as configurações de segurança"""
        if os.path.exists(self.arquivo):
            try:
                with open(self.arquivo, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self.config_padrao.copy()
        else:
            return self.config_padrao.copy()
    
    def salvar(self):
        """Salva as configurações de segurança"""
        with open(self.arquivo, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
    
    def _hash_pin(self, pin):
        """Cria hash do PIN para armazenamento seguro"""
        if not pin:
            return None
        return hashlib.sha256(pin.encode()).hexdigest()
    
    def configurar_pin(self, pin, confirmar_pin):
        """Configura um novo PIN"""
        if pin != confirmar_pin:
            return False, "PINs não conferem!"
        
        if len(pin) < 4 or len(pin) > 6:
            return False, "PIN deve ter 4 a 6 dígitos!"
        
        if not pin.isdigit():
            return False, "PIN deve conter apenas números!"
        
        self.config['pin_hash'] = self._hash_pin(pin)
        self.config['pin_ativado'] = True
        self.salvar()
        return True, "PIN configurado com sucesso!"
    
    def verificar_pin(self, pin):
        """Verifica se o PIN está correto"""
        if self.esta_bloqueado():
            return False, f"App bloqueado! Tente novamente em {self.tempo_restante_bloqueio()} segundos."
        
        pin_hash = self._hash_pin(pin)
        
        if pin_hash == self.config['pin_hash']:
            self.tentativas = 0
            self.bloqueado_ate = None
            self.config['ultimo_acesso'] = datetime.now().isoformat()
            self.salvar()
            return True, "PIN correto!"
        else:
            self.tentativas += 1
            if self.tentativas >= 3:
                self.bloqueado_ate = datetime.now() + timedelta(seconds=30)
            
            return False, f"PIN incorreto! Tentativa {self.tentativas}/3"
    
    def alterar_pin(self, pin_atual, pin_novo, confirmar_pin):
        """Altera o PIN atual"""
        # Verificar PIN atual
        if self._hash_pin(pin_atual) != self.config['pin_hash']:
            return False, "PIN atual incorreto!"
        
        # Verificar novo PIN
        if pin_novo != confirmar_pin:
            return False, "PINs novos não conferem!"
        
        if len(pin_novo) < 4 or len(pin_novo) > 6:
            return False, "PIN deve ter 4 a 6 dígitos!"
        
        if not pin_novo.isdigit():
            return False, "PIN deve conter apenas números!"
        
        self.config['pin_hash'] = self._hash_pin(pin_novo)
        self.salvar()
        return True, "PIN alterado com sucesso!"
    
    def desativar_pin(self):
        """Desativa a exigência de PIN"""
        self.config['pin_ativado'] = False
        self.config['pin_hash'] = None
        self.salvar()
        return True, "PIN desativado!"
    
    def esta_bloqueado(self):
        """Verifica se o app está bloqueado"""
        if self.bloqueado_ate and datetime.now() < self.bloqueado_ate:
            return True
        self.bloqueado_ate = None
        return False
    
    def tempo_restante_bloqueio(self):
        """Retorna o tempo restante de bloqueio em segundos"""
        if self.bloqueado_ate:
            resto = (self.bloqueado_ate - datetime.now()).seconds
            return max(resto, 0)
        return 0
    
    def verificar_biometria_disponivel(self):
        """Verifica se biometria está disponível no dispositivo"""
        if not HAS_BIOMETRIC:
            return False, "Biblioteca de biometria não disponível"
        
        try:
            # Tentar verificar disponibilidade
            return True, "Biometria disponível"
        except:
            return False, "Biometria não suportada neste dispositivo"
    
    def ativar_biometria(self, ativar):
        """Ativa ou desativa a biometria"""
        if ativar:
            disponivel, msg = self.verificar_biometria_disponivel()
            if not disponivel:
                return False, msg
        
        self.config['biometria_ativada'] = ativar
        self.salvar()
        return True, f"Biometria {'ativada' if ativar else 'desativada'}!"
    
    def autenticar_biometria(self, callback):
        """Solicita autenticação biométrica"""
        if not self.config['biometria_ativada']:
            callback(False, "Biometria não ativada")
            return
        
        # Simular autenticação biométrica (em dispositivo real, chamaria a API)
        # Por enquanto, vamos simular sucesso após 2 segundos
        Clock.schedule_once(lambda dt: callback(True, "Autenticação biométrica bem-sucedida!"), 2)
    
    def set_tempo_bloqueio(self, minutos):
        """Define o tempo de bloqueio automático"""
        self.config['tempo_bloqueio'] = minutos
        self.salvar()
    
    def set_modo_visitante(self, ativo):
        """Ativa/desativa modo visitante"""
        self.config['modo_visitante'] = ativo
        self.salvar()
    
    def get_status_seguranca(self):
        """Retorna o status atual da segurança"""
        status = {
            'pin_ativado': self.config['pin_ativado'],
            'biometria_ativada': self.config['biometria_ativada'],
            'modo_visitante': self.config['modo_visitante'],
            'tempo_bloqueio': self.config['tempo_bloqueio'],
            'ultimo_acesso': self.config['ultimo_acesso']
        }
        
        # Calcular nível de segurança
        nivel = 0
        if status['pin_ativado']:
            nivel += 1
        if status['biometria_ativada']:
            nivel += 2
        
        if nivel >= 3:
            status['nivel'] = 'ALTO'
            status['cor'] = COR_SEGURANCA_ALTA
        elif nivel >= 1:
            status['nivel'] = 'MÉDIO'
            status['cor'] = COR_SEGURANCA_MEDIA
        else:
            status['nivel'] = 'BAIXO'
            status['cor'] = COR_SEGURANCA_BAIXA
        
        return status


class GerenciadorMetas:
    """Classe para gerenciar as metas financeiras"""
    def __init__(self, db):
        self.db = db
    
    def criar_meta(self, nome, valor_alvo, data_limite):
        """Cria uma nova meta"""
        return self.db.add_meta(nome, valor_alvo, data_limite)
    
    def listar_metas(self):
        """Retorna todas as metas ativas"""
        return self.db.get_metas()
    
    def adicionar_valor(self, id_meta, valor):
        """Adiciona valor à meta"""
        self.db.add_to_meta(id_meta, valor)
    
    def atualizar_valor(self, id_meta, valor_atual):
        """Atualiza o valor atual da meta"""
        self.db.update_meta_valor(id_meta, valor_atual)
    
    def excluir_meta(self, id_meta):
        """Exclui uma meta"""
        self.db.delete_meta(id_meta)
    
    def calcular_progresso(self, valor_atual, valor_alvo):
        """Calcula o percentual de progresso"""
        if valor_alvo <= 0:
            return 0
        return (valor_atual / valor_alvo) * 100


class GerenciadorOrcamentos:
    """Classe para gerenciar os orçamentos por categoria"""
    def __init__(self, db):
        self.db = db
    
    def get_orcamentos_mes(self, mes_ano):
        """Retorna todos os orçamentos do mês com dados de gastos"""
        orcamentos = self.db.get_todos_orcamentos_mes(mes_ano)
        gastos = self.db.get_total_gasto_por_categoria_mes(mes_ano)
        
        resultado = []
        for cat in orcamentos:
            cat_id, cat_nome, cat_cor, limite = cat
            gasto = gastos.get(cat_id, 0)
            percentual = (gasto / limite * 100) if limite > 0 else 0
            
            if limite == 0:
                status = 'sem_orcamento'
            elif percentual >= 100:
                status = 'estouro'
            elif percentual >= 85:
                status = 'atencao'
            else:
                status = 'dentro'
            
            resultado.append({
                'id': cat_id,
                'nome': cat_nome,
                'limite': limite,
                'gasto': gasto,
                'percentual': percentual,
                'status': status,
                'restante': limite - gasto
            })
        
        return resultado
    
    def set_orcamento(self, categoria_id, mes_ano, limite):
        """Define ou atualiza um orçamento"""
        if limite < 0:
            limite = 0
        self.db.set_orcamento(categoria_id, mes_ano, limite)
    
    def get_resumo(self, orcamentos):
        """Calcula resumo dos orçamentos"""
        total_categorias = len([o for o in orcamentos if o['limite'] > 0])
        categorias_estouro = len([o for o in orcamentos if o['status'] == 'estouro'])
        categorias_atencao = len([o for o in orcamentos if o['status'] == 'atencao'])
        
        total_orcado = sum(o['limite'] for o in orcamentos)
        total_gasto = sum(o['gasto'] for o in orcamentos)
        
        return {
            'total_categorias': total_categorias,
            'estouro': categorias_estouro,
            'atencao': categorias_atencao,
            'total_orcado': total_orcado,
            'total_gasto': total_gasto,
            'saldo': total_orcado - total_gasto
        }


class BotaoArredondado(Button):
    """Botão com cantos arredondados"""
    def __init__(self, **kwargs):
        self.bg_color = kwargs.pop('background_color', COR_BOTAO_AZUL)
        self.text_color = kwargs.pop('color', COR_TEXTO_CLARO)
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = self.bg_color
        self.color = self.text_color
        self.bind(pos=self._update, size=self._update)
    
    def _update(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[8])


class BarraProgresso(Widget):
    """Widget personalizado para barra de progresso de metas"""
    def __init__(self, progresso=0, **kwargs):
        super().__init__(**kwargs)
        self.progresso = min(max(progresso, 0), 100)
        self.size_hint_y = None
        self.height = 25
        self.bind(pos=self._draw, size=self._draw)
    
    def _draw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            # Fundo da barra
            Color(0.85, 0.85, 0.85, 1)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[8])
            
            # Cor do progresso baseada no percentual
            if self.progresso >= 100:
                Color(*COR_PROGRESSO_CONCLUIDO)
            elif self.progresso >= 70:
                Color(*COR_PROGRESSO_ALTO)
            elif self.progresso >= 30:
                Color(*COR_PROGRESSO_MEDIO)
            else:
                Color(*COR_PROGRESSO_BAIXO)
            
            # Barra de progresso
            largura_progresso = self.width * (self.progresso / 100)
            if self.progresso > 0:
                RoundedRectangle(
                    pos=self.pos,
                    size=(largura_progresso, self.height),
                    radius=[8, 0, 0, 8] if self.progresso < 100 else [8]
                )
    
    def set_progresso(self, valor):
        """Atualiza o valor da barra de progresso"""
        self.progresso = min(max(valor, 0), 100)
        self._draw()


class BarraProgressoOrcamento(Widget):
    """Widget personalizado para barra de progresso do orçamento"""
    def __init__(self, percentual=0, **kwargs):
        super().__init__(**kwargs)
        self.percentual = min(max(percentual, 0), 100)
        self.size_hint_y = None
        self.height = 18
        self.bind(pos=self._draw, size=self._draw)
    
    def _draw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            # Fundo da barra
            Color(0.85, 0.85, 0.85, 1)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[5])
            
            # Cor baseada no percentual
            if self.percentual >= 100:
                Color(*COR_ESTouRO)
            elif self.percentual >= 85:
                Color(*COR_ATENCAO)
            else:
                Color(*COR_DENTRO)
            
            # Barra de progresso
            largura = self.width * (self.percentual / 100)
            if self.percentual > 0:
                RoundedRectangle(
                    pos=self.pos,
                    size=(largura, self.height),
                    radius=[5, 0, 0, 5] if self.percentual < 100 else [5]
                )


class TelaBloqueio(BoxLayout):
    """Tela de bloqueio do app (com fundo sólido e espaço para logo)"""

    def __init__(self, gerenciador, on_sucesso, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = [30, 30, 30, 30]
        self.spacing = 20

        # Fundo sólido
        with self.canvas.before:
            Color(0.12, 0.12, 0.12, 1)  # Cinza muito escuro
            Rectangle(pos=self.pos, size=self.size)

        self.gerenciador = gerenciador
        self.on_sucesso = on_sucesso
        self.pin_digitado = ""

        self.construir_ui()
        self.verificar_biometria()

    def construir_ui(self):
        # Espaço para logomarca
        logo_box = BoxLayout(orientation='vertical', size_hint_y=0.4, spacing=10)
        with logo_box.canvas.before:
            Color(0.1, 0.2, 0.4, 0.2)  # Azul marinho transparente
            RoundedRectangle(pos=logo_box.pos, size=logo_box.size, radius=[20])
        
        # Verificar se existe arquivo de logo
        caminho_logo = 'images/logo.png'
        if os.path.exists(caminho_logo):
            # Adicionar imagem
            img = Image(
                source=caminho_logo,
                size_hint_y=0.7,
                allow_stretch=True,
                keep_ratio=True
            )
            logo_box.add_widget(img)
        else:
            # Fallback para texto (caso não tenha a imagem)
            logo_box.add_widget(Label(
                text='💰',
                font_size='120sp',
                color=(0.2, 0.4, 0.8, 1)
            ))
        
        # Nome do app
        logo_box.add_widget(Label(
            text='CONTROLE FINANCEIRO',
            font_size='24sp',
            bold=True,
            color=(0.9, 0.9, 0.9, 1),
            size_hint_y=0.2
        ))
        self.add_widget(logo_box)

        # Instrução
        self.instrucao = Label(
            text='Digite seu PIN de acesso',
            font_size='16sp',
            color=(0.8, 0.8, 0.8, 1),
            size_hint_y=0.1
        )
        self.add_widget(self.instrucao)

        # Display do PIN
        self.pin_display = TextInput(
            text='',
            multiline=False,
            password=True,
            password_mask='•',
            font_size='24sp',
            size_hint_y=0.08,
            readonly=True,
            background_color=(0.3, 0.3, 0.3, 1),
            foreground_color=(1, 1, 1, 1)
        )
        self.add_widget(self.pin_display)

        # Teclado numérico
        teclado = GridLayout(cols=3, size_hint_y=0.3, spacing=8, padding=[5, 5, 5, 5])

        for i in range(1, 10):
            btn = BotaoArredondado(
                text=str(i),
                background_color=COR_BOTAO_CINZA,
                color=COR_TEXTO,
                font_size='24sp'
            )
            btn.bind(on_press=lambda x, n=i: self.adicionar_digito(str(n)))
            teclado.add_widget(btn)

        btn_limpar = BotaoArredondado(
            text='⌫',
            background_color=COR_BOTAO_VERMELHO,
            font_size='24sp'
        )
        btn_limpar.bind(on_press=lambda x: self.limpar_ultimo())
        teclado.add_widget(btn_limpar)

        btn_0 = BotaoArredondado(
            text='0',
            background_color=COR_BOTAO_CINZA,
            color=COR_TEXTO,
            font_size='24sp'
        )
        btn_0.bind(on_press=lambda x: self.adicionar_digito('0'))
        teclado.add_widget(btn_0)

        btn_ok = BotaoArredondado(
            text='✓',
            background_color=COR_BOTAO_VERDE,
            font_size='24sp'
        )
        btn_ok.bind(on_press=lambda x: self.verificar_pin())
        teclado.add_widget(btn_ok)

        self.add_widget(teclado)

        # Botão de biometria (se disponível)
        disponivel, msg = self.gerenciador.verificar_biometria_disponivel()
        if disponivel and self.gerenciador.config['biometria_ativada']:
            btn_biometria = BotaoArredondado(
                text='👆 Usar Biometria',
                background_color=COR_BOTAO_AZUL,
                size_hint_y=0.08
            )
            btn_biometria.bind(on_press=self.usar_biometria)
            self.add_widget(btn_biometria)

    def verificar_biometria(self):
        """Verifica se deve solicitar biometria automaticamente"""
        if (self.gerenciador.config['biometria_ativada'] and
            self.gerenciador.verificar_biometria_disponivel()[0]):
            Clock.schedule_once(lambda dt: self.usar_biometria(None), 0.5)

    def adicionar_digito(self, digito):
        """Adiciona dígito ao PIN"""
        if len(self.pin_digitado) < 6:
            self.pin_digitado += digito
            self.pin_display.text = '•' * len(self.pin_digitado)

    def limpar_ultimo(self):
        """Remove o último dígito"""
        self.pin_digitado = self.pin_digitado[:-1]
        self.pin_display.text = '•' * len(self.pin_digitado)

    def limpar_tudo(self):
        """Limpa todo o PIN"""
        self.pin_digitado = ""
        self.pin_display.text = ""

    def verificar_pin(self):
        """Verifica o PIN digitado"""
        if not self.pin_digitado:
            return

        sucesso, msg = self.gerenciador.verificar_pin(self.pin_digitado)

        if sucesso:
            self.on_sucesso()
        else:
            self.instrucao.text = msg
            self.instrucao.color = COR_BOTAO_VERMELHO
            self.limpar_tudo()

            if self.gerenciador.esta_bloqueado():
                self.instrucao.text = f"⏱️ Bloqueado! Aguarde {self.gerenciador.tempo_restante_bloqueio()}s"
                Clock.schedule_once(self.atualizar_contador, 1)

    def atualizar_contador(self, dt):
        """Atualiza o contador de bloqueio"""
        if self.gerenciador.esta_bloqueado():
            resto = self.gerenciador.tempo_restante_bloqueio()
            self.instrucao.text = f"⏱️ Bloqueado! Aguarde {resto}s"
            Clock.schedule_once(self.atualizar_contador, 1)
        else:
            self.instrucao.text = "Digite seu PIN de acesso"
            self.instrucao.color = (0.8, 0.8, 0.8, 1)

    def usar_biometria(self, instance):
        """Solicita autenticação biométrica"""
        self.instrucao.text = "👆 Aguardando biometria..."

        def callback(sucesso, msg):
            if sucesso:
                self.on_sucesso()
            else:
                self.instrucao.text = msg
                self.instrucao.color = COR_BOTAO_VERMELHO

        self.gerenciador.autenticar_biometria(callback)


class ControleFinanceiroApp(App):
    def build(self):
        sm = ScreenManager()
        
        # Adicionar tela de splash
        sm.add_widget(TelaSplash(name='splash'))
        
        # Criar instância da tela principal
        tela_principal = TelaPrincipal()
        
        # Criar Screen que envolve a tela principal
        tela_principal_screen = TelaPrincipalScreen(
            tela_principal_instance=tela_principal,
            name='principal'
        )
        
        # Adicionar ao gerenciador
        sm.add_widget(tela_principal_screen)
        
        # Começar pela splash
        sm.current = 'splash'
        
        return sm


class TelaPrincipal(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = [10, 10, 10, 10]
        self.spacing = 10
        
        # Fundo com efeito de sombra
        with self.canvas.before:
            # Fundo escuro para criar o efeito de sombra
            Color(0.1, 0.1, 0.1, 1)  # Um cinza bem escuro
            Rectangle(pos=self.pos, size=self.size)
            
            # Card principal com fundo claro e bordas arredondadas
            Color(*COR_FUNDO_TELA)
            # Criamos um retângulo um pouco menor que a tela, com bordas arredondadas
            # para dar o efeito de elevação.
            self.rect_fundo_principal = RoundedRectangle(
                pos=(self.x + 5, self.y + 5),  # Pequeno offset para a sombra
                size=(self.width - 10, self.height - 10),
                radius=[15]
            )
        self.bind(pos=self._atualizar_fundo, size=self._atualizar_fundo)
        
        self.db = Database()
        self.config_manager = GerenciadorConfiguracoes()
        self.gerenciador_seguranca = GerenciadorSeguranca()
        self.gerenciador_metas = GerenciadorMetas(self.db)
        self.gerenciador_orcamentos = GerenciadorOrcamentos(self.db)
        self.mes_atual = datetime.now().strftime('%Y-%m')
        
        self.mes_label = None
        self.salario_valor = None
        self.total_pago = None
        self.saldo_valor = None
        self.lista_despesas = None
        
        # Variáveis para configurações
        self.moeda_spinner = None
        self.dia_input = None
        self.notificacoes_check = None
        
        # Variáveis para segurança
        self.biometria_switch = None
        self.visitante_switch = None
        self.tempo_spinner = None
        self.pin_status = None
        self.status_label = None
        
        self.construir_ui()
        self.carregar_dados()
    
    def on_parent(self, widget, parent):
        """Chamado quando a tela é adicionada ao parent (Screen)"""
        if parent and self.gerenciador_seguranca.config['pin_ativado']:
            Clock.schedule_once(self.mostrar_tela_bloqueio, 0.1)
    
    def mostrar_tela_bloqueio(self, dt):
        """Mostra tela de bloqueio substituindo o conteúdo principal"""
        if self.gerenciador_seguranca.config['pin_ativado']:
            # Limpa o layout atual e adiciona a tela de bloqueio
            self.clear_widgets()
            self.add_widget(TelaBloqueio(
                self.gerenciador_seguranca,
                on_sucesso=self.remover_tela_bloqueio
            ))

    def remover_tela_bloqueio(self):
        """Remove a tela de bloqueio e recarrega a interface principal"""
        self.clear_widgets()
        self.construir_ui()
        self.carregar_dados()
    
    def _atualizar_fundo(self, *args):
        # Atualiza o fundo escuro (sombra)
        # O retângulo de fundo escuro não precisa de posição fixa, ele cobre tudo.
        # Vamos apenas atualizar o retângulo principal.
        if hasattr(self, 'rect_fundo_principal'):
            self.rect_fundo_principal.pos = (self.x + 5, self.y + 5)
            self.rect_fundo_principal.size = (self.width - 10, self.height - 10)
    
    def _criar_separador(self):
        sep = BoxLayout(size_hint_y=None, height=1)
        with sep.canvas:
            Color(*COR_SEPARADOR)
            Rectangle(pos=sep.pos, size=sep.size)
        return sep
    
    def _criar_separador_menor(self):
        """Cria um separador mais fino"""
        sep = BoxLayout(size_hint_y=None, height=1)
        with sep.canvas:
            Color(*COR_SEPARADOR)
            Rectangle(pos=sep.pos, size=sep.size)
        return sep
    
    def _atualizar_card(self, instance, *args):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(*COR_FUNDO_CARD)
            RoundedRectangle(pos=instance.pos, size=instance.size, radius=[8])
    
    def _atualizar_card_simples(self, instance, *args):
        """Atualiza o fundo do card (versão simples)"""
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(*COR_FUNDO_CARD)
            RoundedRectangle(pos=instance.pos, size=instance.size, radius=[8])
    
    def construir_ui(self):
        titulo = Label(
            text='CONTROLE FINANCEIRO',
            font_size='26sp',
            bold=True,
            color=(0.2, 0.4, 0.8, 1),
            size_hint_y=0.08
        )
        self.add_widget(titulo)
        self.add_widget(self._criar_separador())
        
        # Navegação de meses
        nav = BoxLayout(size_hint_y=0.09)
        
        btn_esq = BotaoArredondado(
            text='<',
            font_size='40sp',
            background_color=COR_BOTAO_AZUL,
            color=COR_TEXTO_CLARO
        )
        btn_esq.bind(on_press=lambda x: self.mudar_mes(-1))
        nav.add_widget(btn_esq)
        
        self.mes_label = Label(
            text='',
            font_size='25sp',
            bold=True,
            color=COR_TEXTO
        )
        nav.add_widget(self.mes_label)
        
        btn_dir = BotaoArredondado(
            text='>',
            font_size='40sp',
            background_color=COR_BOTAO_AZUL,
            color=COR_TEXTO_CLARO
        )
        btn_dir.bind(on_press=lambda x: self.mudar_mes(1))
        nav.add_widget(btn_dir)
        self.add_widget(nav)
        self.add_widget(self._criar_separador())
        
        # Cards de resumo
        resumo = BoxLayout(size_hint_y=0.18, spacing=10)
        
        # Card Salário
        card_salario = BoxLayout(orientation='vertical', padding=[8, 8, 8, 8])
        with card_salario.canvas.before:
            Color(*COR_FUNDO_CARD)
            RoundedRectangle(pos=card_salario.pos, size=card_salario.size, radius=[10])
        card_salario.bind(pos=self._atualizar_card, size=self._atualizar_card)
        card_salario.add_widget(Label(text='Salário', bold=True, color=COR_TEXTO, size_hint_y=0.3, halign='center'))
        self.salario_valor = Label(text='R$ 0,00', font_size='20sp', bold=True, color=COR_TEXTO, size_hint_y=0.3, halign='center')
        card_salario.add_widget(self.salario_valor)
        btn_editar = BotaoArredondado(text='Editar', size_hint_y=0.2, background_color=COR_BOTAO_AZUL)
        btn_editar.bind(on_press=self.editar_salario)
        card_salario.add_widget(btn_editar)
        resumo.add_widget(card_salario)
        
        # Card Pagas
        card_pagas = BoxLayout(orientation='vertical', padding=[8, 8, 8, 8])
        with card_pagas.canvas.before:
            Color(*COR_FUNDO_CARD)
            RoundedRectangle(pos=card_pagas.pos, size=card_pagas.size, radius=[10])
        card_pagas.bind(pos=self._atualizar_card, size=self._atualizar_card)
        card_pagas.add_widget(Label(text='Pagas', bold=True, color=COR_TEXTO, size_hint_y=0.3, halign='center'))
        self.total_pago = Label(text='R$ 0,00', font_size='20sp', bold=True, color=COR_TEXTO, size_hint_y=0.7, halign='center')
        card_pagas.add_widget(self.total_pago)
        resumo.add_widget(card_pagas)
        
        # Card Saldo
        card_saldo = BoxLayout(orientation='vertical', padding=[8, 8, 8, 8])
        with card_saldo.canvas.before:
            Color(*COR_FUNDO_CARD)
            RoundedRectangle(pos=card_saldo.pos, size=card_saldo.size, radius=[10])
        card_saldo.bind(pos=self._atualizar_card, size=self._atualizar_card)
        card_saldo.add_widget(Label(text='Saldo', bold=True, color=COR_TEXTO, size_hint_y=0.3, halign='center'))
        self.saldo_valor = Label(text='R$ 0,00', font_size='20sp', bold=True, color=COR_TEXTO, size_hint_y=0.7, halign='center')
        card_saldo.add_widget(self.saldo_valor)
        resumo.add_widget(card_saldo)
        
        self.add_widget(resumo)
        self.add_widget(self._criar_separador())
        
        # Lista de despesas
        scroll = ScrollView(size_hint_y=0.56)
        self.lista_despesas = GridLayout(cols=1, size_hint_y=None, spacing=10, padding=[5, 5, 5, 5])
        self.lista_despesas.bind(minimum_height=self.lista_despesas.setter('height'))
        scroll.add_widget(self.lista_despesas)
        self.add_widget(scroll)
        self.add_widget(self._criar_separador())
        
        # Barra inferior
        barra = BoxLayout(size_hint_y=0.08, spacing=10)
        btn_add = BotaoArredondado(text='Adicionar', font_size='18sp', background_color=COR_BOTAO_AZUL)
        btn_add.bind(on_press=self.nova_despesa)
        barra.add_widget(btn_add)
        btn_menu = BotaoArredondado(text='Menu', font_size='18sp', background_color=COR_BOTAO_AZUL)
        btn_menu.bind(on_press=self.abrir_menu)
        barra.add_widget(btn_menu)
        self.add_widget(barra)
    
    def _criar_card_despesa(self, despesa):
        """Cria um card para despesa com botões maiores"""
        card = BoxLayout(orientation='vertical', size_hint_y=None, height=200, padding=[12, 8, 12, 8], spacing=5)
        with card.canvas.before:
            Color(*COR_FUNDO_CARD)
            card.rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[10])
        
        def update_rect(inst, *args):
            inst.rect.pos = inst.pos
            inst.rect.size = inst.size
        card.bind(pos=update_rect, size=update_rect)
        
        # Verificar modo visitante
        ocultar_valores = self.gerenciador_seguranca.config['modo_visitante']
        
        # Linha 1: Descrição e Valor
        linha1 = BoxLayout(orientation='horizontal', size_hint_y=0.25)
        descricao = despesa[1][:25] if despesa[1] else ''
        linha1.add_widget(Label(text=descricao, bold=True, color=COR_TEXTO, halign='left', font_size='18sp'))
        
        if ocultar_valores:
            valor = '🔒 R$ ••••'
        else:
            moeda = self.config_manager.get('moeda')
            valor = f'{moeda} {despesa[2]:.2f}'.replace('.', ',')
        
        linha1.add_widget(Label(text=valor, bold=True, color=COR_TEXTO, halign='right', font_size='18sp'))
        card.add_widget(linha1)
        
        # Linha 2: Categoria e Vencimento
        linha2 = BoxLayout(orientation='horizontal', size_hint_y=0.2)
        categoria = despesa[-2] if despesa[-2] else 'Sem categoria'
        linha2.add_widget(Label(text=f'Categoria: {categoria}', color=(0.5,0.5,0.5,1), halign='left', font_size='12sp'))
        
        if despesa[6]:
            try:
                data_obj = datetime.strptime(despesa[6], '%Y-%m-%d')
                data_venc = data_obj.strftime('%d/%m/%Y')
            except:
                data_venc = f'Vence dia {despesa[5]}' if despesa[5] else ''
        else:
            data_venc = f'Vence dia {despesa[5]}' if despesa[5] else ''
        linha2.add_widget(Label(text=data_venc, color=(0.5,0.5,0.5,1), halign='right', font_size='12sp'))
        card.add_widget(linha2)
        
        # Linha 3: Data de Pagamento (se pago)
        linha3 = BoxLayout(orientation='horizontal', size_hint_y=0.2)
        if despesa[8] == 'pago' and despesa[7]:
            try:
                data_pag = datetime.strptime(despesa[7], '%Y-%m-%d').strftime('%d/%m/%Y')
                linha3.add_widget(Label(text=f'✅ Pago em: {data_pag}', color=COR_BOTAO_VERDE, halign='left', font_size='12sp'))
            except:
                linha3.add_widget(Label(text='✅ Pago', color=COR_BOTAO_VERDE, halign='left', font_size='12sp'))
        else:
            linha3.add_widget(Label(text='', color=(0.5,0.5,0.5,1), halign='left', font_size='12sp'))
        card.add_widget(linha3)
        
        # Linha 4: Botões (MAIORES - 50px de altura)
        linha4 = BoxLayout(orientation='horizontal', size_hint_y=0.3, spacing=15, padding=[0, 5, 0, 0])
        
        if despesa[8] == 'pago':
            btn_pagar = BotaoArredondado(text='Pago', background_color=COR_BOTAO_VERDE, disabled=True, height=50)
            linha4.add_widget(btn_pagar)
        else:
            btn_pagar = BotaoArredondado(text='Pagar', background_color=COR_BOTAO_AZUL, height=50)
            btn_pagar.bind(on_press=partial(self.pagar_despesa_callback, despesa_id=despesa[0]))
            linha4.add_widget(btn_pagar)
        
        btn_excluir = BotaoArredondado(text='Excluir', background_color=COR_BOTAO_VERMELHO, height=50)
        btn_excluir.bind(on_press=partial(self.excluir_despesa_callback, despesa_id=despesa[0]))
        linha4.add_widget(btn_excluir)
        
        card.add_widget(linha4)
        return card
    
    def carregar_dados(self):
        print(f"📊 Carregando dados do mês {self.mes_atual}")
        self.mes_label.text = self.mes_atual
        
        salario = self.db.get_salario(self.mes_atual)
        moeda = self.config_manager.get('moeda')
        ocultar_valores = self.gerenciador_seguranca.config['modo_visitante']
        
        if ocultar_valores:
            self.salario_valor.text = f'{moeda} ••••'
        else:
            self.salario_valor.text = f'{moeda} {salario:.2f}'.replace('.', ',')
        
        despesas = self.db.get_despesas_mes(self.mes_atual)
        print(f"   Despesas encontradas: {len(despesas)}")
        
        self.lista_despesas.clear_widgets()
        
        tipos = {'fixa': '📌 FIXAS', 'parcelada': '💳 PARCELADAS', 'variavel': '🛒 VARIÁVEIS'}
        despesas_por_tipo = {t: [] for t in tipos}
        
        total_pago = 0.0
        
        for d in despesas:
            tipo = d[3]
            despesas_por_tipo[tipo].append(d)
            if d[8] == 'pago':
                total_pago += d[2]
                print(f"   Despesa paga: {d[1]} - R$ {d[2]} em {d[7]}")
        
        print(f"   Total pago: {total_pago}")
        
        for tipo, titulo in tipos.items():
            lista = despesas_por_tipo[tipo]
            if not lista:
                continue
            
            header = Label(text=titulo, bold=True, color=(0.2,0.4,0.8,1), size_hint_y=None, height=35, halign='left', font_size='16sp')
            self.lista_despesas.add_widget(header)
            
            for d in lista:
                card = self._criar_card_despesa(d)
                self.lista_despesas.add_widget(card)
                print(f"   Card criado para despesa ID {d[0]} com status {d[8]}")
        
        if ocultar_valores:
            self.total_pago.text = f'{moeda} ••••'
            self.saldo_valor.text = f'{moeda} ••••'
        else:
            self.total_pago.text = f'{moeda} {total_pago:.2f}'.replace('.', ',')
            self.saldo_valor.text = f'{moeda} {salario - total_pago:.2f}'.replace('.', ',')
        
        print(f"   Saldo atualizado: {self.saldo_valor.text}")
    
    def pagar_despesa_callback(self, instance, despesa_id):
        print(f"\n🔵 Pagar despesa {despesa_id}")
        resultado = self.db.pagar_despesa(despesa_id)
        print(f"   Resultado: {resultado}")
        self.carregar_dados()
    
    def excluir_despesa_callback(self, instance, despesa_id):
        print(f"🔴 Excluir despesa {despesa_id}")
        
        content = BoxLayout(orientation='vertical', spacing=15, padding=20)
        with content.canvas.before:
            Color(*COR_FUNDO_POPUP)
            Rectangle(pos=content.pos, size=content.size)
        
        content.add_widget(Label(text='Excluir esta despesa?', font_size='16sp', color=COR_TEXTO_CLARO))
        
        botoes = BoxLayout(orientation='horizontal', spacing=15, size_hint_y=0.4)
        btn_sim = BotaoArredondado(text='Sim', background_color=COR_BOTAO_VERDE)
        btn_nao = BotaoArredondado(text='Não', background_color=COR_BOTAO_VERMELHO)
        botoes.add_widget(btn_sim)
        botoes.add_widget(btn_nao)
        content.add_widget(botoes)
        
        popup = Popup(
            title='Confirmar',
            content=content,
            size_hint=(0.5, 0.3),
            background_color=COR_FUNDO_POPUP,
            title_color=COR_TEXTO_CLARO
        )
        
        def confirmar(x):
            self.db.excluir_despesa(despesa_id)
            popup.dismiss()
            self.carregar_dados()
        
        btn_sim.bind(on_press=confirmar)
        btn_nao.bind(on_press=popup.dismiss)
        popup.open()
    
    def editar_salario(self, *args):
        popup = Popup(
            title='Editar Salário', 
            size_hint=(0.8, 0.4), 
            background_color=COR_FUNDO_POPUP,
            title_color=COR_TEXTO_CLARO
        )
        box = BoxLayout(orientation='vertical', spacing=15, padding=15)
        with box.canvas.before:
            Color(*COR_FUNDO_POPUP)
            Rectangle(pos=box.pos, size=box.size)
        
        valor_atual = self.db.get_salario(self.mes_atual)
        input_valor = TextInput(
            text=f"{valor_atual:.2f}".replace('.', ','), 
            multiline=False, 
            font_size='18sp', 
            size_hint_y=0.5, 
            foreground_color=COR_TEXTO,
            background_color=COR_FUNDO_INPUT
        )
        box.add_widget(input_valor)
        
        btn_salvar = BotaoArredondado(text='Salvar', background_color=COR_BOTAO_AZUL, size_hint_y=0.3)
        btn_salvar.bind(on_press=lambda x: self._salvar_salario(input_valor.text, popup))
        box.add_widget(btn_salvar)
        
        popup.content = box
        popup.open()
    
    def _salvar_salario(self, valor_texto, popup):
        try:
            valor = float(valor_texto.replace(',', '.'))
            self.db.set_salario(self.mes_atual, valor)
            popup.dismiss()
            self.carregar_dados()
        except:
            erro = Popup(
                title='Erro', 
                content=Label(text='Valor inválido!', color=COR_TEXTO_CLARO), 
                size_hint=(0.6,0.3), 
                background_color=COR_FUNDO_POPUP,
                title_color=COR_TEXTO_CLARO
            )
            erro.open()
    
    def mudar_mes(self, delta):
        ano, mes = map(int, self.mes_atual.split('-'))
        mes += delta
        if mes == 0:
            mes = 12
            ano -= 1
        elif mes == 13:
            mes = 1
            ano += 1
        self.mes_atual = f'{ano:04d}-{mes:02d}'
        self.carregar_dados()
    
    def nova_despesa(self, *args):
        """Popup de nova despesa com parcelas para despesas fixas também"""
        # Carregar categorias para o spinner
        categorias = self.db.get_categorias()
        categorias_nomes = [cat[1] for cat in categorias]
        
        popup = Popup(
            title='Nova Despesa',
            size_hint=(0.95, 0.95),
            background_color=COR_FUNDO_POPUP,
            title_color=COR_TEXTO_CLARO
        )
        
        # Layout principal com fundo escuro
        layout = BoxLayout(orientation='vertical', spacing=15, padding=20)
        with layout.canvas.before:
            Color(*COR_FUNDO_POPUP)
            Rectangle(pos=layout.pos, size=layout.size)
        
        # Título em branco
        layout.add_widget(Label(
            text='CADASTRAR DESPESA',
            font_size='22sp',
            bold=True,
            color=COR_TEXTO_CLARO,
            size_hint_y=0.08
        ))
        
        # Separador
        sep = BoxLayout(size_hint_y=None, height=1)
        with sep.canvas:
            Color(*COR_BORDA)
            Rectangle(pos=sep.pos, size=sep.size)
        layout.add_widget(sep)
        
        # Formulário - todos os textos em branco
        form = BoxLayout(orientation='vertical', spacing=15, size_hint_y=0.7)
        
        # Descrição
        form.add_widget(Label(
            text='Descrição:',
            halign='left',
            color=COR_TEXTO_CLARO,
            size_hint_y=0.08,
            font_size='16sp'
        ))
        descricao = TextInput(
            multiline=False,
            size_hint_y=0.1,
            font_size='16sp',
            foreground_color=COR_TEXTO,
            background_color=COR_FUNDO_INPUT
        )
        form.add_widget(descricao)
        
        # Valor
        form.add_widget(Label(
            text='Valor (R$):',
            halign='left',
            color=COR_TEXTO_CLARO,
            size_hint_y=0.08,
            font_size='16sp'
        ))
        valor = TextInput(
            multiline=False,
            size_hint_y=0.1,
            font_size='16sp',
            foreground_color=COR_TEXTO,
            background_color=COR_FUNDO_INPUT
        )
        form.add_widget(valor)
        
        # Categoria
        form.add_widget(Label(
            text='Categoria:',
            halign='left',
            color=COR_TEXTO_CLARO,
            size_hint_y=0.08,
            font_size='16sp'
        ))
        categoria_spinner = Spinner(
            text='Selecione a categoria',
            values=categorias_nomes,
            size_hint_y=0.1,
            font_size='16sp',
            color=COR_TEXTO_CLARO,
            background_color=COR_FUNDO_INPUT
        )
        form.add_widget(categoria_spinner)
        
        # Tipo
        form.add_widget(Label(
            text='Tipo:',
            halign='left',
            color=COR_TEXTO_CLARO,
            size_hint_y=0.08,
            font_size='16sp'
        ))
        tipo = Spinner(
            text='Fixa',
            values=['Fixa', 'Variável', 'Parcelada'],
            size_hint_y=0.1,
            font_size='16sp',
            color=COR_TEXTO_CLARO,
            background_color=COR_FUNDO_INPUT
        )
        form.add_widget(tipo)
        
        # Dia
        form.add_widget(Label(
            text='Dia de vencimento (1-31):',
            halign='left',
            color=COR_TEXTO_CLARO,
            size_hint_y=0.08,
            font_size='16sp'
        ))
        dia = TextInput(
            multiline=False,
            input_filter='int',
            size_hint_y=0.1,
            font_size='16sp',
            foreground_color=COR_TEXTO,
            background_color=COR_FUNDO_INPUT
        )
        form.add_widget(dia)
        
        # Container para parcelas (SEMPRE VISÍVEL AGORA)
        parcelas_container = BoxLayout(orientation='vertical', size_hint_y=0.2, spacing=5)
        parcelas_container.add_widget(Label(
            text='Número de parcelas/meses:',
            halign='left',
            color=COR_TEXTO_CLARO,
            size_hint_y=0.3,
            font_size='16sp'
        ))
        parcelas_input = TextInput(
            text='1',  # Valor padrão
            multiline=False,
            input_filter='int',
            size_hint_y=0.7,
            font_size='16sp',
            foreground_color=COR_TEXTO,
            background_color=COR_FUNDO_INPUT
        )
        parcelas_container.add_widget(parcelas_input)
        form.add_widget(parcelas_container)
        
        # Função para alterar o texto do campo de parcelas baseado no tipo
        def on_tipo_selecionado(spinner, text):
            if text == 'Variável':
                parcelas_input.text = '1'
                parcelas_input.disabled = True
                # Muda a cor para indicar que está desabilitado (opcional)
                parcelas_input.background_color = (0.3, 0.3, 0.3, 1)
            else:
                parcelas_input.disabled = False
                parcelas_input.background_color = COR_FUNDO_INPUT
                if text == 'Fixa':
                    # Sugere 12 parcelas para despesas fixas, mas permite editar
                    parcelas_input.text = '12'
                elif text == 'Parcelada':
                    # Sugere 3 parcelas, mas permite editar
                    parcelas_input.text = '3'
        
        tipo.bind(text=on_tipo_selecionado)
        # Chamar a função uma vez para configurar o estado inicial
        on_tipo_selecionado(tipo, tipo.text)
        
        layout.add_widget(form)
        
        # Espaçador
        layout.add_widget(Widget(size_hint_y=0.05))
        
        # Separador
        sep2 = BoxLayout(size_hint_y=None, height=1)
        with sep2.canvas:
            Color(*COR_BORDA)
            Rectangle(pos=sep2.pos, size=sep2.size)
        layout.add_widget(sep2)
        
        # Botões
        botoes = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=20, padding=[10, 0, 10, 0])
        
        btn_salvar = BotaoArredondado(
            text='💾 Salvar',
            background_color=COR_BOTAO_VERDE,
            font_size='16sp',
            height=50
        )
        
        btn_cancelar = BotaoArredondado(
            text='❌ Cancelar',
            background_color=COR_BOTAO_VERMELHO,
            font_size='16sp',
            height=50
        )
        btn_cancelar.bind(on_press=popup.dismiss)
        
        botoes.add_widget(btn_salvar)
        botoes.add_widget(btn_cancelar)
        layout.add_widget(botoes)
        
        popup.content = layout
        
        def salvar(*args):
            # Validações
            if not descricao.text or not valor.text or not dia.text:
                erro = Popup(
                    title='Erro',
                    content=Label(text='Preencha todos os campos obrigatórios!', color=COR_TEXTO_CLARO),
                    size_hint=(0.7,0.3),
                    background_color=COR_FUNDO_POPUP,
                    title_color=COR_TEXTO_CLARO
                )
                erro.open()
                return
            
            if categoria_spinner.text == 'Selecione a categoria':
                erro = Popup(
                    title='Erro',
                    content=Label(text='Selecione uma categoria!', color=COR_TEXTO_CLARO),
                    size_hint=(0.6,0.3),
                    background_color=COR_FUNDO_POPUP,
                    title_color=COR_TEXTO_CLARO
                )
                erro.open()
                return
            
            try:
                v = float(valor.text.replace(',', '.'))
                if v <= 0:
                    erro = Popup(
                        title='Erro',
                        content=Label(text='Valor deve ser positivo!', color=COR_TEXTO_CLARO),
                        size_hint=(0.6,0.3),
                        background_color=COR_FUNDO_POPUP,
                        title_color=COR_TEXTO_CLARO
                    )
                    erro.open()
                    return
                
                d = int(dia.text)
                if d < 1 or d > 31:
                    erro = Popup(
                        title='Erro',
                        content=Label(text='Dia deve ser entre 1 e 31!', color=COR_TEXTO_CLARO),
                        size_hint=(0.6,0.3),
                        background_color=COR_FUNDO_POPUP,
                        title_color=COR_TEXTO_CLARO
                    )
                    erro.open()
                    return
                
                # Obter ID da categoria selecionada
                categoria_id = None
                for cat in categorias:
                    if cat[1] == categoria_spinner.text:
                        categoria_id = cat[0]
                        break
                
                # Processar parcelas (para todos os tipos, exceto variável)
                if tipo.text == 'Variável':
                    parcelas = 1
                else:
                    try:
                        parcelas = int(parcelas_input.text) if parcelas_input.text else 1
                        if parcelas < 1 or parcelas > 60:
                            erro = Popup(
                                title='Erro',
                                content=Label(text='Parcelas deve ser entre 1 e 60!', color=COR_TEXTO_CLARO),
                                size_hint=(0.7,0.3),
                                background_color=COR_FUNDO_POPUP,
                                title_color=COR_TEXTO_CLARO
                            )
                            erro.open()
                            return
                    except:
                        erro = Popup(
                            title='Erro',
                            content=Label(text='Número de parcelas inválido!', color=COR_TEXTO_CLARO),
                            size_hint=(0.7,0.3),
                            background_color=COR_FUNDO_POPUP,
                            title_color=COR_TEXTO_CLARO
                        )
                        erro.open()
                        return
                
                tipo_map = {'Fixa': 'fixa', 'Variável': 'variavel', 'Parcelada': 'parcelada'}
                
                # Adicionar despesa (a lógica de parcelas está DENTRO do método add_despesa do banco de dados)
                self.db.add_despesa(
                    descricao.text, v, tipo_map[tipo.text],
                    self.mes_atual, d, parcelas, categoria_id
                )
                
                popup.dismiss()
                self.carregar_dados()
                
                # Mensagem de sucesso
                sucesso = Popup(
                    title='Sucesso',
                    content=Label(text='✅ Despesa cadastrada com sucesso!', color=COR_TEXTO_CLARO),
                    size_hint=(0.6, 0.3),
                    background_color=COR_FUNDO_POPUP,
                    title_color=COR_TEXTO_CLARO
                )
                sucesso.open()
                
            except Exception as e:
                erro = Popup(
                    title='Erro',
                    content=Label(text=f'Erro: {str(e)}', color=COR_TEXTO_CLARO),
                    size_hint=(0.7,0.3),
                    background_color=COR_FUNDO_POPUP,
                    title_color=COR_TEXTO_CLARO
                )
                erro.open()
        
        btn_salvar.bind(on_press=salvar)
        popup.open()
    
    def abrir_menu(self, *args):
        popup = Popup(
            title='Menu', 
            size_hint=(0.85, 0.8), 
            background_color=COR_FUNDO_POPUP,
            title_color=COR_TEXTO_CLARO
        )
        
        layout = BoxLayout(orientation='vertical', spacing=15, padding=20)
        with layout.canvas.before:
            Color(*COR_FUNDO_POPUP)
            Rectangle(pos=layout.pos, size=layout.size)
        
        layout.add_widget(Label(
            text='OPÇÕES',
            font_size='22sp',
            bold=True,
            color=COR_TEXTO_CLARO,
            size_hint_y=0.1
        ))
        
        sep = BoxLayout(size_hint_y=None, height=1)
        with sep.canvas:
            Color(*COR_BORDA)
            Rectangle(pos=sep.pos, size=sep.size)
        layout.add_widget(sep)
        
        itens = [
            ('📊 Gráficos', self.abrir_graficos),
            ('📄 Relatórios', self.abrir_relatorios),
            ('💾 Backup', self.abrir_backup),
            ('⚙️ Configurações', self.abrir_configuracoes),
            ('🏷️ Categorias', self.gerenciar_categorias),
            ('💰 Orçamentos', self.abrir_orcamentos),
            ('🎯 Metas', self.abrir_metas),
            ('🔐 Segurança', self.abrir_seguranca)
        ]
        
        for texto, funcao in itens:
            btn = BotaoArredondado(
                text=texto,
                background_color=COR_BOTAO_CINZA,
                color=COR_TEXTO,
                size_hint_y=None,
                height=120
            )
            btn.bind(on_press=lambda x, f=funcao: (popup.dismiss(), f()))
            layout.add_widget(btn)
        
        layout.add_widget(Widget(size_hint_y=0.1))
        
        btn_fechar = BotaoArredondado(
            text='Fechar',
            background_color=COR_BOTAO_VERMELHO,
            size_hint_y=0.1
        )
        btn_fechar.bind(on_press=popup.dismiss)
        layout.add_widget(btn_fechar)
        
        popup.content = layout
        popup.open()
    
    # ---------- CONFIGURAÇÕES (SEM OPÇÃO DE TEMA) ----------
    
    def abrir_configuracoes(self, *args):
        """Abre a tela de configurações (sem opção de tema)"""
        popup = Popup(
            title='Configurações',
            size_hint=(0.95, 0.9),
            background_color=COR_FUNDO_POPUP,
            title_color=COR_TEXTO_CLARO
        )
        
        # Layout principal
        layout = BoxLayout(orientation='vertical', spacing=10, padding=15)
        with layout.canvas.before:
            Color(*COR_FUNDO_POPUP)
            Rectangle(pos=layout.pos, size=layout.size)
        
        # Título
        titulo = Label(
            text='⚙️ CONFIGURAÇÕES',
            font_size='22sp',
            bold=True,
            color=COR_TEXTO_CLARO,
            size_hint_y=0.08
        )
        layout.add_widget(titulo)
        layout.add_widget(self._criar_separador_menor())
        
        # ScrollView para as opções
        scroll = ScrollView(size_hint_y=0.8)
        grid = GridLayout(cols=1, size_hint_y=None, spacing=12, padding=[5, 5, 5, 5])
        grid.bind(minimum_height=grid.setter('height'))
        
        # Opção 1: Moeda
        grid.add_widget(self._criar_opcao_moeda())
        
        # Opção 2: Dia de fechamento (MELHORADA)
        grid.add_widget(self._criar_opcao_fechamento_melhorada())
        
        # Opção 3: Notificações
        grid.add_widget(self._criar_opcao_notificacoes())
        
        # Informações adicionais
        info_card = BoxLayout(orientation='vertical', size_hint_y=None, height=120, padding=10)
        with info_card.canvas.before:
            Color(0.9, 0.9, 0.9, 1)
            RoundedRectangle(pos=info_card.pos, size=info_card.size, radius=[8])
        info_card.bind(pos=self._atualizar_card_simples, size=self._atualizar_card_simples)
        
        info_card.add_widget(Label(
            text='ℹ️ As configurações são salvas automaticamente',
            color=(0.5,0.5,0.5,1),
            font_size='12sp'
        ))
        grid.add_widget(info_card)
        
        # Botões de ação
        botoes = BoxLayout(orientation='horizontal', size_hint_y=None, height=100, spacing=10)
        btn_fechar = BotaoArredondado(
            text='Fechar',
            background_color=COR_BOTAO_VERMELHO
        )
        btn_fechar.bind(on_press=popup.dismiss)
        
        botoes.add_widget(Widget())  # Espaçador
        botoes.add_widget(btn_fechar)
        botoes.add_widget(Widget())  # Espaçador
        
        grid.add_widget(botoes)
        
        scroll.add_widget(grid)
        layout.add_widget(scroll)
        
        popup.content = layout
        popup.open()
    
    def _criar_opcao_moeda(self):
        """Card para configuração de moeda"""
        card = BoxLayout(orientation='vertical', size_hint_y=None, height=120, padding=12, spacing=5)
        with card.canvas.before:
            Color(*COR_FUNDO_CARD)
            RoundedRectangle(pos=card.pos, size=card.size, radius=[10])
        card.bind(pos=self._atualizar_card_simples, size=self._atualizar_card_simples)
        
        card.add_widget(Label(
            text='💰 Moeda',
            bold=True,
            color=COR_TEXTO,
            halign='left',
            font_size='16sp',
            size_hint_y=0.3
        ))
        
        linha = BoxLayout(orientation='horizontal', size_hint_y=0.7, spacing=10)
        linha.add_widget(Label(text='Selecione a moeda:', color=COR_TEXTO, halign='left'))
        
        self.moeda_spinner = Spinner(
            text=self.config_manager.get('moeda'),
            values=['R$', 'US$', '€'],
            size_hint_x=0.5,
            color=COR_TEXTO
        )
        self.moeda_spinner.bind(text=self._salvar_moeda)
        linha.add_widget(self.moeda_spinner)
        
        card.add_widget(linha)
        return card
    
    def _criar_opcao_fechamento_melhorada(self):
        """Card para configuração do dia de fechamento (MELHORADO - 200px)"""
        card = BoxLayout(orientation='vertical', size_hint_y=None, height=200, padding=15, spacing=8)
        with card.canvas.before:
            Color(*COR_FUNDO_CARD)
            RoundedRectangle(pos=card.pos, size=card.size, radius=[10])
        card.bind(pos=self._atualizar_card_simples, size=self._atualizar_card_simples)
        
        # Título
        card.add_widget(Label(
            text='📅 Dia de Fechamento',
            bold=True,
            color=COR_TEXTO,
            halign='left',
            font_size='16sp',
            size_hint_y=0.2
        ))
        
        # Descrição
        card.add_widget(Label(
            text='O saldo será calculado a partir deste dia',
            color=(0.5,0.5,0.5,1),
            halign='left',
            font_size='12sp',
            size_hint_y=0.15
        ))
        
        # Linha de configuração
        linha = BoxLayout(orientation='horizontal', size_hint_y=0.4, spacing=15, padding=[0, 5, 0, 5])
        
        # Label e input
        linha_input = BoxLayout(orientation='horizontal', size_hint_x=0.6, spacing=5)
        linha_input.add_widget(Label(text='Dia:', color=COR_TEXTO, halign='right', size_hint_x=0.3))
        self.dia_input = TextInput(
            text=str(self.config_manager.get('dia_fechamento')),
            multiline=False,
            input_filter='int',
            size_hint_x=0.7,
            height=40,
            foreground_color=COR_TEXTO
        )
        linha_input.add_widget(self.dia_input)
        linha.add_widget(linha_input)
        
        # Botão salvar
        btn_salvar = BotaoArredondado(
            text='Salvar',
            background_color=COR_BOTAO_VERDE,
            size_hint_x=0.35,
            height=45
        )
        btn_salvar.bind(on_press=self._salvar_dia_fechamento)
        linha.add_widget(btn_salvar)
        
        card.add_widget(linha)
        
        # Espaçador
        card.add_widget(Widget(size_hint_y=0.1))
        return card
    
    def _criar_opcao_notificacoes(self):
        """Card para configuração de notificações"""
        card = BoxLayout(orientation='vertical', size_hint_y=None, height=120, padding=12, spacing=5)
        with card.canvas.before:
            Color(*COR_FUNDO_CARD)
            RoundedRectangle(pos=card.pos, size=card.size, radius=[10])
        card.bind(pos=self._atualizar_card_simples, size=self._atualizar_card_simples)
        
        card.add_widget(Label(
            text='🔔 Notificações',
            bold=True,
            color=COR_TEXTO,
            halign='left',
            font_size='16sp',
            size_hint_y=0.3
        ))
        
        linha = BoxLayout(orientation='horizontal', size_hint_y=0.7, spacing=10)
        linha.add_widget(Label(text='Receber notificações:', color=COR_TEXTO, halign='left'))
        
        self.notificacoes_check = CheckBox(active=self.config_manager.get('notificacoes'))
        self.notificacoes_check.bind(active=self._salvar_notificacoes)
        linha.add_widget(self.notificacoes_check)
        
        card.add_widget(linha)
        return card
    
    def _salvar_moeda(self, spinner, text):
        """Salva a configuração de moeda"""
        self.config_manager.set('moeda', text)
        self.carregar_dados()  # Atualiza a tela com a nova moeda
    
    def _salvar_dia_fechamento(self, *args):
        """Salva apenas o dia de fechamento"""
        try:
            dia = int(self.dia_input.text)
            if dia < 1 or dia > 31:
                raise ValueError
            self.config_manager.set('dia_fechamento', dia)
            self._mostrar_mensagem_sucesso("Dia de fechamento salvo!")
        except:
            self._mostrar_erro("Dia deve ser entre 1 e 31!")
    
    def _salvar_notificacoes(self, checkbox, value):
        """Salva apenas as configurações de notificações"""
        self.config_manager.set('notificacoes', value)
    
    def _mostrar_mensagem_sucesso(self, mensagem):
        """Mostra popup de sucesso"""
        popup = Popup(
            title='Sucesso',
            content=Label(text=f'✅ {mensagem}', color=COR_TEXTO_CLARO),
            size_hint=(0.6, 0.3),
            background_color=COR_FUNDO_POPUP,
            title_color=COR_TEXTO_CLARO
        )
        popup.open()
    
    def _mostrar_erro(self, mensagem):
        """Mostra popup de erro"""
        popup = Popup(
            title='Erro',
            content=Label(text=f'❌ {mensagem}', color=COR_TEXTO_CLARO),
            size_hint=(0.6, 0.3),
            background_color=COR_FUNDO_POPUP,
            title_color=COR_TEXTO_CLARO
        )
        popup.open()
    
    # ---------- SEGURANÇA (INTEGRADA E CORRIGIDA) ----------
    
    def abrir_seguranca(self, *args):
        """Abre a tela de configurações de segurança"""
        popup = Popup(
            title='🔐 Segurança',
            size_hint=(0.95, 0.9),
            background_color=COR_FUNDO_POPUP,
            title_color=COR_TEXTO_CLARO
        )
        
        # Layout principal
        layout = BoxLayout(orientation='vertical', spacing=12, padding=15)
        with layout.canvas.before:
            Color(*COR_FUNDO_POPUP)
            Rectangle(pos=layout.pos, size=layout.size)
        
        # Título
        titulo = Label(
            text='🔐 SEGURANÇA',
            font_size='24sp',
            bold=True,
            color=COR_TEXTO_CLARO,
            size_hint_y=0.08
        )
        layout.add_widget(titulo)
        layout.add_widget(self._criar_separador_menor())
        
        # Status de segurança
        status_card = BoxLayout(orientation='vertical', size_hint_y=0.12, padding=12, spacing=5)
        with status_card.canvas.before:
            Color(*COR_FUNDO_CARD)
            RoundedRectangle(pos=status_card.pos, size=status_card.size, radius=[8])
        status_card.bind(pos=self._atualizar_card, size=self._atualizar_card)
        
        status = self.gerenciador_seguranca.get_status_seguranca()
        self.status_label = Label(
            text=f"🔒 Nível de Segurança: {status['nivel']}",
            font_size='14sp',
            color=status['cor'],
            halign='center'
        )
        status_card.add_widget(self.status_label)
        layout.add_widget(status_card)
        
        layout.add_widget(self._criar_separador_menor())
        
        # ScrollView para as opções
        scroll = ScrollView(size_hint_y=0.7)
        grid = GridLayout(cols=1, size_hint_y=None, spacing=12, padding=[2, 2, 2, 2])
        grid.bind(minimum_height=grid.setter('height'))
        
        # Opção 1: Configurar PIN
        card_pin = BoxLayout(orientation='vertical', size_hint_y=None, height=180, padding=12, spacing=8)
        with card_pin.canvas.before:
            Color(*COR_FUNDO_CARD)
            card_pin.rect = RoundedRectangle(pos=card_pin.pos, size=card_pin.size, radius=[8])
        card_pin.bind(pos=self._atualizar_card, size=self._atualizar_card)
        
        card_pin.add_widget(Label(
            text='🔢 PIN de Acesso',
            bold=True,
            color=COR_TEXTO,
            halign='left',
            font_size='16sp',
            size_hint_y=0.2
        ))
        
        # Status do PIN
        self.pin_status = Label(
            text='✅ PIN ativo' if self.gerenciador_seguranca.config['pin_ativado'] else '⚠️ PIN não configurado',
            color=COR_SEGURANCA_ALTA if self.gerenciador_seguranca.config['pin_ativado'] else COR_SEGURANCA_BAIXA,
            font_size='12sp',
            size_hint_y=0.15
        )
        card_pin.add_widget(self.pin_status)
        
        # Botões
        botoes_pin = BoxLayout(orientation='horizontal', size_hint_y=0.45, spacing=10)
        
        if self.gerenciador_seguranca.config['pin_ativado']:
            btn_alterar = BotaoArredondado(
                text='🔄 Alterar PIN',
                background_color=COR_BOTAO_AZUL,
                height=45
            )
            btn_alterar.bind(on_press=self.alterar_pin)
            botoes_pin.add_widget(btn_alterar)
            
            btn_desativar = BotaoArredondado(
                text='🔓 Desativar',
                background_color=COR_BOTAO_VERMELHO,
                height=45
            )
            btn_desativar.bind(on_press=self.desativar_pin)
            botoes_pin.add_widget(btn_desativar)
        else:
            btn_configurar = BotaoArredondado(
                text='🔐 Configurar PIN',
                background_color=COR_BOTAO_VERDE,
                height=45
            )
            btn_configurar.bind(on_press=self.configurar_pin)
            botoes_pin.add_widget(btn_configurar)
        
        card_pin.add_widget(botoes_pin)
        grid.add_widget(card_pin)
        
        # Opção 2: Biometria
        card_biometria = BoxLayout(orientation='vertical', size_hint_y=None, height=120, padding=12, spacing=8)
        with card_biometria.canvas.before:
            Color(*COR_FUNDO_CARD)
            card_biometria.rect = RoundedRectangle(pos=card_biometria.pos, size=card_biometria.size, radius=[8])
        card_biometria.bind(pos=self._atualizar_card, size=self._atualizar_card)
        
        card_biometria.add_widget(Label(
            text='👆 Autenticação Biométrica',
            bold=True,
            color=COR_TEXTO,
            halign='left',
            font_size='16sp',
            size_hint_y=0.3
        ))
        
        disponivel, msg = self.gerenciador_seguranca.verificar_biometria_disponivel()
        
        if disponivel:
            linha_biometria = BoxLayout(orientation='horizontal', size_hint_y=0.5, spacing=10)
            linha_biometria.add_widget(Label(
                text='Ativar biometria:',
                color=COR_TEXTO
            ))
            
            self.biometria_switch = Switch(active=self.gerenciador_seguranca.config['biometria_ativada'])
            self.biometria_switch.bind(active=self.toggle_biometria)
            linha_biometria.add_widget(self.biometria_switch)
            
            card_biometria.add_widget(linha_biometria)
        else:
            card_biometria.add_widget(Label(
                text='❌ Biometria não disponível',
                color=COR_BOTAO_VERMELHO,
                size_hint_y=0.5
            ))
        
        grid.add_widget(card_biometria)
        
        # Opção 3: Tempo de bloqueio
        card_tempo = BoxLayout(orientation='vertical', size_hint_y=None, height=120, padding=12, spacing=8)
        with card_tempo.canvas.before:
            Color(*COR_FUNDO_CARD)
            card_tempo.rect = RoundedRectangle(pos=card_tempo.pos, size=card_tempo.size, radius=[8])
        card_tempo.bind(pos=self._atualizar_card, size=self._atualizar_card)
        
        card_tempo.add_widget(Label(
            text='⏱️ Bloqueio Automático',
            bold=True,
            color=COR_TEXTO,
            halign='left',
            font_size='16sp',
            size_hint_y=0.3
        ))
        
        linha_tempo = BoxLayout(orientation='horizontal', size_hint_y=0.5, spacing=10)
        linha_tempo.add_widget(Label(text='Bloquear após:', color=COR_TEXTO))
        
        self.tempo_spinner = Spinner(
            text=f"{self.gerenciador_seguranca.config['tempo_bloqueio']} min",
            values=['1 min', '2 min', '5 min', '10 min', '15 min', '30 min'],
            size_hint_x=0.5,
            color=COR_TEXTO
        )
        self.tempo_spinner.bind(text=self.mudar_tempo_bloqueio)
        linha_tempo.add_widget(self.tempo_spinner)
        
        card_tempo.add_widget(linha_tempo)
        grid.add_widget(card_tempo)
        
        # Opção 4: Modo Visitante
        card_visitante = BoxLayout(orientation='vertical', size_hint_y=None, height=200, padding=12, spacing=8)
        with card_visitante.canvas.before:
            Color(*COR_FUNDO_CARD)
            card_visitante.rect = RoundedRectangle(pos=card_visitante.pos, size=card_visitante.size, radius=[8])
        card_visitante.bind(pos=self._atualizar_card, size=self._atualizar_card)
        
        card_visitante.add_widget(Label(
            text='👤 Modo Visitante',
            bold=True,
            color=COR_TEXTO,
            halign='left',
            font_size='16sp',
            size_hint_y=0.3
        ))
        
        card_visitante.add_widget(Label(
            text='Oculta valores sensíveis (R$)',
            color=(0.5,0.5,0.5,1),
            font_size='12sp',
            size_hint_y=0.2
        ))
        
        linha_visitante = BoxLayout(orientation='horizontal', size_hint_y=0.4, spacing=10)
        linha_visitante.add_widget(Label(text='Ativar modo visitante:', color=COR_TEXTO))
        
        self.visitante_switch = Switch(active=self.gerenciador_seguranca.config['modo_visitante'])
        self.visitante_switch.bind(active=self.toggle_visitante)
        linha_visitante.add_widget(self.visitante_switch)
        
        card_visitante.add_widget(linha_visitante)
        grid.add_widget(card_visitante)
        
        # Informações adicionais
        info_card = BoxLayout(orientation='vertical', size_hint_y=None, height=60, padding=8)
        with info_card.canvas.before:
            Color(0.9, 0.9, 0.9, 1)
            RoundedRectangle(pos=info_card.pos, size=info_card.size, radius=[8])
        
        info_card.add_widget(Label(
            text='ℹ️ Após 3 tentativas erradas, app bloqueia por 30s',
            color=(0.5,0.5,0.5,1),
            font_size='11sp'
        ))
        grid.add_widget(info_card)
        
        scroll.add_widget(grid)
        layout.add_widget(scroll)
        
        # Botão voltar
        btn_voltar = BotaoArredondado(
            text='🔙 Voltar',
            background_color=COR_BOTAO_VERMELHO,
            size_hint_y=0.08,
            height=45
        )
        btn_voltar.bind(on_press=popup.dismiss)
        layout.add_widget(btn_voltar)
        
        popup.content = layout
        popup.open()
    
    def configurar_pin(self, *args):
        """Popup para configurar novo PIN"""
        layout = BoxLayout(orientation='vertical', spacing=12, padding=15)
        with layout.canvas.before:
            Color(*COR_FUNDO_POPUP)
            Rectangle(pos=layout.pos, size=layout.size)
        
        layout.add_widget(Label(
            text='🔢 CONFIGURAR PIN',
            font_size='18sp',
            bold=True,
            color=COR_TEXTO_CLARO,
            size_hint_y=0.15
        ))
        
        layout.add_widget(Label(text='Digite o PIN (4-6 dígitos):', color=COR_TEXTO_CLARO))
        pin1 = TextInput(
            multiline=False,
            password=True,
            password_mask='•',
            font_size='18sp',
            input_filter='int',
            foreground_color=COR_TEXTO,
            background_color=COR_FUNDO_INPUT,
            size_hint_y=0.15
        )
        layout.add_widget(pin1)
        
        layout.add_widget(Label(text='Confirme o PIN:', color=COR_TEXTO_CLARO))
        pin2 = TextInput(
            multiline=False,
            password=True,
            password_mask='•',
            font_size='18sp',
            input_filter='int',
            foreground_color=COR_TEXTO,
            background_color=COR_FUNDO_INPUT,
            size_hint_y=0.15
        )
        layout.add_widget(pin2)
        
        botoes = BoxLayout(orientation='horizontal', size_hint_y=0.2, spacing=10)
        btn_salvar = BotaoArredondado(text='Salvar', background_color=COR_BOTAO_VERDE)
        btn_cancelar = BotaoArredondado(text='Cancelar', background_color=COR_BOTAO_VERMELHO)
        botoes.add_widget(btn_salvar)
        botoes.add_widget(btn_cancelar)
        layout.add_widget(botoes)
        
        popup = Popup(
            title='Configurar PIN',
            content=layout,
            size_hint=(0.85, 0.5),
            background_color=COR_FUNDO_POPUP,
            title_color=COR_TEXTO_CLARO
        )
        
        def salvar(*args):
            sucesso, msg = self.gerenciador_seguranca.configurar_pin(pin1.text, pin2.text)
            if sucesso:
                popup.dismiss()
                self.pin_status.text = "✅ PIN ativo"
                self.pin_status.color = COR_SEGURANCA_ALTA
                self._mostrar_mensagem_sucesso(msg)
            else:
                self._mostrar_erro(msg)
        
        btn_salvar.bind(on_press=salvar)
        btn_cancelar.bind(on_press=popup.dismiss)
        popup.open()
    
    def alterar_pin(self, *args):
        """Popup para alterar PIN"""
        layout = BoxLayout(orientation='vertical', spacing=12, padding=15)
        with layout.canvas.before:
            Color(*COR_FUNDO_POPUP)
            Rectangle(pos=layout.pos, size=layout.size)
        
        layout.add_widget(Label(
            text='🔄 ALTERAR PIN',
            font_size='18sp',
            bold=True,
            color=COR_TEXTO_CLARO,
            size_hint_y=0.15
        ))
        
        layout.add_widget(Label(text='PIN atual:', color=COR_TEXTO_CLARO))
        pin_atual = TextInput(
            multiline=False,
            password=True,
            password_mask='•',
            font_size='18sp',
            input_filter='int',
            foreground_color=COR_TEXTO,
            background_color=COR_FUNDO_INPUT,
            size_hint_y=0.15
        )
        layout.add_widget(pin_atual)
        
        layout.add_widget(Label(text='Novo PIN (4-6 dígitos):', color=COR_TEXTO_CLARO))
        pin_novo = TextInput(
            multiline=False,
            password=True,
            password_mask='•',
            font_size='18sp',
            input_filter='int',
            foreground_color=COR_TEXTO,
            background_color=COR_FUNDO_INPUT,
            size_hint_y=0.15
        )
        layout.add_widget(pin_novo)
        
        layout.add_widget(Label(text='Confirme novo PIN:', color=COR_TEXTO_CLARO))
        pin_confirmar = TextInput(
            multiline=False,
            password=True,
            password_mask='•',
            font_size='18sp',
            input_filter='int',
            foreground_color=COR_TEXTO,
            background_color=COR_FUNDO_INPUT,
            size_hint_y=0.15
        )
        layout.add_widget(pin_confirmar)
        
        botoes = BoxLayout(orientation='horizontal', size_hint_y=0.2, spacing=10)
        btn_salvar = BotaoArredondado(text='Alterar', background_color=COR_BOTAO_VERDE)
        btn_cancelar = BotaoArredondado(text='Cancelar', background_color=COR_BOTAO_VERMELHO)
        botoes.add_widget(btn_salvar)
        botoes.add_widget(btn_cancelar)
        layout.add_widget(botoes)
        
        popup = Popup(
            title='Alterar PIN',
            content=layout,
            size_hint=(0.85, 0.6),
            background_color=COR_FUNDO_POPUP,
            title_color=COR_TEXTO_CLARO
        )
        
        def salvar(*args):
            sucesso, msg = self.gerenciador_seguranca.alterar_pin(pin_atual.text, pin_novo.text, pin_confirmar.text)
            if sucesso:
                popup.dismiss()
                self._mostrar_mensagem_sucesso(msg)
            else:
                self._mostrar_erro(msg)
        
        btn_salvar.bind(on_press=salvar)
        btn_cancelar.bind(on_press=popup.dismiss)
        popup.open()
    
    def desativar_pin(self, *args):
        """Confirma desativação do PIN"""
        content = BoxLayout(orientation='vertical', spacing=12, padding=15)
        with content.canvas.before:
            Color(*COR_FUNDO_POPUP)
            Rectangle(pos=content.pos, size=content.size)
        
        content.add_widget(Label(
            text='Desativar PIN?',
            font_size='16sp',
            color=COR_TEXTO_CLARO
        ))
        content.add_widget(Label(
            text='O app ficará sem proteção!',
            color=COR_BOTAO_VERMELHO,
            font_size='14sp'
        ))
        
        botoes = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.4)
        btn_sim = BotaoArredondado(text='Sim', background_color=COR_BOTAO_VERDE)
        btn_nao = BotaoArredondado(text='Não', background_color=COR_BOTAO_VERMELHO)
        botoes.add_widget(btn_sim)
        botoes.add_widget(btn_nao)
        content.add_widget(botoes)
        
        popup = Popup(
            title='Confirmar',
            content=content,
            size_hint=(0.7, 0.35),
            background_color=COR_FUNDO_POPUP,
            title_color=COR_TEXTO_CLARO
        )
        
        def confirmar(x):
            sucesso, msg = self.gerenciador_seguranca.desativar_pin()
            popup.dismiss()
            self.pin_status.text = "⚠️ PIN não configurado"
            self.pin_status.color = COR_SEGURANCA_BAIXA
            self._mostrar_mensagem_sucesso(msg)
        
        btn_sim.bind(on_press=confirmar)
        btn_nao.bind(on_press=popup.dismiss)
        popup.open()
    
    def toggle_biometria(self, switch, value):
        """Ativa/desativa biometria"""
        sucesso, msg = self.gerenciador_seguranca.ativar_biometria(value)
        if sucesso:
            self._mostrar_mensagem_sucesso(msg)
        else:
            switch.active = not value
            self._mostrar_erro(msg)
    
    def mudar_tempo_bloqueio(self, spinner, text):
        """Altera o tempo de bloqueio"""
        minutos = int(text.split()[0])
        self.gerenciador_seguranca.set_tempo_bloqueio(minutos)
        self._mostrar_mensagem_sucesso(f"Tempo alterado para {minutos} min")
    
    def toggle_visitante(self, switch, value):
        """Ativa/desativa modo visitante"""
        self.gerenciador_seguranca.set_modo_visitante(value)
        self.carregar_dados()  # Recarrega para aplicar/remover ocultação
        status = "ativado" if value else "desativado"
        self._mostrar_mensagem_sucesso(f"Modo visitante {status}")
    
    # ---------- GERENCIAR CATEGORIAS ----------
    
    def gerenciar_categorias(self, *args):
        """Abre a tela de gerenciamento de categorias"""
        self.atualizar_lista_categorias()
    
    def atualizar_lista_categorias(self):
        """Atualiza e mostra a lista de categorias"""
        categorias = self.db.get_categorias()
        
        layout = BoxLayout(orientation='vertical', spacing=15, padding=20)
        with layout.canvas.before:
            Color(*COR_FUNDO_POPUP)
            Rectangle(pos=layout.pos, size=layout.size)
        
        layout.add_widget(Label(
            text='GERENCIAR CATEGORIAS',
            font_size='20sp',
            bold=True,
            color=COR_TEXTO_CLARO,
            size_hint_y=0.1
        ))
        
        sep = BoxLayout(size_hint_y=None, height=1)
        with sep.canvas:
            Color(*COR_BORDA)
            Rectangle(pos=sep.pos, size=sep.size)
        layout.add_widget(sep)
        
        # Lista de categorias
        scroll = ScrollView(size_hint_y=0.6)
        grid = GridLayout(cols=1, size_hint_y=None, spacing=10, padding=10)
        grid.bind(minimum_height=grid.setter('height'))
        
        for cat in categorias:
            # Card da categoria
            card = BoxLayout(orientation='horizontal', size_hint_y=None, height=100, spacing=10)
            with card.canvas.before:
                Color(*COR_FUNDO_CARD)
                RoundedRectangle(pos=card.pos, size=card.size, radius=[8])
            card.bind(pos=self._atualizar_card_simples, size=self._atualizar_card_simples)
            
            card.add_widget(Label(
                text=cat[1],
                color=COR_TEXTO,
                size_hint_x=0.5,
                halign='left'
            ))
            
            btn_editar = BotaoArredondado(
                text='✏️ Editar',
                background_color=COR_BOTAO_AZUL,
                size_hint_x=0.2,
                height=40
            )
            btn_editar.categoria_id = cat[0]
            btn_editar.categoria_nome = cat[1]
            btn_editar.bind(on_press=self.editar_categoria)
            
            btn_excluir = BotaoArredondado(
                text='🗑️ Excluir',
                background_color=COR_BOTAO_VERMELHO,
                size_hint_x=0.2,
                height=40
            )
            btn_excluir.categoria_id = cat[0]
            btn_excluir.categoria_nome = cat[1]
            btn_excluir.bind(on_press=self.excluir_categoria)
            
            card.add_widget(btn_editar)
            card.add_widget(btn_excluir)
            grid.add_widget(card)
        
        scroll.add_widget(grid)
        layout.add_widget(scroll)
        
        # Botão Nova Categoria
        btn_nova = BotaoArredondado(
            text='➕ Nova Categoria',
            background_color=COR_BOTAO_VERDE,
            size_hint_y=0.1
        )
        btn_nova.bind(on_press=self.nova_categoria)
        layout.add_widget(btn_nova)
        
        btn_fechar = BotaoArredondado(
            text='Fechar',
            background_color=COR_BOTAO_VERMELHO,
            size_hint_y=0.1
        )
        
        self.popup_categorias = Popup(
            title='Categorias',
            content=layout,
            size_hint=(0.9, 0.8),
            background_color=COR_FUNDO_POPUP,
            title_color=COR_TEXTO_CLARO
        )
        btn_fechar.bind(on_press=self.popup_categorias.dismiss)
        layout.add_widget(btn_fechar)
        
        self.popup_categorias.open()
    
    def nova_categoria(self, *args):
        """Popup para criar nova categoria"""
        layout = BoxLayout(orientation='vertical', spacing=15, padding=20)
        with layout.canvas.before:
            Color(*COR_FUNDO_POPUP)
            Rectangle(pos=layout.pos, size=layout.size)
        
        layout.add_widget(Label(
            text='NOVA CATEGORIA',
            font_size='18sp',
            bold=True,
            color=COR_TEXTO_CLARO,
            size_hint_y=0.2
        ))
        
        layout.add_widget(Label(text='Nome da categoria:', color=COR_TEXTO_CLARO, size_hint_y=0.1))
        input_nome = TextInput(multiline=False, size_hint_y=0.2, font_size='16sp', foreground_color=COR_TEXTO, background_color=COR_FUNDO_INPUT)
        layout.add_widget(input_nome)
        
        botoes = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.2)
        btn_salvar = BotaoArredondado(
            text='Salvar',
            background_color=COR_BOTAO_VERDE
        )
        btn_cancelar = BotaoArredondado(
            text='Cancelar',
            background_color=COR_BOTAO_VERMELHO
        )
        botoes.add_widget(btn_salvar)
        botoes.add_widget(btn_cancelar)
        layout.add_widget(botoes)
        
        popup = Popup(
            title='Nova Categoria',
            content=layout,
            size_hint=(0.8, 0.5),
            background_color=COR_FUNDO_POPUP,
            title_color=COR_TEXTO_CLARO
        )
        
        def salvar(x):
            nome = input_nome.text.strip()
            if not nome:
                erro = Popup(title='Erro', content=Label(text='Digite um nome!', color=COR_TEXTO_CLARO), size_hint=(0.6,0.3), background_color=COR_FUNDO_POPUP, title_color=COR_TEXTO_CLARO)
                erro.open()
                return
            
            if self.db.add_categoria(nome):
                popup.dismiss()
                self.popup_categorias.dismiss()
                self.atualizar_lista_categorias()
            else:
                erro = Popup(title='Erro', content=Label(text='Categoria já existe!', color=COR_TEXTO_CLARO), size_hint=(0.6,0.3), background_color=COR_FUNDO_POPUP, title_color=COR_TEXTO_CLARO)
                erro.open()
        
        btn_salvar.bind(on_press=salvar)
        btn_cancelar.bind(on_press=popup.dismiss)
        popup.open()
    
    def editar_categoria(self, btn):
        """Popup para editar categoria"""
        layout = BoxLayout(orientation='vertical', spacing=15, padding=20)
        with layout.canvas.before:
            Color(*COR_FUNDO_POPUP)
            Rectangle(pos=layout.pos, size=layout.size)
        
        layout.add_widget(Label(
            text='EDITAR CATEGORIA',
            font_size='18sp',
            bold=True,
            color=COR_TEXTO_CLARO,
            size_hint_y=0.2
        ))
        
        layout.add_widget(Label(text='Nome da categoria:', color=COR_TEXTO_CLARO, size_hint_y=0.1))
        input_nome = TextInput(text=btn.categoria_nome, multiline=False, size_hint_y=0.2, font_size='16sp', foreground_color=COR_TEXTO, background_color=COR_FUNDO_INPUT)
        layout.add_widget(input_nome)
        
        botoes = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.2)
        btn_salvar = BotaoArredondado(
            text='Salvar',
            background_color=COR_BOTAO_VERDE
        )
        btn_cancelar = BotaoArredondado(
            text='Cancelar',
            background_color=COR_BOTAO_VERMELHO
        )
        botoes.add_widget(btn_salvar)
        botoes.add_widget(btn_cancelar)
        layout.add_widget(botoes)
        
        popup = Popup(
            title='Editar Categoria',
            content=layout,
            size_hint=(0.8, 0.5),
            background_color=COR_FUNDO_POPUP,
            title_color=COR_TEXTO_CLARO
        )
        
        def salvar(x):
            nome = input_nome.text.strip()
            if not nome:
                erro = Popup(title='Erro', content=Label(text='Digite um nome!', color=COR_TEXTO_CLARO), size_hint=(0.6,0.3), background_color=COR_FUNDO_POPUP, title_color=COR_TEXTO_CLARO)
                erro.open()
                return
            
            if self.db.update_categoria(btn.categoria_id, nome, '#3498db'):
                popup.dismiss()
                self.popup_categorias.dismiss()
                self.atualizar_lista_categorias()
            else:
                erro = Popup(title='Erro', content=Label(text='Nome já existe!', color=COR_TEXTO_CLARO), size_hint=(0.6,0.3), background_color=COR_FUNDO_POPUP, title_color=COR_TEXTO_CLARO)
                erro.open()
        
        btn_salvar.bind(on_press=salvar)
        btn_cancelar.bind(on_press=popup.dismiss)
        popup.open()
    
    def excluir_categoria(self, btn):
        """Confirma exclusão de categoria"""
        content = BoxLayout(orientation='vertical', spacing=15, padding=20)
        with content.canvas.before:
            Color(*COR_FUNDO_POPUP)
            Rectangle(pos=content.pos, size=content.size)
        
        content.add_widget(Label(
            text=f'Excluir categoria "{btn.categoria_nome}"?\n\nDespesas com esta categoria ficarão sem categoria.',
            color=COR_TEXTO_CLARO
        ))
        
        botoes = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.3)
        btn_sim = BotaoArredondado(
            text='Sim',
            background_color=COR_BOTAO_VERDE
        )
        btn_nao = BotaoArredondado(
            text='Não',
            background_color=COR_BOTAO_VERMELHO
        )
        botoes.add_widget(btn_sim)
        botoes.add_widget(btn_nao)
        content.add_widget(botoes)
        
        popup = Popup(
            title='Confirmar',
            content=content,
            size_hint=(0.7, 0.4),
            background_color=COR_FUNDO_POPUP,
            title_color=COR_TEXTO_CLARO
        )
        
        def confirmar(x):
            if self.db.delete_categoria(btn.categoria_id):
                popup.dismiss()
                self.popup_categorias.dismiss()
                self.atualizar_lista_categorias()
            else:
                erro = Popup(
                    title='Erro',
                    content=Label(text='Não é possível excluir:\nExistem despesas com esta categoria!', color=COR_TEXTO_CLARO),
                    size_hint=(0.7, 0.3),
                    background_color=COR_FUNDO_POPUP,
                    title_color=COR_TEXTO_CLARO
                )
                erro.open()
        
        btn_sim.bind(on_press=confirmar)
        btn_nao.bind(on_press=popup.dismiss)
        popup.open()
    
    # ---------- GRÁFICOS ----------
    
    def abrir_graficos(self):
        """Abre a tela de gráficos"""
        despesas = self.db.get_despesas_mes(self.mes_atual)
        
        if not despesas:
            popup = Popup(
                title='Aviso',
                content=Label(text='Nenhuma despesa no mês atual!', color=COR_TEXTO_CLARO),
                size_hint=(0.6, 0.3),
                background_color=COR_FUNDO_POPUP,
                title_color=COR_TEXTO_CLARO
            )
            popup.open()
            return
        
        # Agrupar despesas por categoria
        categorias = {}
        for d in despesas:
            cat_nome = d[-2] if d[-2] else 'Sem categoria'
            if cat_nome not in categorias:
                categorias[cat_nome] = 0
            categorias[cat_nome] += d[2]
        
        # Criar gráfico
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Dados
        nomes = list(categorias.keys())
        valores = list(categorias.values())
        cores = plt.cm.Set3(range(len(nomes)))
        
        # Barras
        bars = ax.bar(nomes, valores, color=cores)
        ax.set_title(f'Despesas por Categoria - {self.mes_atual}', fontsize=14, fontweight='bold')
        ax.set_ylabel('Valor (R$)', fontsize=12)
        ax.set_xlabel('Categoria', fontsize=12)
        
        # Adicionar valores nas barras
        for bar, valor in zip(bars, valores):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'R$ {valor:.2f}'.replace('.', ','),
                   ha='center', va='bottom', fontsize=10)
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Criar popup com o gráfico
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        layout.add_widget(FigureCanvasKivyAgg(fig))
        
        btn_fechar = BotaoArredondado(
            text='Fechar',
            background_color=COR_BOTAO_VERMELHO
        )
        layout.add_widget(btn_fechar)
        
        popup = Popup(
            title='📊 Gráfico de Despesas',
            content=layout,
            size_hint=(0.9, 0.8),
            background_color=COR_FUNDO_POPUP,
            title_color=COR_TEXTO_CLARO
        )
        btn_fechar.bind(on_press=popup.dismiss)
        popup.open()
    
    # ---------- RELATÓRIOS ----------
    
    def abrir_relatorios(self):
        """Abre a tela de seleção de relatório"""
        layout = BoxLayout(orientation='vertical', spacing=15, padding=20)
        with layout.canvas.before:
            Color(*COR_FUNDO_POPUP)
            Rectangle(pos=layout.pos, size=layout.size)
        
        layout.add_widget(Label(
            text='GERAR RELATÓRIO',
            font_size='18sp',
            bold=True,
            color=COR_TEXTO_CLARO,
            size_hint_y=0.15
        ))
        
        sep = BoxLayout(size_hint_y=None, height=1)
        with sep.canvas:
            Color(*COR_BORDA)
            Rectangle(pos=sep.pos, size=sep.size)
        layout.add_widget(sep)
        
        btn_mes = BotaoArredondado(
            text='📄 Relatório do Mês Atual',
            background_color=COR_BOTAO_AZUL
        )
        btn_mes.bind(on_press=lambda x: self.gerar_relatorio_mes(self.mes_atual))
        layout.add_widget(btn_mes)
        
        btn_ano = BotaoArredondado(
            text='📅 Relatório do Ano',
            background_color=COR_BOTAO_AZUL
        )
        btn_ano.bind(on_press=self.selecionar_ano)
        layout.add_widget(btn_ano)
        
        btn_fechar = BotaoArredondado(
            text='❌ Cancelar',
            background_color=COR_BOTAO_VERMELHO
        )
        
        popup = Popup(
            title='Relatórios',
            content=layout,
            size_hint=(0.8, 0.5),
            background_color=COR_FUNDO_POPUP,
            title_color=COR_TEXTO_CLARO
        )
        btn_fechar.bind(on_press=popup.dismiss)
        layout.add_widget(btn_fechar)
        
        popup.open()
    
    def selecionar_ano(self, *args):
        """Popup para selecionar o ano do relatório"""
        layout = BoxLayout(orientation='vertical', spacing=15, padding=20)
        with layout.canvas.before:
            Color(*COR_FUNDO_POPUP)
            Rectangle(pos=layout.pos, size=layout.size)
        
        layout.add_widget(Label(
            text='SELECIONE O ANO',
            font_size='18sp',
            bold=True,
            color=COR_TEXTO_CLARO,
            size_hint_y=0.2
        ))
        
        ano_atual = datetime.now().year
        anos = [str(ano_atual - i) for i in range(5)]
        
        spinner_ano = Spinner(
            text=str(ano_atual),
            values=anos,
            size_hint_y=0.2,
            font_size='16sp',
            color=COR_TEXTO,
            background_color=COR_FUNDO_INPUT
        )
        layout.add_widget(spinner_ano)
        
        botoes = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.2)
        btn_gerar = BotaoArredondado(
            text='Gerar',
            background_color=COR_BOTAO_VERDE
        )
        btn_cancelar = BotaoArredondado(
            text='Cancelar',
            background_color=COR_BOTAO_VERMELHO
        )
        botoes.add_widget(btn_gerar)
        botoes.add_widget(btn_cancelar)
        layout.add_widget(botoes)
        
        popup = Popup(
            title='Selecionar Ano',
            content=layout,
            size_hint=(0.7, 0.4),
            background_color=COR_FUNDO_POPUP,
            title_color=COR_TEXTO_CLARO
        )
        
        btn_gerar.bind(on_press=lambda x: self.gerar_relatorio_ano(spinner_ano.text, popup))
        btn_cancelar.bind(on_press=popup.dismiss)
        popup.open()
    
    def gerar_relatorio_mes(self, mes_ano):
        """Gera relatório PDF do mês especificado"""
        try:
            salario = self.db.get_salario(mes_ano)
            despesas = self.db.get_despesas_mes(mes_ano)
            
            if not despesas and salario == 0:
                popup = Popup(
                    title='Aviso',
                    content=Label(text='Não há dados para este mês!', color=COR_TEXTO_CLARO),
                    size_hint=(0.6, 0.3),
                    background_color=COR_FUNDO_POPUP,
                    title_color=COR_TEXTO_CLARO
                )
                popup.open()
                return
            
            total_pago = sum(d[2] for d in despesas if d[8] == 'pago')
            saldo = salario - total_pago
            moeda = self.config_manager.get('moeda')
            
            pdf = FPDF()
            pdf.add_page()
            
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(190, 10, f'Relatório Financeiro - {mes_ano}', ln=1, align='C')
            pdf.ln(10)
            
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(190, 8, 'RESUMO DO MÊS', ln=1)
            pdf.set_font('Arial', '', 12)
            pdf.cell(190, 8, f'Salário: {moeda} {salario:.2f}'.replace('.', ','), ln=1)
            pdf.cell(190, 8, f'Total Pago: {moeda} {total_pago:.2f}'.replace('.', ','), ln=1)
            pdf.cell(190, 8, f'Saldo: {moeda} {saldo:.2f}'.replace('.', ','), ln=1)
            pdf.ln(10)
            
            if despesas:
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(190, 8, 'DESPESAS DO MÊS', ln=1)
                pdf.ln(5)
                
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(70, 8, 'Descrição', 1)
                pdf.cell(30, 8, 'Valor', 1)
                pdf.cell(30, 8, 'Vencimento', 1)
                pdf.cell(30, 8, 'Status', 1)
                pdf.cell(30, 8, 'Categoria', 1)
                pdf.ln()
                
                pdf.set_font('Arial', '', 9)
                for d in despesas:
                    desc = d[1][:30] if d[1] else ''
                    valor = f'{moeda} {d[2]:.2f}'.replace('.', ',')
                    venc = d[6][8:] if d[6] else f'Dia {d[5]}'
                    status = 'Pago' if d[8] == 'pago' else 'Pendente'
                    cat = d[-2] if d[-2] else 'Sem categoria'
                    
                    pdf.cell(70, 8, desc, 1)
                    pdf.cell(30, 8, valor, 1)
                    pdf.cell(30, 8, venc, 1)
                    pdf.cell(30, 8, status, 1)
                    pdf.cell(30, 8, cat, 1)
                    pdf.ln()
            
            downloads_path = '/storage/emulated/0/Download/'
            if not os.path.exists(downloads_path):
                downloads_path = os.getcwd()
            
            nome_arquivo = f'relatorio_{mes_ano}.pdf'
            caminho = os.path.join(downloads_path, nome_arquivo)
            pdf.output(caminho)
            
            content = BoxLayout(orientation='vertical', spacing=10, padding=10)
            with content.canvas.before:
                Color(*COR_FUNDO_POPUP)
                Rectangle(pos=content.pos, size=content.size)
            content.add_widget(Label(
                text=f'✅ PDF gerado com sucesso!\n\n{caminho}',
                color=COR_TEXTO_CLARO
            ))
            btn_ok = BotaoArredondado(
                text='OK',
                background_color=COR_BOTAO_VERDE,
                size_hint_y=0.3
            )
            content.add_widget(btn_ok)
            
            popup = Popup(
                title='Sucesso',
                content=content,
                size_hint=(0.8, 0.4),
                background_color=COR_FUNDO_POPUP,
                title_color=COR_TEXTO_CLARO
            )
            btn_ok.bind(on_press=popup.dismiss)
            popup.open()
            
        except Exception as e:
            erro = Popup(
                title='Erro',
                content=Label(text=f'Erro ao gerar PDF:\n{str(e)}', color=COR_TEXTO_CLARO),
                size_hint=(0.8, 0.3),
                background_color=COR_FUNDO_POPUP,
                title_color=COR_TEXTO_CLARO
            )
            erro.open()
    
    def gerar_relatorio_ano(self, ano, popup_ano):
        """Gera relatório PDF do ano inteiro"""
        popup_ano.dismiss()
        
        try:
            todos_meses = []
            total_ano = 0
            total_receitas = 0
            moeda = self.config_manager.get('moeda')
            
            for mes in range(1, 13):
                mes_ano = f'{ano}-{mes:02d}'
                salario = self.db.get_salario(mes_ano)
                despesas = self.db.get_despesas_mes(mes_ano)
                
                if despesas or salario > 0:
                    total_pago = sum(d[2] for d in despesas if d[8] == 'pago')
                    total_receitas += salario
                    total_ano += total_pago
                    todos_meses.append((mes_ano, salario, total_pago, despesas))
            
            if not todos_meses:
                popup = Popup(
                    title='Aviso',
                    content=Label(text=f'Não há dados para o ano {ano}!', color=COR_TEXTO_CLARO),
                    size_hint=(0.6, 0.3),
                    background_color=COR_FUNDO_POPUP,
                    title_color=COR_TEXTO_CLARO
                )
                popup.open()
                return
            
            pdf = FPDF()
            pdf.add_page()
            
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(190, 10, f'Relatório Anual - {ano}', ln=1, align='C')
            pdf.ln(10)
            
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(190, 8, 'RESUMO DO ANO', ln=1)
            pdf.set_font('Arial', '', 12)
            pdf.cell(190, 8, f'Total de Receitas: {moeda} {total_receitas:.2f}'.replace('.', ','), ln=1)
            pdf.cell(190, 8, f'Total de Despesas: {moeda} {total_ano:.2f}'.replace('.', ','), ln=1)
            pdf.cell(190, 8, f'Saldo Anual: {moeda} {total_receitas - total_ano:.2f}'.replace('.', ','), ln=1)
            pdf.ln(10)
            
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(190, 8, 'DETALHAMENTO POR MÊS', ln=1)
            pdf.ln(5)
            
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(40, 8, 'Mês', 1)
            pdf.cell(40, 8, 'Receitas', 1)
            pdf.cell(40, 8, 'Despesas', 1)
            pdf.cell(40, 8, 'Saldo', 1)
            pdf.ln()
            
            pdf.set_font('Arial', '', 10)
            for mes_ano, rec, desp, _ in todos_meses:
                nome_mes = {
                    '01': 'Janeiro', '02': 'Fevereiro', '03': 'Março',
                    '04': 'Abril', '05': 'Maio', '06': 'Junho',
                    '07': 'Julho', '08': 'Agosto', '09': 'Setembro',
                    '10': 'Outubro', '11': 'Novembro', '12': 'Dezembro'
                }.get(mes_ano[5:7], mes_ano[5:7])
                
                pdf.cell(40, 8, nome_mes, 1)
                pdf.cell(40, 8, f'{moeda} {rec:.2f}'.replace('.', ','), 1)
                pdf.cell(40, 8, f'{moeda} {desp:.2f}'.replace('.', ','), 1)
                pdf.cell(40, 8, f'{moeda} {rec - desp:.2f}'.replace('.', ','), 1)
                pdf.ln()
            
            downloads_path = '/storage/emulated/0/Download/'
            if not os.path.exists(downloads_path):
                downloads_path = os.getcwd()
            
            nome_arquivo = f'relatorio_anual_{ano}.pdf'
            caminho = os.path.join(downloads_path, nome_arquivo)
            pdf.output(caminho)
            
            content = BoxLayout(orientation='vertical', spacing=10, padding=10)
            with content.canvas.before:
                Color(*COR_FUNDO_POPUP)
                Rectangle(pos=content.pos, size=content.size)
            content.add_widget(Label(
                text=f'✅ PDF anual gerado com sucesso!\n\n{caminho}',
                color=COR_TEXTO_CLARO
            ))
            btn_ok = BotaoArredondado(
                text='OK',
                background_color=COR_BOTAO_VERDE,
                size_hint_y=0.3
            )
            content.add_widget(btn_ok)
            
            popup = Popup(
                title='Sucesso',
                content=content,
                size_hint=(0.8, 0.4),
                background_color=COR_FUNDO_POPUP,
                title_color=COR_TEXTO_CLARO
            )
            btn_ok.bind(on_press=popup.dismiss)
            popup.open()
            
        except Exception as e:
            erro = Popup(
                title='Erro',
                content=Label(text=f'Erro ao gerar PDF:\n{str(e)}', color=COR_TEXTO_CLARO),
                size_hint=(0.8, 0.3),
                background_color=COR_FUNDO_POPUP,
                title_color=COR_TEXTO_CLARO
            )
            erro.open()
    
    # ---------- BACKUP ----------
    
    def abrir_backup(self):
        """Abre a tela de backup e restauração"""
        layout = BoxLayout(orientation='vertical', spacing=15, padding=20)
        with layout.canvas.before:
            Color(*COR_FUNDO_POPUP)
            Rectangle(pos=layout.pos, size=layout.size)
        
        layout.add_widget(Label(
            text='BACKUP E RESTAURAÇÃO',
            font_size='18sp',
            bold=True,
            color=COR_TEXTO_CLARO,
            size_hint_y=0.15
        ))
        
        sep = BoxLayout(size_hint_y=None, height=1)
        with sep.canvas:
            Color(*COR_BORDA)
            Rectangle(pos=sep.pos, size=sep.size)
        layout.add_widget(sep)
        
        btn_backup = BotaoArredondado(
            text='💾 Fazer Backup',
            background_color=COR_BOTAO_AZUL
        )
        btn_backup.bind(on_press=self.fazer_backup)
        layout.add_widget(btn_backup)
        
        btn_restore = BotaoArredondado(
            text='↩️ Restaurar Backup',
            background_color=COR_BOTAO_VERDE
        )
        btn_restore.bind(on_press=self.restaurar_backup)
        layout.add_widget(btn_restore)
        
        layout.add_widget(Widget(size_hint_y=0.1))
        
        btn_fechar = BotaoArredondado(
            text='❌ Fechar',
            background_color=COR_BOTAO_VERMELHO
        )
        
        popup = Popup(
            title='Backup',
            content=layout,
            size_hint=(0.8, 0.5),
            background_color=COR_FUNDO_POPUP,
            title_color=COR_TEXTO_CLARO
        )
        btn_fechar.bind(on_press=popup.dismiss)
        layout.add_widget(btn_fechar)
        
        popup.open()
    
    def fazer_backup(self, *args):
        """Faz backup dos dados para arquivo JSON"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nome_arquivo = f'backup_financas_{timestamp}.json'
            
            downloads_path = '/storage/emulated/0/Download/'
            if not os.path.exists(downloads_path):
                downloads_path = os.getcwd()
            
            caminho = os.path.join(downloads_path, nome_arquivo)
            
            self.db.export_to_json(caminho)
            
            content = BoxLayout(orientation='vertical', spacing=10, padding=10)
            with content.canvas.before:
                Color(*COR_FUNDO_POPUP)
                Rectangle(pos=content.pos, size=content.size)
            content.add_widget(Label(
                text=f'✅ Backup realizado com sucesso!\n\n{caminho}',
                color=COR_TEXTO_CLARO
            ))
            btn_ok = BotaoArredondado(
                text='OK',
                background_color=COR_BOTAO_VERDE,
                size_hint_y=0.3
            )
            content.add_widget(btn_ok)
            
            popup = Popup(
                title='Sucesso',
                content=content,
                size_hint=(0.8, 0.4),
                background_color=COR_FUNDO_POPUP,
                title_color=COR_TEXTO_CLARO
            )
            btn_ok.bind(on_press=popup.dismiss)
            popup.open()
            
        except Exception as e:
            erro = Popup(
                title='Erro',
                content=Label(text=f'Erro ao fazer backup:\n{str(e)}', color=COR_TEXTO_CLARO),
                size_hint=(0.8, 0.3),
                background_color=COR_FUNDO_POPUP,
                title_color=COR_TEXTO_CLARO
            )
            erro.open()
    
    def restaurar_backup(self, *args):
        """Abre seletor de arquivo para restaurar backup"""
        layout = BoxLayout(orientation='vertical', spacing=15, padding=20)
        with layout.canvas.before:
            Color(*COR_FUNDO_POPUP)
            Rectangle(pos=layout.pos, size=layout.size)
        
        layout.add_widget(Label(
            text='SELECIONE O ARQUIVO DE BACKUP',
            font_size='16sp',
            bold=True,
            color=COR_TEXTO_CLARO,
            size_hint_y=0.15
        ))
        
        downloads_path = '/storage/emulated/0/Download/'
        if os.path.exists(downloads_path):
            arquivos = [f for f in os.listdir(downloads_path) 
                       if f.startswith('backup_financas_') and f.endswith('.json')]
        else:
            arquivos = []
        
        if not arquivos:
            layout.add_widget(Label(
                text='Nenhum arquivo de backup encontrado!',
                color=COR_TEXTO_CLARO,
                size_hint_y=0.2
            ))
            btn_fechar = BotaoArredondado(
                text='Fechar',
                background_color=COR_BOTAO_VERMELHO
            )
            layout.add_widget(btn_fechar)
            
            popup = Popup(
                title='Restaurar Backup',
                content=layout,
                size_hint=(0.8, 0.4),
                background_color=COR_FUNDO_POPUP,
                title_color=COR_TEXTO_CLARO
            )
            btn_fechar.bind(on_press=popup.dismiss)
            popup.open()
            return
        
        arquivos.sort(reverse=True)
        
        scroll = ScrollView(size_hint_y=0.6)
        grid = GridLayout(cols=1, size_hint_y=None, spacing=5)
        grid.bind(minimum_height=grid.setter('height'))
        
        for arq in arquivos[:10]:
            btn_arquivo = BotaoArredondado(
                text=arq,
                background_color=COR_BOTAO_CINZA,
                color=COR_TEXTO,
                size_hint_y=None,
                height=40
            )
            caminho = os.path.join(downloads_path, arq)
            btn_arquivo.bind(on_press=lambda x, c=caminho: self.confirmar_restauracao(c))
            grid.add_widget(btn_arquivo)
        
        scroll.add_widget(grid)
        layout.add_widget(scroll)
        
        btn_cancelar = BotaoArredondado(
            text='Cancelar',
            background_color=COR_BOTAO_VERMELHO
        )
        layout.add_widget(btn_cancelar)
        
        popup = Popup(
            title='Restaurar Backup',
            content=layout,
            size_hint=(0.9, 0.7),
            background_color=COR_FUNDO_POPUP,
            title_color=COR_TEXTO_CLARO
        )
        btn_cancelar.bind(on_press=popup.dismiss)
        popup.open()
    
    def confirmar_restauracao(self, caminho):
        """Confirma a restauração do backup"""
        content = BoxLayout(orientation='vertical', spacing=15, padding=20)
        with content.canvas.before:
            Color(*COR_FUNDO_POPUP)
            Rectangle(pos=content.pos, size=content.size)
        
        content.add_widget(Label(
            text='⚠️ ATENÇÃO ⚠️\n\nIsso substituirá TODOS os dados atuais.\nDeseja continuar?',
            color=COR_TEXTO_CLARO
        ))
        
        botoes = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.3)
        btn_sim = BotaoArredondado(
            text='Sim',
            background_color=COR_BOTAO_VERDE
        )
        btn_nao = BotaoArredondado(
            text='Não',
            background_color=COR_BOTAO_VERMELHO
        )
        botoes.add_widget(btn_sim)
        botoes.add_widget(btn_nao)
        content.add_widget(botoes)
        
        popup = Popup(
            title='Confirmar',
            content=content,
            size_hint=(0.7, 0.4),
            background_color=COR_FUNDO_POPUP,
            title_color=COR_TEXTO_CLARO
        )
        
        def restaurar(x):
            try:
                self.db.import_from_json(caminho)
                popup.dismiss()
                self.carregar_dados()
                
                sucesso = Popup(
                    title='Sucesso',
                    content=Label(text='✅ Dados restaurados com sucesso!', color=COR_TEXTO_CLARO),
                    size_hint=(0.6, 0.3),
                    background_color=COR_FUNDO_POPUP,
                    title_color=COR_TEXTO_CLARO
                )
                sucesso.open()
                
            except Exception as e:
                erro = Popup(
                    title='Erro',
                    content=Label(text=f'Erro ao restaurar:\n{str(e)}', color=COR_TEXTO_CLARO),
                    size_hint=(0.8, 0.3),
                    background_color=COR_FUNDO_POPUP,
                    title_color=COR_TEXTO_CLARO
                )
                erro.open()
        
        btn_sim.bind(on_press=restaurar)
        btn_nao.bind(on_press=popup.dismiss)
        popup.open()
    
    # ---------- ORÇAMENTOS (INTEGRADO) ----------
    
    def abrir_orcamentos(self, *args):
        """Abre a tela de gerenciamento de orçamentos"""
        popup = Popup(
            title='💰 Orçamentos',
            size_hint=(0.95, 0.9),
            background_color=COR_FUNDO_POPUP,
            title_color=COR_TEXTO_CLARO
        )
        
        # Layout principal
        layout = BoxLayout(orientation='vertical', spacing=8, padding=[8, 8, 8, 8])
        with layout.canvas.before:
            Color(*COR_FUNDO_POPUP)
            Rectangle(pos=layout.pos, size=layout.size)
        
        # Cabeçalho com navegação
        cabecalho = BoxLayout(size_hint_y=0.1, spacing=5)
        
        btn_ant = BotaoArredondado(
            text='<',
            background_color=COR_BOTAO_AZUL,
            size_hint_x=0.15,
            height=40
        )
        btn_ant.bind(on_press=lambda x: self.mudar_mes_orcamentos(-1))
        
        titulo = Label(
            text='ORÇAMENTOS',
            font_size='18sp',
            bold=True,
            color=COR_TEXTO_CLARO,
            size_hint_x=0.7,
            halign='center'
        )
        
        btn_prox = BotaoArredondado(
            text='>',
            background_color=COR_BOTAO_AZUL,
            size_hint_x=0.15,
            height=40
        )
        btn_prox.bind(on_press=lambda x: self.mudar_mes_orcamentos(1))
        
        cabecalho.add_widget(btn_ant)
        cabecalho.add_widget(titulo)
        cabecalho.add_widget(btn_prox)
        
        layout.add_widget(cabecalho)
        
        # Mês atual
        self.mes_orcamento_label = Label(
            text=self.mes_atual,
            font_size='14sp',
            color=COR_TEXTO_CLARO,
            size_hint_y=0.04,
            halign='center'
        )
        layout.add_widget(self.mes_orcamento_label)
        
        layout.add_widget(self._criar_separador_menor())
        
        # Área de resumo
        self.resumo_orcamentos = BoxLayout(size_hint_y=0.08, spacing=8)
        layout.add_widget(self.resumo_orcamentos)
        
        layout.add_widget(self._criar_separador_menor())
        
        # Lista de orçamentos
        scroll = ScrollView(size_hint_y=0.7)
        self.lista_orcamentos = GridLayout(cols=1, size_hint_y=None, spacing=6, padding=[2, 2, 2, 2])
        self.lista_orcamentos.bind(minimum_height=self.lista_orcamentos.setter('height'))
        scroll.add_widget(self.lista_orcamentos)
        layout.add_widget(scroll)
        
        # Botão voltar
        btn_voltar = BotaoArredondado(
            text='🔙 Voltar',
            background_color=COR_BOTAO_VERMELHO,
            size_hint_y=0.08,
            height=40
        )
        btn_voltar.bind(on_press=popup.dismiss)
        layout.add_widget(btn_voltar)
        
        popup.content = layout
        self.popup_orcamentos = popup
        self.carregar_orcamentos()
        popup.open()
    
    def mudar_mes_orcamentos(self, delta):
        """Navega entre meses na tela de orçamentos"""
        ano, mes = map(int, self.mes_atual.split('-'))
        mes += delta
        if mes == 0:
            mes = 12
            ano -= 1
        elif mes == 13:
            mes = 1
            ano += 1
        self.mes_atual = f'{ano:04d}-{mes:02d}'
        self.mes_orcamento_label.text = self.mes_atual
        self.carregar_orcamentos()
    
    def carregar_orcamentos(self):
        """Carrega e exibe todos os orçamentos do mês"""
        orcamentos = self.gerenciador_orcamentos.get_orcamentos_mes(self.mes_atual)
        self.atualizar_resumo_orcamentos(orcamentos)
        self.lista_orcamentos.clear_widgets()
        
        if not orcamentos:
            msg = BoxLayout(orientation='vertical', size_hint_y=None, height=150)
            with msg.canvas.before:
                Color(*COR_FUNDO_CARD)
                RoundedRectangle(pos=msg.pos, size=msg.size, radius=[8])
            
            msg.add_widget(Label(
                text='📊 Nenhuma categoria encontrada',
                font_size='16sp',
                color=(0.5,0.5,0.5,1)
            ))
            self.lista_orcamentos.add_widget(msg)
            return
        
        for orc in orcamentos:
            card = self._criar_card_orcamento(orc)
            self.lista_orcamentos.add_widget(card)
    
    def _criar_card_orcamento(self, orc):
        """Cria um card para exibir um orçamento"""
        card = BoxLayout(orientation='vertical', size_hint_y=None, height=250, padding=10, spacing=8)
        with card.canvas.before:
            Color(*COR_FUNDO_CARD)
            card.rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[8])
        
        def update_rect(inst, *args):
            inst.rect.pos = inst.pos
            inst.rect.size = inst.size
        card.bind(pos=update_rect, size=update_rect)
        
        # LINHA 1: Nome e Status
        linha1 = BoxLayout(orientation='horizontal', size_hint_y=0.15, spacing=10)
        
        nome_label = Label(
            text=orc['nome'],
            bold=True,
            color=COR_TEXTO,
            halign='left',
            font_size='16sp',
            size_hint_x=0.5
        )
        linha1.add_widget(nome_label)
        
        if orc['limite'] == 0:
            status_text = '⚪ Sem limite'
            cor_status = COR_SEM_ORCAMENTO
        elif orc['status'] == 'estouro':
            status_text = '🔴 Estouro!'
            cor_status = COR_ESTouRO
        elif orc['status'] == 'atencao':
            status_text = '🟡 Atenção'
            cor_status = COR_ATENCAO
        else:
            status_text = '🟢 OK'
            cor_status = COR_DENTRO
        
        status_label = Label(
            text=status_text,
            color=cor_status,
            halign='right',
            font_size='13sp',
            bold=True,
            size_hint_x=0.5
        )
        linha1.add_widget(status_label)
        
        card.add_widget(linha1)
        
        # LINHA 2: Barra de progresso
        if orc['limite'] > 0:
            barra = BarraProgressoOrcamento(percentual=orc['percentual'], size_hint_y=0.1)
            card.add_widget(barra)
        else:
            card.add_widget(Widget(size_hint_y=0.1))
        
        # LINHA 3: Três colunas com valores
        linha3 = BoxLayout(orientation='horizontal', size_hint_y=0.4, spacing=15, padding=[0, 5, 0, 5])
        
        # Coluna Gasto
        col_gasto = BoxLayout(orientation='vertical', spacing=2)
        col_gasto.add_widget(Label(
            text='GASTO',
            color=(0.5,0.5,0.5,1),
            font_size='11sp',
            size_hint_y=0.3,
            halign='center'
        ))
        col_gasto.add_widget(Label(
            text=f'R$ {orc["gasto"]:.2f}'.replace('.', ','),
            color=COR_TEXTO,
            font_size='16sp',
            bold=True,
            size_hint_y=0.7,
            halign='center'
        ))
        
        # Coluna Limite
        col_limite = BoxLayout(orientation='vertical', spacing=2)
        col_limite.add_widget(Label(
            text='LIMITE',
            color=(0.5,0.5,0.5,1),
            font_size='11sp',
            size_hint_y=0.3,
            halign='center'
        ))
        
        if orc['limite'] > 0:
            texto_limite = f'R$ {orc["limite"]:.2f}'.replace('.', ',')
        else:
            texto_limite = '---'
        
        col_limite.add_widget(Label(
            text=texto_limite,
            color=COR_TEXTO,
            font_size='16sp',
            bold=True,
            size_hint_y=0.7,
            halign='center'
        ))
        
        # Coluna Restante
        col_restante = BoxLayout(orientation='vertical', spacing=2)
        col_restante.add_widget(Label(
            text='RESTANTE',
            color=(0.5,0.5,0.5,1),
            font_size='11sp',
            size_hint_y=0.3,
            halign='center'
        ))
        
        if orc['limite'] > 0:
            cor_restante = COR_DENTRO if orc['restante'] > 0 else COR_ESTouRO
            texto_restante = f'R$ {orc["restante"]:.2f}'.replace('.', ',')
        else:
            cor_restante = COR_SEM_ORCAMENTO
            texto_restante = '---'
        
        col_restante.add_widget(Label(
            text=texto_restante,
            color=cor_restante,
            font_size='16sp',
            bold=True,
            size_hint_y=0.7,
            halign='center'
        ))
        
        linha3.add_widget(col_gasto)
        linha3.add_widget(col_limite)
        linha3.add_widget(col_restante)
        card.add_widget(linha3)
        
        # LINHA 4: Botões
        linha4 = BoxLayout(orientation='horizontal', size_hint_y=0.2, spacing=15, padding=[0, 5, 0, 0])
        
        btn_config = BotaoArredondado(
            text='⚙️ Configurar',
            background_color=COR_BOTAO_AZUL,
            size_hint_x=0.48,
            height=40
        )
        btn_config.orc = orc
        btn_config.bind(on_press=self.configurar_orcamento)
        
        btn_zerar = BotaoArredondado(
            text='🔄 Zerar',
            background_color=COR_BOTAO_CINZA,
            color=COR_TEXTO,
            size_hint_x=0.48,
            height=40
        )
        btn_zerar.orc = orc
        btn_zerar.bind(on_press=self.zerar_orcamento)
        
        linha4.add_widget(btn_config)
        linha4.add_widget(btn_zerar)
        
        card.add_widget(linha4)
        
        return card
    
    def atualizar_resumo_orcamentos(self, orcamentos):
        """Atualiza o card de resumo de orçamentos"""
        self.resumo_orcamentos.clear_widgets()
        resumo = self.gerenciador_orcamentos.get_resumo(orcamentos)
        
        card = BoxLayout(orientation='horizontal', padding=8, spacing=8, size_hint_y=None, height=50)
        with card.canvas.before:
            Color(*COR_FUNDO_CARD)
            card.rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[8])
        
        # Coluna 1
        col1 = BoxLayout(orientation='vertical', spacing=2)
        col1.add_widget(Label(
            text=f'📊 Com limite: {resumo["total_categorias"]}',
            color=COR_TEXTO,
            font_size='11sp',
            halign='left',
            size_hint_y=0.5
        ))
        col1.add_widget(Label(
            text=f'🟡 {resumo["atencao"]}  🔴 {resumo["estouro"]}',
            color=COR_TEXTO,
            font_size='11sp',
            halign='left',
            size_hint_y=0.5
        ))
        
        # Coluna 2
        col2 = BoxLayout(orientation='vertical', spacing=2)
        col2.add_widget(Label(
            text=f'💰 R$ {resumo["total_gasto"]:.2f}'.replace('.', ','),
            color=COR_TEXTO,
            font_size='11sp',
            halign='left',
            size_hint_y=0.5
        ))
        
        cor_saldo = COR_DENTRO if resumo['saldo'] >= 0 else COR_ESTouRO
        col2.add_widget(Label(
            text=f'💵 R$ {resumo["saldo"]:.2f}'.replace('.', ','),
            color=cor_saldo,
            font_size='11sp',
            bold=True,
            halign='left',
            size_hint_y=0.5
        ))
        
        card.add_widget(col1)
        card.add_widget(col2)
        
        self.resumo_orcamentos.add_widget(card)
    
    def configurar_orcamento(self, btn):
        """Popup para configurar orçamento"""
        orc = btn.orc
        
        layout = BoxLayout(orientation='vertical', spacing=12, padding=15)
        with layout.canvas.before:
            Color(*COR_FUNDO_POPUP)
            Rectangle(pos=layout.pos, size=layout.size)
        
        layout.add_widget(Label(
            text=f'⚙️ {orc["nome"]}',
            font_size='18sp',
            bold=True,
            color=COR_TEXTO_CLARO,
            size_hint_y=0.2
        ))
        
        if orc['limite'] > 0:
            layout.add_widget(Label(
                text=f'Limite atual: R$ {orc["limite"]:.2f}'.replace('.', ','),
                color=COR_TEXTO_CLARO,
                size_hint_y=0.1
            ))
        
        layout.add_widget(Label(text='Novo limite mensal (R$):', color=COR_TEXTO_CLARO, size_hint_y=0.1))
        valor = TextInput(
            text=f"{orc['limite']:.2f}" if orc['limite'] > 0 else "",
            multiline=False,
            input_filter='float',
            font_size='16sp',
            foreground_color=COR_TEXTO,
            background_color=COR_FUNDO_INPUT,
            size_hint_y=0.15
        )
        layout.add_widget(valor)
        
        layout.add_widget(Label(
            text='💡 0 remove o orçamento',
            color=(0.5,0.5,0.5,1),
            font_size='11sp',
            size_hint_y=0.1
        ))
        
        botoes = BoxLayout(orientation='horizontal', size_hint_y=0.2, spacing=8)
        btn_salvar = BotaoArredondado(text='Salvar', background_color=COR_BOTAO_VERDE, height=40)
        btn_cancelar = BotaoArredondado(text='Cancelar', background_color=COR_BOTAO_VERMELHO, height=40)
        botoes.add_widget(btn_salvar)
        botoes.add_widget(btn_cancelar)
        layout.add_widget(botoes)
        
        popup = Popup(
            title='Configurar Orçamento',
            content=layout,
            size_hint=(0.85, 0.5),
            background_color=COR_FUNDO_POPUP,
            title_color=COR_TEXTO_CLARO
        )
        
        def salvar(*args):
            try:
                v = float(valor.text.replace(',', '.')) if valor.text else 0
                if v < 0:
                    self._mostrar_erro("Valor não pode ser negativo!")
                    return
                
                self.gerenciador_orcamentos.set_orcamento(orc['id'], self.mes_atual, v)
                popup.dismiss()
                self.carregar_orcamentos()
                self._mostrar_mensagem_sucesso("Orçamento salvo!")
            except ValueError:
                self._mostrar_erro("Valor inválido!")
        
        btn_salvar.bind(on_press=salvar)
        btn_cancelar.bind(on_press=popup.dismiss)
        popup.open()
    
    def zerar_orcamento(self, btn):
        """Zera (remove) o orçamento"""
        orc = btn.orc
        
        content = BoxLayout(orientation='vertical', spacing=12, padding=15)
        with content.canvas.before:
            Color(*COR_FUNDO_POPUP)
            Rectangle(pos=content.pos, size=content.size)
        
        content.add_widget(Label(
            text=f'Remover orçamento de\n"{orc["nome"]}"?',
            font_size='15sp',
            color=COR_TEXTO_CLARO
        ))
        
        botoes = BoxLayout(orientation='horizontal', spacing=8, size_hint_y=0.4)
        btn_sim = BotaoArredondado(text='Sim', background_color=COR_BOTAO_VERDE, height=40)
        btn_nao = BotaoArredondado(text='Não', background_color=COR_BOTAO_VERMELHO, height=40)
        botoes.add_widget(btn_sim)
        botoes.add_widget(btn_nao)
        content.add_widget(botoes)
        
        popup = Popup(
            title='Confirmar',
            content=content,
            size_hint=(0.7, 0.3),
            background_color=COR_FUNDO_POPUP,
            title_color=COR_TEXTO_CLARO
        )
        
        def confirmar(x):
            self.gerenciador_orcamentos.set_orcamento(orc['id'], self.mes_atual, 0)
            popup.dismiss()
            self.carregar_orcamentos()
            self._mostrar_mensagem_sucesso("Orçamento removido!")
        
        btn_sim.bind(on_press=confirmar)
        btn_nao.bind(on_press=popup.dismiss)
        popup.open()
    
    # ---------- METAS (MELHORADAS) ----------
    
    def abrir_metas(self, *args):
        """Abre a tela de gerenciamento de metas"""
        popup = Popup(
            title='🎯 Metas Financeiras',
            size_hint=(0.95, 0.9),
            background_color=COR_FUNDO_POPUP,
            title_color=COR_TEXTO_CLARO
        )
        
        # Layout principal
        layout = BoxLayout(orientation='vertical', spacing=10, padding=15)
        with layout.canvas.before:
            Color(*COR_FUNDO_POPUP)
            Rectangle(pos=layout.pos, size=layout.size)
        
        # Cabeçalho
        cabecalho = BoxLayout(size_hint_y=0.1, spacing=10)
        
        titulo = Label(
            text='🎯 METAS FINANCEIRAS',
            font_size='22sp',
            bold=True,
            color=COR_TEXTO_CLARO,
            size_hint_x=0.7
        )
        cabecalho.add_widget(titulo)
        
        btn_nova = BotaoArredondado(
            text='➕ Nova',
            background_color=COR_BOTAO_VERDE,
            size_hint_x=0.2,
            height=50
        )
        btn_nova.bind(on_press=lambda x: self.nova_meta(popup))
        cabecalho.add_widget(btn_nova)
        
        layout.add_widget(cabecalho)
        layout.add_widget(self._criar_separador_menor())
        
        # Área de resumo
        self.resumo_metas = BoxLayout(size_hint_y=0.1, spacing=10)
        layout.add_widget(self.resumo_metas)
        
        layout.add_widget(self._criar_separador_menor())
        
        # Lista de metas
        scroll = ScrollView(size_hint_y=0.7)
        self.lista_metas = GridLayout(cols=1, size_hint_y=None, spacing=12, padding=[5, 5, 5, 5])
        self.lista_metas.bind(minimum_height=self.lista_metas.setter('height'))
        scroll.add_widget(self.lista_metas)
        layout.add_widget(scroll)
        
        # Botão fechar
        btn_fechar = BotaoArredondado(
            text='🔙 Fechar',
            background_color=COR_BOTAO_VERMELHO,
            size_hint_y=0.08,
            height=45
        )
        btn_fechar.bind(on_press=popup.dismiss)
        layout.add_widget(btn_fechar)
        
        popup.content = layout
        self.popup_metas = popup
        self.carregar_metas()
        popup.open()
    
    def carregar_metas(self):
        """Carrega e exibe todas as metas"""
        metas = self.gerenciador_metas.listar_metas()
        
        self.atualizar_resumo_metas(metas)
        self.lista_metas.clear_widgets()
        
        if not metas:
            msg = BoxLayout(orientation='vertical', size_hint_y=None, height=200)
            with msg.canvas.before:
                Color(*COR_FUNDO_CARD)
                RoundedRectangle(pos=msg.pos, size=msg.size, radius=[10])
            msg.bind(pos=self._atualizar_card, size=self._atualizar_card)
            
            msg.add_widget(Label(
                text='✨ Nenhuma meta cadastrada',
                font_size='18sp',
                color=(0.5,0.5,0.5,1)
            ))
            msg.add_widget(Label(
                text='Clique em "Nova" para começar',
                font_size='14sp',
                color=(0.5,0.5,0.5,1)
            ))
            self.lista_metas.add_widget(msg)
            return
        
        for meta in metas:
            card = self._criar_card_meta_melhorado(meta)
            self.lista_metas.add_widget(card)
    
    def _criar_card_meta_melhorado(self, meta):
        """Cria um card para exibir uma meta (MELHORADO - 400px)"""
        id_meta, nome, valor_alvo, valor_atual, data_limite = meta
        progresso = self.gerenciador_metas.calcular_progresso(valor_atual, valor_alvo)
        dias_restantes = self._calcular_dias_restantes(data_limite)
        
        ocultar_valores = self.gerenciador_seguranca.config['modo_visitante']
        
        # Card principal - altura 400px
        card = BoxLayout(orientation='vertical', size_hint_y=None, height=400, padding=15, spacing=12)
        with card.canvas.before:
            Color(*COR_FUNDO_CARD)
            card.rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[10])
        
        def update_rect(inst, *args):
            inst.rect.pos = inst.pos
            inst.rect.size = inst.size
        card.bind(pos=update_rect, size=update_rect)
        
        # Linha 1: Nome e percentual
        linha1 = BoxLayout(orientation='horizontal', size_hint_y=0.15, spacing=10)
        linha1.add_widget(Label(
            text=nome[:30],
            bold=True,
            color=COR_TEXTO,
            halign='left',
            font_size='18sp',
            size_hint_x=0.7
        ))
        
        if progresso >= 100:
            status = '✅ CONCLUÍDA'
            cor_status = COR_PROGRESSO_CONCLUIDO
        else:
            status = f'{progresso:.1f}%'
            cor_status = COR_TEXTO
        
        linha1.add_widget(Label(
            text=status,
            color=cor_status,
            halign='right',
            font_size='16sp',
            bold=True,
            size_hint_x=0.3
        ))
        card.add_widget(linha1)
        
        # Barra de progresso
        barra = BarraProgresso(progresso=progresso, size_hint_y=0.1, height=25)
        card.add_widget(barra)
        
        # Linha 2: Valores (atual / alvo / restante) - MAIS ESPAÇAMENTO
        linha2 = BoxLayout(orientation='horizontal', size_hint_y=0.25, spacing=25, padding=[0, 5, 0, 5])
        
        # Valor atual
        col1 = BoxLayout(orientation='vertical', spacing=3)
        col1.add_widget(Label(text='Atual', color=(0.5,0.5,0.5,1), font_size='12sp', size_hint_y=0.25))
        if ocultar_valores:
            texto_atual = '🔒 ••••'
        else:
            texto_atual = f'R$ {valor_atual:.2f}'.replace('.', ',')
        col1.add_widget(Label(
            text=texto_atual,
            color=COR_BOTAO_VERDE,
            font_size='17sp',
            bold=True,
            size_hint_y=0.75
        ))
        
        # Valor alvo
        col2 = BoxLayout(orientation='vertical', spacing=3)
        col2.add_widget(Label(text='Meta', color=(0.5,0.5,0.5,1), font_size='12sp', size_hint_y=0.25))
        if ocultar_valores:
            texto_alvo = '🔒 ••••'
        else:
            texto_alvo = f'R$ {valor_alvo:.2f}'.replace('.', ',')
        col2.add_widget(Label(
            text=texto_alvo,
            color=COR_TEXTO,
            font_size='17sp',
            bold=True,
            size_hint_y=0.75
        ))
        
        # Valor restante
        col3 = BoxLayout(orientation='vertical', spacing=3)
        col3.add_widget(Label(text='Faltam', color=(0.5,0.5,0.5,1), font_size='12sp', size_hint_y=0.25))
        restante = valor_alvo - valor_atual
        if ocultar_valores:
            texto_restante = '🔒 ••••'
            cor_restante = COR_TEXTO
        else:
            texto_restante = f'R$ {restante:.2f}'.replace('.', ',')
            cor_restante = COR_BOTAO_VERMELHO if restante > 0 else COR_BOTAO_VERDE
        col3.add_widget(Label(
            text=texto_restante,
            color=cor_restante,
            font_size='17sp',
            bold=True,
            size_hint_y=0.75
        ))
        
        linha2.add_widget(col1)
        linha2.add_widget(col2)
        linha2.add_widget(col3)
        card.add_widget(linha2)
        
        # Linha 3: Data limite
        linha3 = BoxLayout(orientation='horizontal', size_hint_y=0.15, padding=[0, 5, 0, 5])
        
        if dias_restantes > 0:
            texto_data = f'📅 {data_limite} ({dias_restantes} dias)'
            cor_data = COR_TEXTO if dias_restantes > 7 else COR_BOTAO_AMARELO
        elif dias_restantes == 0:
            texto_data = f'📅 {data_limite} (Último dia!)'
            cor_data = COR_BOTAO_AMARELO
        else:
            texto_data = f'📅 {data_limite} (Atrasada {abs(dias_restantes)} dias)'
            cor_data = COR_BOTAO_VERMELHO
        
        linha3.add_widget(Label(
            text=texto_data,
            color=cor_data,
            halign='left',
            font_size='14sp'
        ))
        card.add_widget(linha3)
        
        # Linha 4: Botões - MAIORES E MAIS ESPAÇADOS
        linha4 = BoxLayout(orientation='horizontal', size_hint_y=0.2, spacing=20, padding=[0, 10, 0, 0])
        
        btn_adicionar = BotaoArredondado(
            text='💰 Adicionar',
            background_color=COR_BOTAO_AZUL,
            size_hint_x=0.33,
            height=48
        )
        btn_adicionar.meta_id = id_meta
        btn_adicionar.meta_nome = nome
        btn_adicionar.valor_atual = valor_atual
        btn_adicionar.valor_alvo = valor_alvo
        btn_adicionar.bind(on_press=lambda x: self.adicionar_valor_meta(x, self.popup_metas))
        
        btn_editar = BotaoArredondado(
            text='✏️ Editar',
            background_color=COR_BOTAO_AMARELO,
            size_hint_x=0.33,
            height=48
        )
        btn_editar.meta_id = id_meta
        btn_editar.meta_nome = nome
        btn_editar.valor_alvo = valor_alvo
        btn_editar.data_limite = data_limite
        btn_editar.bind(on_press=lambda x: self.editar_meta(x, self.popup_metas))
        
        btn_excluir = BotaoArredondado(
            text='🗑️ Excluir',
            background_color=COR_BOTAO_VERMELHO,
            size_hint_x=0.34,
            height=48
        )
        btn_excluir.meta_id = id_meta
        btn_excluir.meta_nome = nome
        btn_excluir.bind(on_press=lambda x: self.excluir_meta(x, self.popup_metas))
        
        linha4.add_widget(btn_adicionar)
        linha4.add_widget(btn_editar)
        linha4.add_widget(btn_excluir)
        
        card.add_widget(linha4)
        
        return card
    
    def _calcular_dias_restantes(self, data_limite):
        """Calcula dias restantes até a data limite"""
        try:
            data_obj = datetime.strptime(data_limite, '%Y-%m-%d')
            hoje = datetime.now()
            diferenca = data_obj - hoje
            return diferenca.days
        except:
            return 0
    
    def atualizar_resumo_metas(self, metas):
        """Atualiza o card de resumo de metas"""
        self.resumo_metas.clear_widgets()
        
        total_metas = len(metas)
        metas_concluidas = sum(1 for m in metas if m[3] >= m[2])
        valor_total = sum(m[2] for m in metas)
        valor_acumulado = sum(m[3] for m in metas)
        
        ocultar_valores = self.gerenciador_seguranca.config['modo_visitante']
        
        card = BoxLayout(orientation='horizontal', padding=12, spacing=15, size_hint_y=None, height=100)
        with card.canvas.before:
            Color(*COR_FUNDO_CARD)
            card.rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[10])
        card.bind(pos=self._atualizar_card, size=self._atualizar_card)
        
        # Coluna 1
        col1 = BoxLayout(orientation='vertical', spacing=3)
        col1.add_widget(Label(
            text=f'📊 Total: {total_metas}',
            bold=True,
            color=COR_TEXTO,
            font_size='14sp',
            halign='left'
        ))
        col1.add_widget(Label(
            text=f'✅ Concluídas: {metas_concluidas}',
            color=COR_TEXTO,
            font_size='14sp',
            halign='left'
        ))
        
        # Coluna 2
        col2 = BoxLayout(orientation='vertical', spacing=3)
        if ocultar_valores:
            texto_meta = '🎯 Meta: 🔒 ••••'
            texto_acumulado = '💰 Acumulado: 🔒 ••••'
        else:
            texto_meta = f'🎯 Meta: R$ {valor_total:.2f}'.replace('.', ',')
            texto_acumulado = f'💰 Acumulado: R$ {valor_acumulado:.2f}'.replace('.', ',')
        
        col2.add_widget(Label(
            text=texto_meta,
            color=COR_TEXTO,
            font_size='14sp',
            halign='left'
        ))
        col2.add_widget(Label(
            text=texto_acumulado,
            color=COR_TEXTO,
            font_size='14sp',
            halign='left'
        ))
        
        card.add_widget(col1)
        card.add_widget(col2)
        
        self.resumo_metas.add_widget(card)
    
    def nova_meta(self, popup_pai):
        """Popup para criar nova meta"""
        layout = BoxLayout(orientation='vertical', spacing=15, padding=20)
        with layout.canvas.before:
            Color(*COR_FUNDO_POPUP)
            Rectangle(pos=layout.pos, size=layout.size)
        
        layout.add_widget(Label(
            text='🎯 NOVA META',
            font_size='20sp',
            bold=True,
            color=COR_TEXTO_CLARO,
            size_hint_y=0.15
        ))
        
        # Formulário
        form = BoxLayout(orientation='vertical', spacing=12, size_hint_y=0.6)
        
        form.add_widget(Label(text='Nome da meta:', halign='left', color=COR_TEXTO_CLARO))
        nome = TextInput(multiline=False, font_size='16sp', foreground_color=COR_TEXTO, background_color=COR_FUNDO_INPUT)
        form.add_widget(nome)
        
        form.add_widget(Label(text='Valor alvo (R$):', halign='left', color=COR_TEXTO_CLARO))
        valor = TextInput(multiline=False, input_filter='float', font_size='16sp', foreground_color=COR_TEXTO, background_color=COR_FUNDO_INPUT)
        form.add_widget(valor)
        
        form.add_widget(Label(text='Data limite (AAAA-MM-DD):', halign='left', color=COR_TEXTO_CLARO))
        data = TextInput(
            text=datetime.now().strftime('%Y-%m-%d'),
            multiline=False,
            font_size='16sp',
            foreground_color=COR_TEXTO,
            background_color=COR_FUNDO_INPUT
        )
        form.add_widget(data)
        
        layout.add_widget(form)
        
        # Botões
        botoes = BoxLayout(orientation='horizontal', size_hint_y=0.15, spacing=10)
        btn_salvar = BotaoArredondado(text='Salvar', background_color=COR_BOTAO_VERDE)
        btn_cancelar = BotaoArredondado(text='Cancelar', background_color=COR_BOTAO_VERMELHO)
        botoes.add_widget(btn_salvar)
        botoes.add_widget(btn_cancelar)
        layout.add_widget(botoes)
        
        popup = Popup(
            title='Nova Meta',
            content=layout,
            size_hint=(0.9, 0.6),
            background_color=COR_FUNDO_POPUP,
            title_color=COR_TEXTO_CLARO
        )
        
        def salvar(*args):
            if not nome.text or not valor.text or not data.text:
                self._mostrar_erro_meta("Preencha todos os campos!")
                return
            
            try:
                v = float(valor.text.replace(',', '.'))
                if v <= 0:
                    self._mostrar_erro_meta("Valor deve ser positivo!")
                    return
                
                # Validar data
                try:
                    datetime.strptime(data.text, '%Y-%m-%d')
                except:
                    self._mostrar_erro_meta("Data inválida! Use AAAA-MM-DD")
                    return
                
                self.gerenciador_metas.criar_meta(nome.text, v, data.text)
                popup.dismiss()
                self.carregar_metas()
                self._mostrar_sucesso_meta("Meta criada com sucesso!")
                
            except ValueError:
                self._mostrar_erro_meta("Valor inválido!")
        
        btn_salvar.bind(on_press=salvar)
        btn_cancelar.bind(on_press=popup.dismiss)
        popup.open()
    
    def adicionar_valor_meta(self, btn, popup_pai):
        """Popup para adicionar valor à meta"""
        layout = BoxLayout(orientation='vertical', spacing=15, padding=20)
        with layout.canvas.before:
            Color(*COR_FUNDO_POPUP)
            Rectangle(pos=layout.pos, size=layout.size)
        
        layout.add_widget(Label(
            text=f'💰 {btn.meta_nome}',
            font_size='18sp',
            bold=True,
            color=COR_TEXTO_CLARO,
            size_hint_y=0.2
        ))
        
        restante = btn.valor_alvo - btn.valor_atual
        ocultar = self.gerenciador_seguranca.config['modo_visitante']
        
        if ocultar:
            texto_restante = '🔒 ••••'
        else:
            texto_restante = f'R$ {restante:.2f}'.replace('.', ',')
        
        layout.add_widget(Label(
            text=f'Faltam {texto_restante}',
            color=COR_TEXTO_CLARO,
            size_hint_y=0.1,
            font_size='16sp'
        ))
        
        layout.add_widget(Label(text='Valor a adicionar (R$):', color=COR_TEXTO_CLARO))
        valor = TextInput(multiline=False, input_filter='float', font_size='18sp', foreground_color=COR_TEXTO, background_color=COR_FUNDO_INPUT)
        layout.add_widget(valor)
        
        botoes = BoxLayout(orientation='horizontal', size_hint_y=0.2, spacing=10)
        btn_salvar = BotaoArredondado(text='Adicionar', background_color=COR_BOTAO_VERDE)
        btn_cancelar = BotaoArredondado(text='Cancelar', background_color=COR_BOTAO_VERMELHO)
        botoes.add_widget(btn_salvar)
        botoes.add_widget(btn_cancelar)
        layout.add_widget(botoes)
        
        popup = Popup(
            title='Adicionar Valor',
            content=layout,
            size_hint=(0.8, 0.5),
            background_color=COR_FUNDO_POPUP,
            title_color=COR_TEXTO_CLARO
        )
        
        def salvar(*args):
            if not valor.text:
                self._mostrar_erro_meta("Digite um valor!")
                return
            
            try:
                v = float(valor.text.replace(',', '.'))
                if v <= 0:
                    self._mostrar_erro_meta("Valor deve ser positivo!")
                    return
                
                if v > restante + 0.01:
                    self._mostrar_erro_meta(f"Valor excede o necessário!\nFaltam {texto_restante}")
                    return
                
                self.gerenciador_metas.adicionar_valor(btn.meta_id, v)
                popup.dismiss()
                self.carregar_metas()
                
                if abs(v - restante) < 0.01:
                    self._mostrar_sucesso_meta("🎉 Meta concluída! Parabéns!")
                else:
                    self._mostrar_sucesso_meta("Valor adicionado com sucesso!")
                
            except ValueError:
                self._mostrar_erro_meta("Valor inválido!")
        
        btn_salvar.bind(on_press=salvar)
        btn_cancelar.bind(on_press=popup.dismiss)
        popup.open()
    
    def editar_meta(self, btn, popup_pai):
        """Popup para editar meta"""
        layout = BoxLayout(orientation='vertical', spacing=15, padding=20)
        with layout.canvas.before:
            Color(*COR_FUNDO_POPUP)
            Rectangle(pos=layout.pos, size=layout.size)
        
        layout.add_widget(Label(
            text='✏️ EDITAR META',
            font_size='20sp',
            bold=True,
            color=COR_TEXTO_CLARO,
            size_hint_y=0.15
        ))
        
        form = BoxLayout(orientation='vertical', spacing=12, size_hint_y=0.6)
        
        form.add_widget(Label(text='Nome da meta:', halign='left', color=COR_TEXTO_CLARO))
        nome = TextInput(text=btn.meta_nome, multiline=False, font_size='16sp', foreground_color=COR_TEXTO, background_color=COR_FUNDO_INPUT)
        form.add_widget(nome)
        
        form.add_widget(Label(text='Valor alvo (R$):', halign='left', color=COR_TEXTO_CLARO))
        valor = TextInput(
            text=f"{btn.valor_alvo:.2f}".replace('.', ','),
            multiline=False,
            input_filter='float',
            font_size='16sp',
            foreground_color=COR_TEXTO,
            background_color=COR_FUNDO_INPUT
        )
        form.add_widget(valor)
        
        form.add_widget(Label(text='Data limite (AAAA-MM-DD):', halign='left', color=COR_TEXTO_CLARO))
        data = TextInput(text=btn.data_limite, multiline=False, font_size='16sp', foreground_color=COR_TEXTO, background_color=COR_FUNDO_INPUT)
        form.add_widget(data)
        
        layout.add_widget(form)
        
        botoes = BoxLayout(orientation='horizontal', size_hint_y=0.15, spacing=10)
        btn_salvar = BotaoArredondado(text='Salvar', background_color=COR_BOTAO_VERDE)
        btn_cancelar = BotaoArredondado(text='Cancelar', background_color=COR_BOTAO_VERMELHO)
        botoes.add_widget(btn_salvar)
        botoes.add_widget(btn_cancelar)
        layout.add_widget(botoes)
        
        popup = Popup(
            title='Editar Meta',
            content=layout,
            size_hint=(0.9, 0.6),
            background_color=COR_FUNDO_POPUP,
            title_color=COR_TEXTO_CLARO
        )
        
        def salvar(*args):
            if not nome.text or not valor.text or not data.text:
                self._mostrar_erro_meta("Preencha todos os campos!")
                return
            
            try:
                v = float(valor.text.replace(',', '.'))
                if v <= 0:
                    self._mostrar_erro_meta("Valor deve ser positivo!")
                    return
                
                try:
                    datetime.strptime(data.text, '%Y-%m-%d')
                except:
                    self._mostrar_erro_meta("Data inválida! Use AAAA-MM-DD")
                    return
                
                self.db.update_meta(btn.meta_id, nome.text, v, data.text)
                popup.dismiss()
                self.carregar_metas()
                self._mostrar_sucesso_meta("Meta atualizada com sucesso!")
                
            except ValueError:
                self._mostrar_erro_meta("Valor inválido!")
        
        btn_salvar.bind(on_press=salvar)
        btn_cancelar.bind(on_press=popup.dismiss)
        popup.open()
    
    def excluir_meta(self, btn, popup_pai):
        """Confirma exclusão de meta"""
        content = BoxLayout(orientation='vertical', spacing=15, padding=20)
        with content.canvas.before:
            Color(*COR_FUNDO_POPUP)
            Rectangle(pos=content.pos, size=content.size)
        
        content.add_widget(Label(
            text=f'Excluir meta "{btn.meta_nome}"?',
            font_size='16sp',
            color=COR_TEXTO_CLARO
        ))
        
        botoes = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.4)
        btn_sim = BotaoArredondado(text='Sim', background_color=COR_BOTAO_VERDE)
        btn_nao = BotaoArredondado(text='Não', background_color=COR_BOTAO_VERMELHO)
        botoes.add_widget(btn_sim)
        botoes.add_widget(btn_nao)
        content.add_widget(botoes)
        
        popup = Popup(
            title='Confirmar',
            content=content,
            size_hint=(0.6, 0.3),
            background_color=COR_FUNDO_POPUP,
            title_color=COR_TEXTO_CLARO
        )
        
        def confirmar(x):
            self.gerenciador_metas.excluir_meta(btn.meta_id)
            popup.dismiss()
            self.carregar_metas()
            self._mostrar_sucesso_meta("Meta excluída!")
        
        btn_sim.bind(on_press=confirmar)
        btn_nao.bind(on_press=popup.dismiss)
        popup.open()
    
    def _mostrar_sucesso_meta(self, mensagem):
        """Mostra popup de sucesso para metas"""
        popup = Popup(
            title='Sucesso',
            content=Label(text=f'✅ {mensagem}', color=COR_TEXTO_CLARO),
            size_hint=(0.6, 0.3),
            background_color=COR_FUNDO_POPUP,
            title_color=COR_TEXTO_CLARO
        )
        popup.open()
    
    def _mostrar_erro_meta(self, mensagem):
        """Mostra popup de erro para metas"""
        popup = Popup(
            title='Erro',
            content=Label(text=f'❌ {mensagem}', color=COR_TEXTO_CLARO),
            size_hint=(0.6, 0.3),
            background_color=COR_FUNDO_POPUP,
            title_color=COR_TEXTO_CLARO
        )
        popup.open()


if __name__ == '__main__':
    ControleFinanceiroApp().run()