# Example 2 — Promotions and product availability

**Demonstrates:** data lookups with store rules applied. The agent lists only products with an active promotion, showing the original price and the discount (manual 6.2), explains that the PIX discount is not cumulative with promotions, and reports an out-of-stock and a discontinued product instead of saying they do not exist (manual 7.3).

Run with `python main.py --show-tools` (model `gemini-3.5-flash-lite`). Lines starting with `[tool]` show the tools the agent called.

```text
Clave: Olá! Eu sou a Clave, assistente virtual da Empório da Música. Como posso ajudar?  (digite 'sair' para encerrar)

Você: Tem algum violão em promoção?
  [tool] search_products {"only_promotions":true,"category":"Violões"}

Clave: Temos sim! Encontrei 2 violões em promoção na nossa loja:

- Crafter HT-100 Folk Aço Natural: de R$ 2.399,00 por R$ 1.967,18 (18% de desconto na promoção Desconto Exclusivo)
- Taylor 110e Dreadnought Natural: de R$ 5.999,00 por R$ 5.519,08 (8% de desconto na promoção Desconto Exclusivo)

Lembrando que os descontos promocionais não são acumulativos com o desconto de PIX, beleza? Quer saber mais detalhes de algum deles?

Você: Se eu pagar o Crafter no PIX, ganho mais 5% de desconto?
  [tool] get_product_details {"product_id":90}

Clave: Não, o desconto de PIX não se aplica a produtos que já estão com preço promocional, pois as promoções não são acumulativas. O valor do Crafter HT-100 Folk Aço Natural no PIX continua sendo o preço promocional de R$ 1.967,18.

Se preferir parcelar, ele sai em até 12 vezes de R$ 163,93 sem juros! Precisa de mais alguma informação sobre ele?

Você: Vocês têm o Giannini GF-3D?
  [tool] search_products {"query":"Giannini GF-3D"}

Clave: Encontrei o Giannini GF-3D Dreadnought Sunburst, mas ele está esgotado no momento.

Quer que eu te mostre outras opções de violões disponíveis que temos por aqui?

Você: E o Shelby SN-7C 7 cordas?
  [tool] search_products {"query":"Shelby SN-7C"}

Clave: O Shelby SN-7C 7 Cordas Nylon Natural infelizmente está fora do catálogo e não teremos mais reposição.

Posso te ajudar a buscar outro modelo de violão que esteja disponível?

Você: sair

Clave: Até mais! Obrigada por falar com a Empório da Música.
```
