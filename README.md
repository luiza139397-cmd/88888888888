# Multi Platform Bot

Projeto novo, separado do bot antigo, com interface grafica e arquitetura modular.

Plataformas:
- IQ Option: integrado via `iqoptionapi` se a biblioteca estiver disponivel no ambiente.
- Quotex: estrutura pronta para integrar cliente/API.
- Exnova: estrutura pronta para integrar cliente/API.

Recursos:
- Interface grafica mais organizada.
- Selecao de varias plataformas.
- Envio opcional de sinais para Telegram.
- Loop continuo de analise sem parar apos o primeiro sinal.
- Logs em tempo real.
- Painel de fluxo de caixa com wins, losses e saldo.

Arquivos principais:
- `main.py`: inicia a interface.
- `app.py`: interface e orquestracao.
- `engine.py`: loop principal do bot.
- `platforms.py`: adaptadores das corretoras.
- `signals.py`: estrategia simples de sinal.
- `telegram_service.py`: envio opcional para Telegram.
- `cashflow.py`: controle de banca e historico de resultados.

Como rodar:

```bash
python main.py
```

Observacao:
- Quotex e Exnova estao com a base pronta, mas dependem da API/SDK que voce usa na sua maquina.
- A IQ Option pode funcionar direto se o modulo `iqoptionapi` estiver disponivel.
