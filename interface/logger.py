from datetime import datetime


class AppLogger:
    def __init__(self, textbox):
        self.textbox = textbox

    def log(self, nivel, mensagem):
        horario = datetime.now().strftime("%H:%M:%S")
        cores = {
            "INFO": "#D1D5DB",
            "SUCCESS": "#4ADE80",
            "WARNING": "#FBBF24",
            "ERROR": "#F87171",
        }
        self.textbox.configure(state="normal")
        self.textbox.insert("end", f"[{horario}] [{nivel}] {mensagem}\n")
        self.textbox.configure(state="disabled")
        self.textbox.see("end")
