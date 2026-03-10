# telas.py
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
import os

class TelaSplash(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical')
        
        # Fundo azul marinho
        with layout.canvas.before:
            Color(0.05, 0.1, 0.3, 1)  # Azul marinho
            self.rect = Rectangle(pos=layout.pos, size=layout.size)
        
        # Verificar se existe imagem de splash
        caminho_splash = 'images/splash.png'
        if os.path.exists(caminho_splash):
            from kivy.uix.image import Image as KivyImage
            splash_img = KivyImage(
                source=caminho_splash,
                allow_stretch=True,
                keep_ratio=True,
                size_hint=(0.8, 0.8),
                pos_hint={'center_x': 0.5, 'center_y': 0.5}
            )
            layout.add_widget(splash_img)
        else:
            # Fallback visual se não tiver imagem
            layout.add_widget(Label(
                text='💰\nCONTROLE\nFINANCEIRO',
                font_size='40sp',
                color=(1, 1, 1, 1),
                halign='center',
                valign='middle'
            ))
        
        self.add_widget(layout)
    
    def on_enter(self):
        # Animação de fade out após 2 segundos
        Clock.schedule_once(self.fade_out, 2)
    
    def fade_out(self, dt):
        anim = Animation(opacity=0, duration=0.5)
        anim.bind(on_complete=self.mudar_tela)
        anim.start(self)
    
    def mudar_tela(self, *args):
        self.manager.current = 'principal'


class TelaPrincipalScreen(Screen):
    """Wrapper Screen para a TelaPrincipal"""
    def __init__(self, tela_principal_instance, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(tela_principal_instance)