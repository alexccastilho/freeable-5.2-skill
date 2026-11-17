# Freeable 5.2 Skill

A planning skill that gives other models, primarily **Claude Opus 5.5**, the planning pattern observed in **Claude Fable 5.2**. Fable 5.2 extracted the pattern, wrote the skill, and the skill was then measured in blind A/B tests.

> **Unofficial.** This project is not affiliated with or endorsed by Anthropic. It is a behavioural approximation built from observed outputs, not from any access to model internals.

[Português abaixo](#português)

## What it does

When you plan a feature, migration, refactor, incident fix, vague request or non-software project, the skill changes the *shape* of the plan:

- **The opener says where the work really is**, which is not always where the request points ("8M rows is small; the cross-table joins are most of the effort").
- **It picks the default path when nobody answers.** That is the cheaper, reversible route when the requested one is costly or irreversible, so the plan never blocks waiting for answers.
- **At most five questions, ranked.** The driver comes first, then tolerance; each question carries a default and the branch that changes if the answer differs.
- **The smallest change with full failure coverage.** Scope is limited, risk coverage is not.
- **Gates with numbers:** a go/no-go list before an irreversible step, an abort rule inside it, a revert rule after it.
- **Flags that sit beside what they qualify:** recalled specifics, unrun code, and relative dates turned into concrete ones.
- **Proportionality:** trivial tasks get the change itself and no plan, and plans stay under a length ceiling.

## Install

The skill lives in `skills/freeable-planning/`, alongside its reference files.

**Claude Code (personal):**
```bash
git clone https://github.com/alexccastilho/freeable-5.2-skill.git
mkdir -p ~/.claude/skills
cp -r freeable-5.2-skill/skills/freeable-planning ~/.claude/skills/
```
**Per project:** copy the folder to `.claude/skills/freeable-planning/` in your repository.

**Other harnesses or models:** give the model `SKILL.md` as an instruction file. It reads `references/*.md` on demand.

## Does it work? (measured, not claimed)

Full write-up: [`research/RESULTS.md`](research/RESULTS.md). All raw traces, answer keys, judge outputs and scripts are in `research/`.

The final held-out round covered 3 new tasks, 2 runs per arm, and two blind judges (Fable 5.2 and Opus 5.5):

| Arm | Traps caught (net) | Scope creep | Quality (1–5) | Mean rank (1 = best of 8) | Words | Skill move-set presence* |
|---|---|---|---|---|---|---|
| Opus 5.5 | **90.0%** | 4 | 4.22 | 3.67 | 1,300 | 0.44 |
| Opus 5.5 + skill v1 | 88.8% | **0** | **4.50** | **3.42** | 1,594 | **0.93** |
| Opus 5.5 + skill v2 (shipped) | 87.5% | **0** | 4.38 | 4.17 | **1,188** | 0.84 |
| Fable 5.2 (no review tool) | 85.0% | 3 | 3.77 | 6.75 | 963 | 0.40 |

\*Presence of the skill's own moves D1–D11, scored by one Opus judge.

- **What improves:** clarifying questions (3.92 → 4.83 with v2), risk and verification (3.75 → 4.42), proportionality (3.83 → 4.42), and scope creep (none).
- **What gets worse:** grounding in the existing code (4.75 → 4.08) and actionability (4.83 → 4.17). The trap-catch rate does not improve, and overall rank is mixed: one judge ranks bare Opus above both skill versions.
- **v1 or v2:** v1 scored best on quality and rank in the final round but writes 23% more than bare Opus. v2 is shorter than bare Opus. See [`research/RESULTS.md`](research/RESULTS.md) for why v2 ships.
- **Surprising finding:** unaided Fable 5.2 did not out-plan unaided Opus 5.5 on average on the held-out tasks; it was ahead on 3 of 9. The distinctive pattern appears most strongly when Fable plans *with a review step*, and the skill encodes something closer to that.
- **Caveat:** samples are small, so read the numbers as directional.

## Repository layout

```
skills/freeable-planning/   the skill (SKILL.md, references/, CHANGELOG.md)
research/extraction/        tasks, Fable and Opus traces, Fable self-report, delta analysis
research/evaluation/        round 1 and round 2: tasks, answer keys, runs, blind judgments, scripts
research/fixtures/shopmini/ the small repository used by brownfield tasks
research/RESULTS.md         the full results
```

## License

MIT.

---

## Português

Uma skill de planejamento que leva a outros modelos, principalmente o **Claude Opus 5.5**, o padrão de planejamento observado no **Claude Fable 5.2**. O próprio Fable 5.2 extraiu o padrão e escreveu a skill. Depois ela foi medida em testes A/B às cegas.

> **Não oficial.** Projeto sem vínculo com a Anthropic. É uma aproximação comportamental construída a partir de saídas observadas, sem acesso a mecanismos internos do modelo.

### O que ela faz

Ao planejar uma funcionalidade, migração, refatoração, correção de incidente, pedido vago ou projeto fora de software, a skill muda a *forma* do plano:

- **A abertura diz onde está o trabalho de verdade**, que nem sempre é onde o pedido aponta.
- **Escolhe o caminho padrão para quando ninguém responder.** É o caminho mais barato e reversível quando o pedido é caro ou irreversível, e assim o plano nunca trava esperando resposta.
- **No máximo cinco perguntas, priorizadas.** O motivo do pedido vem primeiro, depois a tolerância. Cada pergunta traz um padrão e o que muda se a resposta for outra.
- **A menor mudança, com cobertura total de falhas.** O escopo é limitado; a cobertura de risco, não.
- **Condições de parada com números:** seguir ou não antes de um passo irreversível, abortar durante e reverter depois.
- **Avisos ao lado do que qualificam:** detalhes lembrados de memória, código não executado e datas relativas convertidas em datas concretas.
- **Proporcionalidade:** tarefa trivial recebe só a mudança, sem plano, e planos ficam abaixo de um limite de tamanho.

### Instalação

Copie `skills/freeable-planning/` para `~/.claude/skills/`, para uso pessoal, ou para `.claude/skills/` do seu projeto. Em outros ambientes, entregue o `SKILL.md` ao modelo como arquivo de instruções.

### Funciona?

Os números estão na tabela acima e o relatório completo em [`research/RESULTS.md`](research/RESULTS.md).

- **O que melhora:** com a skill, o Opus faz perguntas melhores, cuida mais de risco e verificação, fica mais proporcional e não amplia o escopo.
- **O que piora:** o plano fica um pouco menos ancorado no código existente e menos direto ao ponto de execução. Ele também não pega mais armadilhas do que o Opus puro, e a posição geral ficou mista entre os juízes.
- **Achado mais curioso:** sem ferramenta de revisão, o Fable 5.2 não planejou melhor que o Opus 5.5 na média; ficou à frente em 3 de 9 tarefas. O padrão característico aparece com mais força quando o Fable planeja *com uma etapa de revisão*, e a skill ensina algo mais próximo disso.
- **Ressalva:** as amostras são pequenas, então leia os números como tendência, não como prova.
