# Example 3 — Order check, return and warranty

**Demonstrates:** a non-trivial case that combines policies and data. The agent first explains the return policy (`get_store_policy`), then checks the customer's order only after the order number and the registered phone are given (`get_order_status`). The return window and the warranty that applies are computed in code from the order dates and the reference date (2026-03-25): the 7-day return period is over, and a defect is now covered by the manufacturer warranty.

Run with `python main.py --show-tools` (model `gemini-3.5-flash-lite`). Lines starting with `[tool]` show the tools the agent called.

```text
Clave: Olá! Eu sou a Clave, assistente virtual da Empório da Música. Como posso ajudar?  (digite 'sair' para encerrar)

Você: Me arrependi da minha compra, posso devolver meu pedido?
  [tool] get_store_policy {"topic":"returns_and_exchanges"}

Clave: Com certeza! Para compras feitas online, você tem até 7 dias corridos após o recebimento para solicitar a devolução por arrependimento, sem precisar justificar. O produto precisa estar na embalagem original, sem sinais de uso e com todos os acessórios e manuais.

Se quiser, me passa o número do seu pedido e o e-mail ou telefone cadastrado para eu dar uma olhada e confirmar se ainda está dentro do prazo para você!

Você: pedido 1, telefone (67) 98432-1098
  [tool] get_order_status {"contact":"(67) 98432-1098","order_id":1}

Clave: Oi, Pedro! Olhei aqui nos dados do seu pedido. Como ele foi entregue no dia 25 de outubro do ano passado, o prazo de 7 dias para devolução por arrependimento já passou, então não é mais possível fazer a devolução.

Se precisar de ajuda com qualquer outra coisa ou tiver alguma dúvida sobre o seu Martin D-28, é só me chamar!

Você: E se aparecer algum defeito, a garantia cobre?
  [tool] get_store_policy {"topic":"warranty"}

Clave: Como o seu pedido já passou do prazo inicial, a cobertura que se aplica agora para defeitos de fabricação é a garantia do fabricante. A gente pode ajudar a intermediar esse processo se você precisar, é só entrar em contato com a nossa equipe pelo WhatsApp ou telefone (67) 3341-4444 ou pelo e-mail contato@emporiodamusica.com.br.

Tem mais alguma coisa em que eu possa te ajudar hoje?

Você: sair

Clave: Até mais! Obrigada por falar com a Empório da Música.
```
