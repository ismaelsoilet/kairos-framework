# Protocolo de auditoria adversarial — correções de escopo

> **Aviso:** este documento era chamado "Protocolo de Auditoria Adversarial
> **Independente** (Zero-Trust) — V3". A palavra "independente" não era
> verdadeira. A auditoria foi conduzida pelo autor do projeto, na mesma máquina,
> usando um prompt escrito pelo autor para confirmar critérios definidos pelo
> autor. Isso é auto-verificação, e auto-verificação foi exatamente o mecanismo
> que produziu as alegações retratadas em [`RETRACTION.md`](../RETRACTION.md).
>
> O protocolo continua útil como **roteiro de reprodução manual**. Ele não é, e
> não pode ser apresentado como, certificação externa.

---

## O que este protocolo pode e não pode provar

**Pode:** confirmar que um ambiente reproduz os artefatos — que os servidores
sobem, que o teste de concorrência se comporta como descrito, que os endpoints
respondem. É verificação de execução, e é valiosa.

**Não pode:**

- provar que o resultado se deve ao KAIROS (o desenho dos braços era assimétrico — ver
  [`EMPIRICAL_BENCHMARK_REPORT.md`](EMPIRICAL_BENCHMARK_REPORT.md));
- substituir revisão por pares ou auditoria de terceiro;
- atestar segurança. O scanner usado na época detectava 3 de 8 padrões de fraude
  que uma sonda independente exercitou, e excluía o próprio arquivo-fonte da
  análise. Ambos foram corrigidos na v1.2, mas "corrigido" não é "certificado".

## O único critério de veredito que vale

Um item só pode ser marcado como confirmado se:

1. houver um comando exato que qualquer pessoa possa executar;
2. a saída esperada for comparada com a observada, colada no registro;
3. o comando for reproduzível em ambiente limpo, sem estado prévio;
4. o item falhar quando a implementação estiver errada — ou seja, o teste precisa
   ser capaz de falhar.

Sem o item 4, o "teste" é uma cerimônia. Foi o que aconteceu com a verificação
anterior de 6/6: nenhum dos seis critérios tinha um caso negativo.

## Roteiro de reprodução (mantido)

Estes comandos verificam o laboratório físico. Eles são úteis para qualquer pessoa
que queira ver o comportamento com os próprios olhos:

```bash
# 1. Concorrência: 50 reservas simultâneas para 10 assentos
#    Implementação sem mutex deve sobre-reservar; com mutex deve rejeitar.
curl -s -X POST http://localhost:5053/api/test-concurrency \
  -H "Content-Type: application/json" \
  -d '{"threads": 50, "balance": 500, "amount": 10}'

# 2. Tokens reais de um log de harness (não auto-declarados)
python3 scripts/kairos_cli.py token import --usage <log.jsonl>
python3 scripts/kairos_cli.py token show

# 3. Auditoria do diff com gate de mutação
python3 scripts/kairos_cli.py mutate <arquivo> --test "<comando-de-teste>"
python3 scripts/kairos_cli.py audit --base main
```

## O que mudou na v1.2

- o título perdeu "Independente";
- o veredito `[ ✅ VERIFIED ]` deixou de ser emitido sem evidência de mutação;
- `kairos audit` não exclui mais o próprio código-fonte;
- os critérios passaram a exigir um caso negativo (ver
  `tests/fixtures/fraud_corpus/` para o formato).

Se você quer uma auditoria de verdade: contrate alguém que não escreveu o código,
não lhe dê o prompt, e publique o que essa pessoa encontrar. Este documento não
substitui isso.
