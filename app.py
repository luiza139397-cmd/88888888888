import tkinter as tk
from tkinter import ttk

from config import APP_TITLE, DEFAULT_ACCOUNT_TYPE, DEFAULT_AMOUNT, DEFAULT_ASSET, DEFAULT_EXPIRATION, PREPARE_SECONDS_OPTIONS, THEME
from cashflow import load_cashflow, register_result, register_signal, set_initial_balance
from engine import BotEngine
from platforms import PLATFORM_MAP
from telegram_service import TelegramService


class BotApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("860x560")
        self.root.minsize(780, 500)
        self.root.configure(bg=THEME["bg"])

        self.platform_vars = {name: tk.BooleanVar(value=(name == "IQ Option")) for name in PLATFORM_MAP}
        self.telegram_enabled = tk.BooleanVar(value=False)
        self.auto_trade_var = tk.BooleanVar(value=True)
        self.account_type_var = tk.StringVar(value=DEFAULT_ACCOUNT_TYPE)
        self.asset_var = tk.StringVar(value=DEFAULT_ASSET)
        self.amount_var = tk.StringVar(value=str(DEFAULT_AMOUNT))
        self.expiration_var = tk.StringVar(value=str(DEFAULT_EXPIRATION))
        self.prepare_seconds_var = tk.StringVar(value=str(PREPARE_SECONDS_OPTIONS[0]))
        self.status_var = tk.StringVar(value="Bot desligado.")
        self.run_state_var = tk.StringVar(value="BOT DESLIGADO")
        self.run_state_color = THEME["danger"]
        self.last_activity_var = tk.StringVar(value="Ultima atividade: --:--:--")
        self.action_message_var = tk.StringVar(value="Preencha os dados e clique em Iniciar Bot.")
        self.chart_title_var = tk.StringVar(value="Grafico aguardando dados.")
        self.cashflow_balance_var = tk.StringVar(value="R$0.00")
        self.cashflow_profit_var = tk.StringVar(value="R$0.00")
        self.cashflow_gross_profit_var = tk.StringVar(value="R$0.00")
        self.cashflow_gross_loss_var = tk.StringVar(value="R$0.00")
        self.cashflow_last_result_var = tk.StringVar(value="R$0.00")
        self.cashflow_updated_var = tk.StringVar(value="--")
        self.cashflow_wins_var = tk.StringVar(value="0")
        self.cashflow_losses_var = tk.StringVar(value="0")
        self.cashflow_signals_var = tk.StringVar(value="0")
        self.cashflow_initial_var = tk.StringVar(value="100")
        self.manual_asset_var = tk.StringVar(value=DEFAULT_ASSET)
        self.manual_result_var = tk.StringVar(value="10")

        self.engine = BotEngine(self.add_log, self.set_status, self.show_signal, self.update_chart, self.handle_engine_event)
        self.log_queue = []
        self.chart_queue = []

        self._build_styles()
        self._build_layout()
        self._refresh_cashflow()
        self._flush_logs()
        self._flush_chart_updates()

    def _build_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Card.TFrame", background=THEME["panel"])
        style.configure("CardAlt.TFrame", background=THEME["panel_alt"])
        style.configure("Title.TLabel", background=THEME["bg"], foreground=THEME["text"], font=("Segoe UI Semibold", 18))
        style.configure("Sub.TLabel", background=THEME["bg"], foreground=THEME["muted"], font=("Segoe UI", 9))
        style.configure("Card.TLabel", background=THEME["panel"], foreground=THEME["text"], font=("Segoe UI", 9))
        style.configure("Accent.TButton", font=("Segoe UI Semibold", 10))
        style.configure("Bot.TNotebook", background=THEME["bg"], borderwidth=0)
        style.configure("Bot.TNotebook.Tab", background=THEME["panel"], foreground=THEME["text"], padding=(10, 6), font=("Segoe UI Semibold", 9))
        style.map("Bot.TNotebook.Tab", background=[("selected", THEME["accent_alt"])], foreground=[("selected", "white")])

    def _build_layout(self):
        header = tk.Frame(self.root, bg=THEME["bg"])
        header.pack(fill="x", padx=14, pady=(12, 8))

        tk.Label(header, text="Multi Platform Signal Bot", bg=THEME["bg"], fg=THEME["text"], font=("Segoe UI Semibold", 18)).pack(anchor="w")
        tk.Label(
            header,
            text="Projeto novo para IQ Option, Quotex e Exnova com Telegram opcional.",
            bg=THEME["bg"],
            fg=THEME["muted"],
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(4, 0))

        status_bar = tk.Frame(header, bg=THEME["panel"], highlightthickness=1, highlightbackground="#263040")
        status_bar.pack(fill="x", pady=(8, 0))
        self.run_state_badge = tk.Label(
            status_bar,
            textvariable=self.run_state_var,
            bg=self.run_state_color,
            fg="white",
            font=("Segoe UI Semibold", 9),
            padx=8,
            pady=4,
        )
        self.run_state_badge.pack(side="left", padx=8, pady=8)
        tk.Label(
            status_bar,
            textvariable=self.last_activity_var,
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 9),
        ).pack(side="left", padx=(0, 8))
        tk.Label(
            status_bar,
            textvariable=self.status_var,
            bg=THEME["panel"],
            fg=THEME["warning"],
            font=("Segoe UI", 9),
        ).pack(side="right", padx=8)

        body = tk.Frame(self.root, bg=THEME["bg"])
        body.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        self.notebook = ttk.Notebook(body, style="Bot.TNotebook")
        self.notebook.pack(fill="both", expand=True)

        trading_tab = tk.Frame(self.notebook, bg=THEME["bg"])
        telegram_tab = tk.Frame(self.notebook, bg=THEME["bg"])
        chart_tab = tk.Frame(self.notebook, bg=THEME["bg"])
        cashflow_tab = tk.Frame(self.notebook, bg=THEME["bg"])
        logs_tab = tk.Frame(self.notebook, bg=THEME["bg"])

        self.notebook.add(trading_tab, text="Operacao")
        self.notebook.add(telegram_tab, text="Telegram")
        self.notebook.add(chart_tab, text="Graficos")
        self.notebook.add(cashflow_tab, text="Fluxo de Caixa")
        self.notebook.add(logs_tab, text="Logs")

        self._build_trading_tab(trading_tab)
        self._build_telegram_tab(telegram_tab)
        self._build_chart_tab(chart_tab)
        self._build_cashflow_tab(cashflow_tab)
        self._build_logs_tab(logs_tab)

    def _build_trading_tab(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)
        parent.grid_rowconfigure(2, weight=1)
        self._build_operation_notice(parent)
        self._build_trading_controls(parent)
        self._build_platform_card(parent)
        self._build_settings_card(parent)

    def _build_operation_notice(self, parent):
        notice = tk.Frame(parent, bg=THEME["panel_alt"], highlightthickness=1, highlightbackground="#263040")
        notice.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        tk.Label(notice, text="Pronto Para Iniciar", bg=THEME["panel_alt"], fg=THEME["text"], font=("Segoe UI Semibold", 11)).pack(anchor="w", padx=12, pady=(10, 4))
        tk.Label(notice, textvariable=self.action_message_var, bg=THEME["panel_alt"], fg=THEME["text"], font=("Segoe UI", 9)).pack(anchor="w", padx=12, pady=(4, 8))
        actions = tk.Frame(notice, bg=THEME["panel_alt"])
        actions.pack(fill="x", padx=12, pady=(0, 10))
        tk.Button(actions, text="Abrir Logs", command=self.open_logs_tab, bg="#39424e", fg="white", relief="flat", font=("Segoe UI Semibold", 9)).pack(side="left")

    def _build_trading_controls(self, parent):
        controls = tk.Frame(parent, bg=THEME["bg"])
        controls.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        controls.grid_columnconfigure(0, weight=1)
        controls.grid_columnconfigure(1, weight=1)

        tk.Button(
            controls,
            text="LIGAR BOT",
            command=self.start_bot,
            bg=THEME["accent"],
            fg="white",
            relief="flat",
            font=("Segoe UI Semibold", 10),
            height=1,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        tk.Button(
            controls,
            text="DESLIGAR BOT",
            command=self.stop_bot,
            bg=THEME["danger"],
            fg="white",
            relief="flat",
            font=("Segoe UI Semibold", 10),
            height=1,
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def _build_platform_card(self, parent):
        card = tk.Frame(parent, bg=THEME["panel"], bd=0, highlightthickness=1, highlightbackground="#263040")
        card.grid(row=2, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10))

        tk.Label(card, text="Plataformas", bg=THEME["panel"], fg=THEME["text"], font=("Segoe UI Semibold", 11)).pack(anchor="w", padx=12, pady=(10, 4))
        tk.Label(card, text="Marque onde voce quer buscar sinais ou operar.", bg=THEME["panel"], fg=THEME["muted"], font=("Segoe UI", 8)).pack(anchor="w", padx=12, pady=(0, 6))

        for name, variable in self.platform_vars.items():
            tk.Checkbutton(
                card,
                text=name,
                variable=variable,
                bg=THEME["panel"],
                fg=THEME["text"],
                selectcolor=THEME["input_bg"],
                activebackground=THEME["panel"],
                activeforeground=THEME["text"],
                font=("Segoe UI", 9),
            ).pack(anchor="w", padx=12, pady=2)

    def _build_settings_card(self, parent):
        card = tk.Frame(parent, bg=THEME["panel"], bd=0, highlightthickness=1, highlightbackground="#263040")
        card.grid(row=2, column=1, sticky="nsew", pady=(0, 10))

        tk.Label(card, text="Operacao", bg=THEME["panel"], fg=THEME["text"], font=("Segoe UI Semibold", 11)).pack(anchor="w", padx=12, pady=(10, 8))

        self.email_entry = self._labeled_entry(card, "E-mail", "")
        self.password_entry = self._labeled_entry(card, "Senha", "", show="*")
        self.asset_entry = self._labeled_entry(card, "Ativos", self.asset_var.get())
        self.amount_entry = self._labeled_entry(card, "Valor por entrada", self.amount_var.get())
        self.expiration_entry = self._labeled_entry(card, "Expiracao (min)", self.expiration_var.get())

        account_row = tk.Frame(card, bg=THEME["panel"])
        account_row.pack(fill="x", padx=12, pady=(6, 3))
        tk.Label(account_row, text="Conta", bg=THEME["panel"], fg=THEME["muted"], font=("Segoe UI", 8)).pack(anchor="w")
        tk.OptionMenu(account_row, self.account_type_var, "PRACTICE", "REAL").pack(fill="x", pady=(4, 0))

        prepare_row = tk.Frame(card, bg=THEME["panel"])
        prepare_row.pack(fill="x", padx=12, pady=(6, 3))
        tk.Label(prepare_row, text="Avisar antes do fechamento", bg=THEME["panel"], fg=THEME["muted"], font=("Segoe UI", 8)).pack(anchor="w")
        tk.OptionMenu(prepare_row, self.prepare_seconds_var, *[str(value) for value in PREPARE_SECONDS_OPTIONS]).pack(fill="x", pady=(4, 0))

        tk.Checkbutton(
            card,
            text="Operar automaticamente quando surgir sinal (ligado por padrao)",
            variable=self.auto_trade_var,
            bg=THEME["panel"],
            fg=THEME["text"],
            selectcolor=THEME["input_bg"],
            activebackground=THEME["panel"],
            activeforeground=THEME["text"],
            font=("Segoe UI", 9),
        ).pack(anchor="w", padx=12, pady=(8, 10))

    def _build_telegram_tab(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)
        card = tk.Frame(parent, bg=THEME["panel_alt"], bd=0, highlightthickness=1, highlightbackground="#263040")
        card.grid(row=0, column=0, sticky="nsew")

        tk.Label(card, text="Telegram", bg=THEME["panel_alt"], fg=THEME["text"], font=("Segoe UI Semibold", 11)).pack(anchor="w", padx=12, pady=(10, 4))
        tk.Label(card, text="Ative se quiser receber os sinais no Telegram.", bg=THEME["panel_alt"], fg=THEME["muted"], font=("Segoe UI", 8)).pack(anchor="w", padx=12)

        tk.Checkbutton(
            card,
            text="Enviar sinais para Telegram",
            variable=self.telegram_enabled,
            bg=THEME["panel_alt"],
            fg=THEME["text"],
            selectcolor=THEME["input_bg"],
            activebackground=THEME["panel_alt"],
            activeforeground=THEME["text"],
            font=("Segoe UI", 9),
        ).pack(anchor="w", padx=12, pady=8)

        self.telegram_token_entry = self._labeled_entry(card, "Bot Token", "", parent_bg=THEME["panel_alt"])
        self.telegram_chat_entry = self._labeled_entry(card, "Chat ID", "", parent_bg=THEME["panel_alt"])

        signal_box = tk.Frame(card, bg="#0f141a", highlightthickness=1, highlightbackground="#263040")
        signal_box.pack(fill="both", expand=True, padx=12, pady=(8, 12))
        tk.Label(signal_box, text="Ultimo sinal", bg="#0f141a", fg=THEME["muted"], font=("Segoe UI", 8)).pack(anchor="w", padx=10, pady=(8, 4))
        self.signal_text = tk.Text(signal_box, height=6, bg="#0f141a", fg=THEME["text"], relief="flat", wrap="word", font=("Consolas", 8))
        self.signal_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _build_chart_tab(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)
        card = tk.Frame(parent, bg=THEME["panel_alt"], bd=0, highlightthickness=1, highlightbackground="#263040")
        card.grid(row=0, column=0, sticky="nsew")

        top = tk.Frame(card, bg=THEME["panel_alt"])
        top.pack(fill="x", padx=16, pady=(14, 6))
        tk.Label(top, text="Grafico de Velas", bg=THEME["panel_alt"], fg=THEME["text"], font=("Segoe UI Semibold", 11)).pack(anchor="w")
        tk.Label(top, textvariable=self.chart_title_var, bg=THEME["panel_alt"], fg=THEME["muted"], font=("Segoe UI", 8)).pack(anchor="w", pady=(4, 0))

        self.chart_canvas = tk.Canvas(card, bg="#0b1016", highlightthickness=0)
        self.chart_canvas.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.chart_canvas.bind("<Configure>", lambda event: self._draw_placeholder_chart())
        self._draw_placeholder_chart()

    def _build_logs_tab(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)
        card = tk.Frame(parent, bg=THEME["panel_alt"], bd=0, highlightthickness=1, highlightbackground="#263040")
        card.grid(row=0, column=0, sticky="nsew")

        top = tk.Frame(card, bg=THEME["panel_alt"])
        top.pack(fill="x", padx=16, pady=(14, 6))
        tk.Label(top, text="Logs", bg=THEME["panel_alt"], fg=THEME["text"], font=("Segoe UI Semibold", 11)).pack(anchor="w")
        tk.Label(top, textvariable=self.status_var, bg=THEME["panel_alt"], fg=THEME["warning"], font=("Segoe UI", 8)).pack(anchor="w", pady=(4, 0))

        self.log_text = tk.Text(card, bg="#0b1016", fg="#9ee57b", relief="flat", wrap="word", font=("Consolas", 8))
        self.log_text.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def _build_cashflow_tab(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)
        parent.grid_rowconfigure(1, weight=1)

        summary = tk.Frame(parent, bg=THEME["panel"], bd=0, highlightthickness=1, highlightbackground="#263040")
        summary.grid(row=0, column=0, columnspan=2, sticky="nsew", pady=(0, 10))

        tk.Label(summary, text="Fluxo de Caixa", bg=THEME["panel"], fg=THEME["text"], font=("Segoe UI Semibold", 11)).pack(anchor="w", padx=12, pady=(10, 6))
        balance_row = tk.Frame(summary, bg=THEME["panel"])
        balance_row.pack(fill="x", padx=12, pady=(0, 8))
        tk.Label(balance_row, text="Banca inicial", bg=THEME["panel"], fg=THEME["muted"], font=("Segoe UI", 8)).pack(anchor="w")
        self.initial_balance_entry = tk.Entry(balance_row, textvariable=self.cashflow_initial_var, bg=THEME["input_bg"], fg=THEME["text"], insertbackground=THEME["text"], relief="flat", font=("Segoe UI", 9))
        self.initial_balance_entry.pack(fill="x", pady=(4, 6), ipady=4)
        tk.Button(balance_row, text="Salvar banca", command=self.save_initial_balance, bg=THEME["accent_alt"], fg="white", relief="flat", font=("Segoe UI Semibold", 9)).pack(anchor="w")

        manual_row = tk.Frame(summary, bg=THEME["panel"])
        manual_row.pack(fill="x", padx=12, pady=(0, 10))
        manual_row.grid_columnconfigure(0, weight=2)
        manual_row.grid_columnconfigure(1, weight=1)
        tk.Label(manual_row, text="Ativo manual", bg=THEME["panel"], fg=THEME["muted"], font=("Segoe UI", 8)).grid(row=0, column=0, sticky="w")
        tk.Label(manual_row, text="Valor", bg=THEME["panel"], fg=THEME["muted"], font=("Segoe UI", 8)).grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.manual_asset_entry = tk.Entry(manual_row, textvariable=self.manual_asset_var, bg=THEME["input_bg"], fg=THEME["text"], insertbackground=THEME["text"], relief="flat", font=("Segoe UI", 9))
        self.manual_asset_entry.grid(row=1, column=0, sticky="ew", pady=(4, 6))
        self.manual_result_entry = tk.Entry(manual_row, textvariable=self.manual_result_var, bg=THEME["input_bg"], fg=THEME["text"], insertbackground=THEME["text"], relief="flat", font=("Segoe UI", 9))
        self.manual_result_entry.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(4, 6))

        manual_buttons = tk.Frame(summary, bg=THEME["panel"])
        manual_buttons.pack(fill="x", padx=12, pady=(0, 10))
        tk.Button(manual_buttons, text="Lancar WIN", command=self.manual_win, bg=THEME["accent"], fg="white", relief="flat", font=("Segoe UI Semibold", 9)).pack(side="left", padx=(0, 8))
        tk.Button(manual_buttons, text="Lancar LOSS", command=self.manual_loss, bg=THEME["danger"], fg="white", relief="flat", font=("Segoe UI Semibold", 9)).pack(side="left")

        stats = tk.Frame(parent, bg=THEME["panel_alt"], bd=0, highlightthickness=1, highlightbackground="#263040")
        stats.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        tk.Label(stats, text="Resumo", bg=THEME["panel_alt"], fg=THEME["text"], font=("Segoe UI Semibold", 11)).pack(anchor="w", padx=12, pady=(10, 6))
        self._summary_line(stats, "Saldo atual", self.cashflow_balance_var)
        self._summary_line(stats, "Resultado acumulado", self.cashflow_profit_var)
        self._summary_line(stats, "Lucro bruto", self.cashflow_gross_profit_var)
        self._summary_line(stats, "Perda bruta", self.cashflow_gross_loss_var)
        self._summary_line(stats, "Ultimo resultado", self.cashflow_last_result_var)
        self._summary_line(stats, "Wins", self.cashflow_wins_var)
        self._summary_line(stats, "Losses", self.cashflow_losses_var)
        self._summary_line(stats, "Sinais", self.cashflow_signals_var)
        self._summary_line(stats, "Atualizado em", self.cashflow_updated_var)

        history = tk.Frame(parent, bg=THEME["panel_alt"], bd=0, highlightthickness=1, highlightbackground="#263040")
        history.grid(row=1, column=1, sticky="nsew")
        tk.Label(history, text="Historico", bg=THEME["panel_alt"], fg=THEME["text"], font=("Segoe UI Semibold", 11)).pack(anchor="w", padx=12, pady=(10, 6))
        self.cashflow_text = tk.Text(history, bg="#0b1016", fg=THEME["text"], relief="flat", wrap="word", font=("Consolas", 8))
        self.cashflow_text.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def _summary_line(self, parent, label, variable):
        row = tk.Frame(parent, bg=parent["bg"])
        row.pack(fill="x", padx=12, pady=3)
        tk.Label(row, text=label, bg=parent["bg"], fg=THEME["muted"], font=("Segoe UI", 8)).pack(anchor="w")
        tk.Label(row, textvariable=variable, bg=parent["bg"], fg=THEME["text"], font=("Segoe UI Semibold", 10)).pack(anchor="w")

    def _labeled_entry(self, parent, label, default_value, show=None, parent_bg=None):
        bg = parent_bg or THEME["panel"]
        wrapper = tk.Frame(parent, bg=bg)
        wrapper.pack(fill="x", padx=12, pady=3)
        tk.Label(wrapper, text=label, bg=bg, fg=THEME["muted"], font=("Segoe UI", 8)).pack(anchor="w")
        entry = tk.Entry(wrapper, bg=THEME["input_bg"], fg=THEME["text"], insertbackground=THEME["text"], relief="flat", font=("Segoe UI", 9), show=show)
        entry.pack(fill="x", pady=(4, 0), ipady=4)
        if default_value:
            entry.insert(0, default_value)
        return entry

    def add_log(self, message):
        self.log_queue.append(message)
        timestamp = message[1:9] if message.startswith("[") and len(message) >= 9 else "--:--:--"
        self.root.after(0, self.last_activity_var.set, f"Ultima atividade: {timestamp}")

    def _flush_logs(self):
        while self.log_queue:
            message = self.log_queue.pop(0)
            self.log_text.insert("end", message + "\n")
            self.log_text.see("end")
        self.root.after(120, self._flush_logs)

    def _flush_chart_updates(self):
        while self.chart_queue:
            platform_name, asset, candles = self.chart_queue.pop(0)
            self._draw_candles(platform_name, asset, candles)
        self.root.after(180, self._flush_chart_updates)

    def set_status(self, message):
        self.root.after(0, self.status_var.set, message)

    def _set_running_indicator(self, running):
        self.run_state_var.set("BOT RODANDO" if running else "BOT DESLIGADO")
        self.run_state_badge.configure(bg=THEME["accent"] if running else THEME["danger"])

    def show_signal(self, message):
        def _update():
            self.signal_text.delete("1.0", "end")
            self.signal_text.insert("end", message)
        self.root.after(0, _update)

    def update_chart(self, platform_name, asset, candles):
        self.chart_queue.append((platform_name, asset, candles))

    def _build_platform_objects(self):
        selected = [name for name, variable in self.platform_vars.items() if variable.get()]
        if not selected:
            raise ValueError("Selecione pelo menos uma plataforma.")

        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        account_type = self.account_type_var.get().strip()
        return [PLATFORM_MAP[name](email, password, account_type) for name in selected]

    def _build_assets(self):
        raw_assets = self.asset_entry.get().strip()
        assets = [asset.strip() for asset in raw_assets.split(",") if asset.strip()]
        if not assets:
            raise ValueError("Informe pelo menos um ativo.")
        return assets

    def _build_telegram(self):
        return TelegramService(
            enabled=self.telegram_enabled.get(),
            token=self.telegram_token_entry.get(),
            chat_id=self.telegram_chat_entry.get(),
        )

    def start_bot(self):
        try:
            platforms = self._build_platform_objects()
            assets = self._build_assets()
            amount = float(self.amount_entry.get().strip())
            expiration = int(self.expiration_entry.get().strip())
            prepare_seconds = int(self.prepare_seconds_var.get().strip())
            telegram_service = self._build_telegram()
        except Exception as exc:
            self.add_log(f"[ERRO] {exc}")
            self.action_message_var.set(str(exc))
            self.set_status("Revise os campos antes de iniciar.")
            return

        ok, message = self.engine.start(
            platforms=platforms,
            assets=assets,
            amount=amount,
            expiration=expiration,
            telegram_service=telegram_service,
            auto_trade=self.auto_trade_var.get(),
            prepare_seconds=prepare_seconds,
        )
        self.add_log(message)
        self.set_status(message)
        self.action_message_var.set(message)
        if ok:
            self._set_running_indicator(True)
            if self.auto_trade_var.get():
                self.add_log("Modo automatico ligado: quando surgir sinal, o bot tenta entrar sozinho no tempo da vela.")
            else:
                self.add_log("Modo automatico desligado: o bot vai apenas avisar o sinal sem operar.")

    def stop_bot(self):
        ok, message = self.engine.stop()
        self.add_log(message)
        self.set_status(message)
        self.action_message_var.set(message)
        self._set_running_indicator(False)

    def _draw_placeholder_chart(self):
        if not hasattr(self, "chart_canvas"):
            return
        canvas = self.chart_canvas
        canvas.delete("all")
        width = max(canvas.winfo_width(), 200)
        height = max(canvas.winfo_height(), 200)
        canvas.create_text(width / 2, height / 2, text="Aguardando velas do bot...", fill=THEME["muted"], font=("Segoe UI", 10))

    def _draw_candles(self, platform_name, asset, candles):
        if not candles:
            self._draw_placeholder_chart()
            return

        canvas = self.chart_canvas
        canvas.delete("all")
        width = max(canvas.winfo_width(), 300)
        height = max(canvas.winfo_height(), 240)
        margin_left = 24
        margin_top = 20
        margin_bottom = 28
        margin_right = 16
        chart_width = width - margin_left - margin_right
        chart_height = height - margin_top - margin_bottom

        highs = [float(candle["high"]) for candle in candles]
        lows = [float(candle["low"]) for candle in candles]
        price_max = max(highs)
        price_min = min(lows)
        price_range = price_max - price_min or 1

        self.chart_title_var.set(f"{platform_name} | {asset} | {len(candles)} velas")

        for index in range(5):
            y = margin_top + (chart_height / 4) * index
            canvas.create_line(margin_left, y, width - margin_right, y, fill="#1c2633")

        candle_width = max(6, chart_width / max(len(candles), 1) * 0.55)
        gap = chart_width / max(len(candles), 1)

        def price_to_y(price):
            normalized = (price - price_min) / price_range
            return margin_top + chart_height - (normalized * chart_height)

        for index, candle in enumerate(candles):
            center_x = margin_left + gap * index + gap / 2
            open_price = float(candle["open"])
            close_price = float(candle["close"])
            high_price = float(candle["high"])
            low_price = float(candle["low"])

            open_y = price_to_y(open_price)
            close_y = price_to_y(close_price)
            high_y = price_to_y(high_price)
            low_y = price_to_y(low_price)

            color = "#2ea043" if close_price >= open_price else "#f85149"
            top = min(open_y, close_y)
            bottom = max(open_y, close_y)

            canvas.create_line(center_x, high_y, center_x, low_y, fill=color, width=1)
            canvas.create_rectangle(
                center_x - candle_width / 2,
                top,
                center_x + candle_width / 2,
                bottom if bottom > top else top + 1,
                fill=color,
                outline=color,
            )

        canvas.create_text(margin_left, margin_top - 8, text=f"{price_max:.5f}", anchor="w", fill=THEME["muted"], font=("Consolas", 8))
        canvas.create_text(margin_left, height - 10, text=f"{price_min:.5f}", anchor="w", fill=THEME["muted"], font=("Consolas", 8))

    def handle_engine_event(self, event_type, payload):
        if event_type == "signal":
            register_signal()
            self.root.after(0, self._refresh_cashflow)
            return
        if event_type == "trade_result":
            register_result(payload["platform"], payload["asset"], payload["result"])
            self.root.after(0, self._refresh_cashflow)

    def _refresh_cashflow(self):
        data = load_cashflow()
        self.cashflow_initial_var.set(str(data["initial_balance"]))
        self.cashflow_balance_var.set(f"R${data['current_balance']:.2f}")
        total = data["current_balance"] - data["initial_balance"]
        self.cashflow_profit_var.set(f"R${total:.2f}")
        self.cashflow_gross_profit_var.set(f"R${data.get('gross_profit', 0.0):.2f}")
        self.cashflow_gross_loss_var.set(f"R${data.get('gross_loss', 0.0):.2f}")
        self.cashflow_last_result_var.set(f"R${data.get('last_result', 0.0):.2f}")
        self.cashflow_updated_var.set(data.get("updated_at", "--") or "--")
        self.cashflow_wins_var.set(str(data["wins"]))
        self.cashflow_losses_var.set(str(data["losses"]))
        self.cashflow_signals_var.set(str(data["signals"]))
        if hasattr(self, "cashflow_text"):
            self.cashflow_text.delete("1.0", "end")
            for item in reversed(data["history"][-20:]):
                self.cashflow_text.insert(
                    "end",
                    f"{item['time']} | {item['platform']} | {item['asset']} | R${item['result']:.2f} | saldo R${item['balance_after']:.2f}\n",
                )

    def save_initial_balance(self):
        try:
            value = float(self.initial_balance_entry.get().strip())
            set_initial_balance(value)
            self._refresh_cashflow()
            self.add_log("Fluxo de caixa reiniciado com a nova banca.")
        except Exception as exc:
            self.add_log(f"[ERRO] Nao foi possivel salvar a banca: {exc}")

    def _register_manual_result(self, multiplier):
        try:
            asset = self.manual_asset_entry.get().strip() or "MANUAL"
            value = abs(float(self.manual_result_entry.get().strip()))
            result = value * multiplier
            register_result("MANUAL", asset, result)
            self._refresh_cashflow()
            self.add_log(f"Fluxo manual atualizado: {asset} | R${result:.2f}")
        except Exception as exc:
            self.add_log(f"[ERRO] Nao foi possivel lancar resultado manual: {exc}")

    def manual_win(self):
        self._register_manual_result(1)

    def manual_loss(self):
        self._register_manual_result(-1)

    def open_logs_tab(self):
        self.notebook.select(4)
