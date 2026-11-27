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
- **Proportionality:** trivial tasks get the change itself and no plan, and a plan's length is set by how many separate workstreams the request holds.
- **Grounded and actionable:** facts found in the code that change the request come first, defaults are checked against how the result will really be used, and phase 1 ends in concrete first steps (files, commands, edits).
- **A silent self-review:** before answering, the model runs nine quick checks on its own draft and fixes what fails.

## Install

The skill lives in `skills/freeable-planning/`, alongside its reference files.

**Claude Code (personal):**
```bash
git clone https://github.com/alexccastilho/freeable-5.2-skill.git
mkdir -p ~/.claude/skills
cp -r freeable-5.2-skill/skills/freeable-planning ~/.claude/skills/
```
**Windows (PowerShell):**
```powershell
git clone https://github.com/alexccastilho/freeable-5.2-skill.git
New-Item -ItemType Directory -Force "$HOME\.claude\skills" | Out-Null
Copy-Item -Recurse -Force freeable-5.2-skill\skills\freeable-planning "$HOME\.claude\skills\"
```
**Per project:** copy the folder to `.claude/skills/freeable-planning/` in your repository.

**Other harnesses or models:** give the model `SKILL.md` as an instruction file. It reads `references/*.md` on demand.

## Does it work? (measured, not claimed)

Full write-up: [`research/RESULTS.md`](research/RESULTS.md). All raw traces, answer keys, judge outputs and scripts are in `research/`.

**Version note.** The shipped skill is **v3.1**: v3 with a length rule that scales with the number of workstreams and the fixes listed in [`CHANGELOG.md`](CHANGELOG.md). The table below measures **v3**, frozen in `research/evaluation/round3/skill-v3/`. v3.1 has only a smoke check so far (see `research/RESULTS.md`): on a plan with several workstreams it scored 8.4 against 6.9 for v3 (bare models about 8.9), and on a one-workstream task it matched v3 but wrote about 50% more than bare Opus.

The latest round (round 3, skill v3) covered 4 new software-planning tasks: a production-readiness review of a real repository, a mobile crash regression, internationalising a Next.js shop, and speeding up a WooCommerce store. Each arm ran twice per task. Two blind judges scored every plan from 0 to 10, one Fable 5.2 and one Opus 5.5, against an answer key written before any response existed.

| Arm | Quality (0–10) | Traps caught (net) | Scope creep | Mean rank (1 = best of 8) | Words |
|---|---|---|---|---|---|
| **Opus 5.5 + skill v3** | **8.7** | **93.8%** | **0** | **2.50** | 1,454 |
| Opus 5.5 + skill v1 | 8.5 | 91.2% | 0 | 3.00 | 1,358 |
| Opus 5.5 | 7.5 | 87.2% | 3 | 5.88 | 1,344 |
| Fable 5.2 (no review tool) | 7.4 | 84.4% | 0 | 6.62 | 1,013 |

- **Every task:** v3 beat both bare Opus and bare Fable on every task (+0.2 to +1.9 points), and both judges ordered the arms the same way.
- **Cost:** v3 is about 8% longer than bare Opus.
- **How v3 was built:** Fable 5.2 merged four sources into one skill:
  - v1's richness;
  - v2's measured fixes;
  - unaided Fable's concision and moves;
  - new rules: state facts found in the code that change the request, check each default against the user's real workflow, end phase 1 in concrete first steps, run before asserting, and a silent nine-check self-review before output.
- **Earlier rounds:**
  - v1 gave consistent but smaller gains.
  - v2 traded quality for brevity.
  - Unaided Fable 5.2 did not out-plan unaided Opus 5.5 on average.
- **Caveat:** 4 tasks, 2 runs and 2 judges per task. "Ahead on 4 of 4" is the honest claim; it is not statistically significant at this sample size.

## Repository layout

```
skills/freeable-planning/   the skill (SKILL.md, references/)
CHANGELOG.md                what changed in each version, and the evidence for it
research/extraction/        tasks, Fable and Opus traces, Fable self-report, delta analysis
research/evaluation/        rounds 1–3: tasks, answer keys, runs, blind judgments, scripts, frozen skill versions
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
- **Proporcionalidade:** tarefa trivial recebe só a mudança, sem plano, e o tamanho do plano acompanha o número de frentes de trabalho do pedido.
- **Ancorado e executável:** fatos do código que mudam o pedido vêm primeiro, cada padrão é conferido no uso real e a primeira fase termina com passos concretos (arquivos, comandos, edições).
- **Autorrevisão silenciosa:** antes de responder, o modelo passa nove checagens rápidas no próprio rascunho e corrige o que falhar.

### Instalação

Copie `skills/freeable-planning/` para `~/.claude/skills/`, para uso pessoal, ou para `.claude/skills/` do seu projeto. No Windows, os comandos de PowerShell estão na seção em inglês. Em outros ambientes, entregue o `SKILL.md` ao modelo como arquivo de instruções.

### Funciona?

**Sobre a versão.** A skill publicada é a **v3.1**: a v3 com uma regra de tamanho que acompanha o número de frentes de trabalho e as correções listadas no [`CHANGELOG.md`](CHANGELOG.md). A tabela abaixo mede a **v3**, congelada em `research/evaluation/round3/skill-v3/`. Por enquanto, a v3.1 só passou por uma checagem rápida (ver `research/RESULTS.md`). Num plano com várias frentes, tirou 8,4 contra 6,9 da v3 (os modelos puros ficaram perto de 8,9). Numa tarefa de uma frente só, empatou com a v3, mas escreveu cerca de 50% a mais que o Opus puro.

Na rodada mais recente (rodada 3, skill v3), 4 tarefas novas de planejamento de software foram avaliadas às cegas por dois juízes, um Fable 5.2 e um Opus 5.5, com notas de 0 a 10:

| Braço | Nota (0–10) | Armadilhas pegas | Ampliou escopo | Posição média (1 = melhor de 8) | Palavras |
|---|---|---|---|---|---|
| **Opus 5.5 + skill v3** | **8,7** | **93,8%** | **0** | **2,50** | 1.454 |
| Opus 5.5 + skill v1 | 8,5 | 91,2% | 0 | 3,00 | 1.358 |
| Opus 5.5 puro | 7,5 | 87,2% | 3 | 5,88 | 1.344 |
| Fable 5.2 puro | 7,4 | 84,4% | 0 | 6,62 | 1.013 |

- **Todas as tarefas:** a v3 superou o Opus puro e o Fable puro em todas as 4 tarefas (+0,2 a +1,9 ponto), e os dois juízes concordaram na ordem.
- **Custo:** a v3 escreve cerca de 8% a mais que o Opus puro.
- **Rodadas anteriores:** a v1 deu ganhos consistentes, porém menores; a v2 trocou qualidade por concisão; e o Fable 5.2 sem ajuda não planejou melhor que o Opus 5.5 sem ajuda, na média.
- **Como a v3 foi feita:** juntando quatro fontes:
  - a riqueza da v1;
  - as correções medidas da v2;
  - a concisão do Fable;
  - regras novas: citar fatos do código que mudam o pedido, conferir cada padrão no fluxo real do usuário, terminar a primeira fase com passos concretos, verificar antes de afirmar e fazer uma autorrevisão silenciosa antes de entregar.
- **Ressalva:** são 4 tarefas, então leia "à frente em 4 de 4" como tendência forte, não como prova estatística. O relatório completo está em [`research/RESULTS.md`](research/RESULTS.md).
