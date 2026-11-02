# Example 4 — Store policies

**Demonstrates:** policy lookups. Address, opening hours and payment methods come from the store manual through `get_store_policy`. Opening hours are shown in Campo Grande and Brasília time, and the combined payment rule (above R$ 2,000) is applied.

Run with `python main.py --show-tools` (model `gemini-3.5-flash-lite`). Lines starting with `[tool]` show the tools the agent called.

```text
Clave: Olá! Eu sou a Clave, assistente virtual da Empório da Música. Como posso ajudar?  (digite 'sair' para encerrar)

Você: Qual o endereço da loja?
  [tool] get_store_policy {"topic":"about_store"}

Clave: Nossa loja fica na Rua 14 de Maio, 3200, no Centro, aqui em Campo Grande - MS, CEP 79202-333. Se precisar de mais alguma informação, é só falar!

Você: Qual o horário de vocês?
  [tool] get_store_policy {"topic":"opening_hours"}

Clave: Nosso horário de atendimento é de segunda a sexta-feira, das 09h00 às 18h00 (horário de MS) ou 10h00 às 19h00 (horário de Brasília). Aos sábados, funcionamos das 09h00 às 13h00 (horário de MS) ou 10h00 às 14h00 (horário de Brasília). Aos domingos e feriados estamos fechados. Precisa de mais alguma ajuda?

Você: Quais formas de pagamento vocês aceitam? Posso pagar metade no PIX e metade no cartão?
  [tool] get_store_policy {"topic":"payment"}

Clave: Aceitamos PIX com 5% de desconto, cartão de débito, cartão de crédito em até 12x sem juros (conforme as regras de parcela mínima) e boleto bancário. E sim, você pode combinar formas de pagamento, como PIX mais cartão, para compras acima de R$ 2.000,00.

Você: sair

Clave: Até mais! Obrigada por falar com a Empório da Música.
```
