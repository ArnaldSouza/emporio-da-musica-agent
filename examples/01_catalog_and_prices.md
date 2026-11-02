# Example 1 — Catalog search and prices

**Demonstrates:** data lookups. The agent searches the catalog with a price filter, then gets the details of one product. Price, PIX price, installments and Campo Grande shipping are computed in code; shipping to another city is handed off to the team.

Run with `python main.py --show-tools` (model `gemini-3.5-flash-lite`). Lines starting with `[tool]` show the tools the agent called.

```text
Clave: Olá! Eu sou a Clave, assistente virtual da Empório da Música. Como posso ajudar?  (digite 'sair' para encerrar)

Você: Quais violões vocês têm até R$1000?
  [tool] search_products {"category":"Violões","max_price":1000}

Clave: Temos 12 violões no total nessa faixa de preço por aqui. Olha só alguns dos modelos disponíveis:

- Tagima Memphis AC-39 Nylon Natural por R$ 429,90
- Rozini RC-104 Nylon Estudante por R$ 459,90
- Shelby SN-100 Folk Aço Preto por R$ 549,00
- Giannini GF-1R Aço Folk Sunburst por R$ 579,90
- Yamaha C40 Nylon Natural por R$ 599,90
- Giannini GN-15 Nylon Cedr Natural por R$ 689,00
- Yamaha F310 Aço Natural por R$ 699,90
- Tagima Dallas Tuner Aço Natural por R$ 749,00
- Shelby SGD-195E Elétrico Aço Sunburst por R$ 799,00
- Yamaha C70 Nylon Natural por R$ 849,00

Se quiser saber mais detalhes sobre algum desses ou ver os outros modelos, é só me falar. Precisa de mais alguma coisa?

Você: Quanto custa o Takamine GD20?
  [tool] search_products {"category":"Violões","query":"Takamine GD20"}
  [tool] get_product_details {"product_id":95}

Clave: O violão Takamine GD20 Dreadnought Natural custa R$ 2.199,00. No PIX ele sai por R$ 2.089,05, ou você pode parcelar em até 12 vezes de R$ 183,25. Ah, e a entrega para Campo Grande é gratuita.

Ele é construído com tampo em cedro sólido, fundo e laterais em sapele, braço em mogno, cordas de aço e escala de 650mm, sendo um modelo acústico sem captação.

Quer saber mais alguma coisa sobre ele ou sobre outro instrumento?

Você: E se eu morar em Dourados, quanto fica o frete?

Clave: Para entregas fora de Campo Grande, como em Dourados, o cálculo do frete e o atendimento são feitos diretamente com a nossa equipe. Você pode entrar em contato pelo WhatsApp ou telefone no número (67) 3341-4444 ou pelo e-mail contato@emporiodamusica.com.br, beleza?

Se precisar de mais alguma ajuda por aqui, é só chamar!

Você: sair

Clave: Até mais! Obrigada por falar com a Empório da Música.
```
