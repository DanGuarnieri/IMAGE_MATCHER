import queue
import threading
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog, messagebox

from config import (
    APP_TITLE, WINDOW_SIZE, MIN_WINDOW_SIZE,
    DEFAULT_TOLERANCE, MIN_TOLERANCE, MAX_TOLERANCE
)
from core.comparator import comparar_imagens
from core.excel_export import salvar_planilha
from .logger import AppLogger


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ImageMatcherApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(WINDOW_SIZE)
        self.minsize(*MIN_WINDOW_SIZE)

        self.eventos = queue.Queue()
        self.cancelar = threading.Event()
        self.thread = None
        self.executando = False

        self.pasta_ref = ctk.StringVar()
        self.pasta_destino = ctk.StringVar()
        self.arquivo_saida = ctk.StringVar(value=str(Path.home() / "Desktop" / "image_matcher_resultado.xlsx"))
        self.tolerancia = ctk.IntVar(value=DEFAULT_TOLERANCE)

        self._montar_interface()
        self.after(100, self._processar_eventos)

    def _montar_interface(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, corner_radius=14)
        header.grid(row=0, column=0, padx=18, pady=(18, 10), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text="IMAGE MATCHER",
            font=ctk.CTkFont(size=25, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(16, 2), sticky="w")
        ctk.CTkLabel(
            header, text="Identificação de imagens semelhantes usando pHash",
            text_color="gray70", font=ctk.CTkFont(size=12)
        ).grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")

        conteudo = ctk.CTkFrame(self, fg_color="transparent")
        conteudo.grid(row=1, column=0, padx=18, pady=(0, 18), sticky="nsew")
        conteudo.grid_columnconfigure(0, weight=5)
        conteudo.grid_columnconfigure(1, weight=6)
        conteudo.grid_rowconfigure(0, weight=1)

        esquerda = ctk.CTkFrame(conteudo, corner_radius=14)
        esquerda.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        esquerda.grid_columnconfigure(0, weight=1)

        direita = ctk.CTkFrame(conteudo, corner_radius=14)
        direita.grid(row=0, column=1, padx=(8, 0), sticky="nsew")
        direita.grid_columnconfigure(0, weight=1)
        direita.grid_rowconfigure(4, weight=1)

        self._titulo_secao(esquerda, "CONFIGURAÇÃO", 0)

        self._campo_pasta(esquerda, "01  Pasta de referências", self.pasta_ref, 1)
        self._campo_pasta(esquerda, "02  Pasta de imagens para analisar", self.pasta_destino, 2)

        ctk.CTkLabel(
            esquerda, text="03  Arquivo Excel de saída",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=5, column=0, padx=18, pady=(18, 6), sticky="w")

        saida_frame = ctk.CTkFrame(esquerda, fg_color="transparent")
        saida_frame.grid(row=6, column=0, padx=18, sticky="ew")
        saida_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkEntry(saida_frame, textvariable=self.arquivo_saida).grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(saida_frame, text="Salvar em", width=95, command=self._selecionar_saida).grid(row=0, column=1, padx=(7, 0))

        ctk.CTkLabel(
            esquerda, text="04  Tolerância pHash",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=7, column=0, padx=18, pady=(22, 4), sticky="w")

        tol_linha = ctk.CTkFrame(esquerda, fg_color="transparent")
        tol_linha.grid(row=8, column=0, padx=18, sticky="ew")
        tol_linha.grid_columnconfigure(0, weight=1)
        self.tol_valor = ctk.CTkLabel(
            tol_linha, text=str(DEFAULT_TOLERANCE),
            font=ctk.CTkFont(size=14, weight="bold"), text_color="#60A5FA"
        )
        self.tol_valor.grid(row=0, column=1, padx=(10, 0))
        self.slider = ctk.CTkSlider(
            tol_linha, from_=MIN_TOLERANCE, to=MAX_TOLERANCE,
            number_of_steps=MAX_TOLERANCE, variable=self.tolerancia,
            command=self._atualizar_tolerancia
        )
        self.slider.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(
            esquerda,
            text="Menor valor = comparação mais rigorosa.\nMaior valor = aceita imagens mais diferentes.",
            text_color="gray65", justify="left",
            font=ctk.CTkFont(size=11)
        ).grid(row=9, column=0, padx=18, pady=(5, 15), sticky="w")

        self.btn_executar = ctk.CTkButton(
            esquerda, text="▶  EXECUTAR ANÁLISE", height=42,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._iniciar
        )
        self.btn_executar.grid(row=10, column=0, padx=18, pady=(8, 8), sticky="ew")

        self.btn_cancelar = ctk.CTkButton(
            esquerda, text="CANCELAR", height=34,
            fg_color="#7F1D1D", hover_color="#991B1B",
            command=self._cancelar, state="disabled"
        )
        self.btn_cancelar.grid(row=11, column=0, padx=18, pady=(0, 18), sticky="ew")

        self._titulo_secao(direita, "ACOMPANHAMENTO", 0)

        status = ctk.CTkFrame(direita, fg_color="transparent")
        status.grid(row=1, column=0, padx=18, pady=(4, 10), sticky="ew")
        status.grid_columnconfigure(0, weight=1)
        self.status_label = ctk.CTkLabel(status, text="Aguardando execução", text_color="gray70")
        self.status_label.grid(row=0, column=0, sticky="w")
        self.progresso_label = ctk.CTkLabel(status, text="0%")
        self.progresso_label.grid(row=0, column=1, sticky="e")
        self.barra = ctk.CTkProgressBar(direita)
        self.barra.grid(row=2, column=0, padx=18, pady=(0, 15), sticky="ew")
        self.barra.set(0)

        ctk.CTkLabel(
            direita, text="LOG DE EXECUÇÃO",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=3, column=0, padx=18, pady=(5, 6), sticky="nw")

        self.log_box = ctk.CTkTextbox(
            direita, corner_radius=10, font=ctk.CTkFont(family="Consolas", size=11),
            activate_scrollbars=True
        )
        self.log_box.grid(row=4, column=0, padx=18, pady=(0, 18), sticky="nsew")
        self.log_box.configure(state="disabled")
        self.logger = AppLogger(self.log_box)
        self.logger.log("INFO", "Sistema iniciado.")
        self.logger.log("INFO", "Selecione as pastas para começar.")

    def _titulo_secao(self, parent, texto, linha):
        ctk.CTkLabel(
            parent, text=texto, font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#60A5FA"
        ).grid(row=linha, column=0, padx=18, pady=(18, 10), sticky="w")

    def _campo_pasta(self, parent, titulo, variavel, linha):
        ctk.CTkLabel(
            parent, text=titulo, font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=linha * 2 - 1, column=0, padx=18, pady=(12, 6), sticky="w")
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=linha * 2, column=0, padx=18, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkEntry(frame, textvariable=variavel, placeholder_text="Selecione uma pasta...").grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(
            frame, text="Procurar", width=90,
            command=lambda v=variavel: self._selecionar_pasta(v)
        ).grid(row=0, column=1, padx=(7, 0))

    def _selecionar_pasta(self, variavel):
        pasta = filedialog.askdirectory()
        if pasta:
            variavel.set(pasta)

    def _selecionar_saida(self):
        arquivo = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Planilha Excel", "*.xlsx")],
            initialfile="image_matcher_resultado.xlsx"
        )
        if arquivo:
            self.arquivo_saida.set(arquivo)

    def _atualizar_tolerancia(self, valor):
        numero = int(round(float(valor)))
        self.tolerancia.set(numero)
        self.tol_valor.configure(text=str(numero))

    def _iniciar(self):
        if self.executando:
            return
        if not self.pasta_ref.get().strip() or not self.pasta_destino.get().strip():
            messagebox.showwarning("Pastas obrigatórias", "Selecione a pasta de referências e a pasta de imagens.")
            return
        if not self.arquivo_saida.get().strip():
            messagebox.showwarning("Saída obrigatória", "Escolha onde salvar o Excel.")
            return

        self.cancelar.clear()
        self.executando = True
        self.btn_executar.configure(state="disabled")
        self.btn_cancelar.configure(state="normal")
        self.barra.set(0)
        self.progresso_label.configure(text="0%")
        self.status_label.configure(text="Preparando análise...")
        self.logger.log("INFO", "Iniciando processamento.")
        self.logger.log("INFO", f"Tolerância pHash definida: {self.tolerancia.get()}")

        self.thread = threading.Thread(target=self._executar_worker, daemon=True)
        self.thread.start()

    def _executar_worker(self):
        def emitir(tipo, dado):
            self.eventos.put((tipo, dado))

        try:
            resultado = comparar_imagens(
                self.pasta_ref.get(), self.pasta_destino.get(),
                self.tolerancia.get(), emitir, self.cancelar
            )
            if resultado is None:
                emitir("cancelled", None)
                return

            caminho = salvar_planilha(resultado["resultados"], self.arquivo_saida.get())
            emitir("finished", (resultado, str(caminho)))
        except Exception as erro:
            emitir("error", str(erro))

    def _processar_eventos(self):
        try:
            while True:
                tipo, dado = self.eventos.get_nowait()

                if tipo == "info":
                    self.logger.log("INFO", dado)
                elif tipo == "warning":
                    self.logger.log("WARNING", dado)
                elif tipo == "progress":
                    atual, total, mensagem = dado
                    percentual = atual / total if total else 0
                    self.barra.set(percentual)
                    self.progresso_label.configure(text=f"{percentual:.0%}")
                    self.status_label.configure(text=mensagem)
                elif tipo == "finished":
                    resultado, caminho = dado
                    self._finalizar()
                    qtd = len(resultado["resultados"])
                    self.barra.set(1)
                    self.progresso_label.configure(text="100%")
                    self.status_label.configure(text="Análise concluída")
                    self.logger.log("SUCCESS", f"Análise concluída: {qtd} correspondência(s).")
                    self.logger.log("INFO", f"Planilha salva em: {caminho}")
                    self.logger.log("INFO", f"Imagens analisadas: {resultado['processadas']}")
                    if resultado["erros_referencia"] or resultado["erros_destino"]:
                        self.logger.log("WARNING", "Algumas imagens não puderam ser processadas.")
                    messagebox.showinfo(
                        "Processamento concluído",
                        f"Análise finalizada!\n\nCorrespondências: {qtd}\nPlanilha: {caminho}"
                    )
                elif tipo == "cancelled":
                    self._finalizar()
                    self.status_label.configure(text="Processamento cancelado")
                    self.logger.log("WARNING", "Processamento cancelado pelo usuário.")
                elif tipo == "error":
                    self._finalizar()
                    self.status_label.configure(text="Erro na execução")
                    self.logger.log("ERROR", dado)
                    messagebox.showerror("Erro na análise", dado)
        except queue.Empty:
            pass

        self.after(100, self._processar_eventos)

    def _cancelar(self):
        if self.executando:
            self.cancelar.set()
            self.btn_cancelar.configure(state="disabled")
            self.status_label.configure(text="Cancelando...")
            self.logger.log("WARNING", "Solicitação de cancelamento enviada.")

    def _finalizar(self):
        self.executando = False
        self.btn_executar.configure(state="normal")
        self.btn_cancelar.configure(state="disabled")
