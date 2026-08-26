# Compilation Pipeline Specification

This document is the canonical specification for the compiled-prose pipeline implemented in this repository. It defines the stage graph, authority model, output/failure protocol, peer-review gate, build lifecycle, and reproducibility boundary.

The implementation is intentionally small: GNU Make orchestrates file dependencies, `tools/render_prompt.py` creates one flattened prompt per model-backed stage, `tools/llm_run.sh` selects the backend, `tools/enforce_protocol.py` enforces the common result protocol, and `tools/review_decision.py` enforces the peer-review decision gate. Provider-specific capabilities remain in backend adapters; the OpenAI Responses adapter exposes web search only to academic-journal peer review.

Model-backed stage count is part of the user-visible cost surface. The core pipeline therefore follows a simple rule: **a second writing pass happens only when new information exists that justifies it**. The first model call performs the complete target realisation. Peer review supplies an independent judgement. A final writing call occurs only when review reports a `REALISATION` defect.

This design is motivated by regression evidence, not by a universal claim about every model or source. In the `grantaj/censorship` GPT-5.6 Sol case that prompted the simplification, the former draft-to-smooth pass left about 99.42% of words unchanged and smooth-to-revise left about 99.86% unchanged, at roughly $0.73 combined cost, without repairing the main outline-prosification problem. Peer review was materially more informative. That evidence justifies removing the blind polishing passes while retaining review as an independent stage.

## Normative vocabulary and enforcement boundary

### Mechanically enforced rules

Mechanical enforcement currently covers:

- stage ordering through Make dependencies;
- stable prompt composition inputs;
- declared `tex` versus `md` result routing;
- the `@@FAIL` sentinel protocol;
- atomic publication of successful artefacts and external diagnostics;
- removal of stale nominal outputs on failed rebuilds;
- peer-review status syntax and status/finding consistency;
- deterministic `PASS` promotion from `realise.tex` to `final.tex`;
- exactly one conditional final-revision route;
- build-directory isolation.

The repository example adds release-specific checks around its audited source catalogue and bibliography keys. These verify provenance and rendering integrity for emitted material; they do not implement semantic target selection or prose quality in deterministic code.

### Prompt contracts

Prompt contracts govern properties not mechanically proved by the build system: source fidelity, absence of invented conceptual content, preservation of conceptual topology and epistemic stance, target-relative coverage, rhetorical architecture, writing quality, evidence/attribution/citation presentation, and semantic classification of review findings as `SOURCE` or `REALISATION`.

A structurally valid LaTeX result can still violate these contracts. Mechanical code therefore does not try to force section counts, list usage, source-item mappings, or other surface proxies for prose quality.

### Design constraints

The principal design constraints are backend independence, explicit failure over improvisation, file-driven operation, keeping conceptual authority upstream of generated prose, model-stage economy, and keeping semantic target decisions in the prompt/model layer.

Model-stage economy means a conceptual responsibility should be absorbed into an existing model-backed stage when that stage can perform it reliably. Adding a model call requires empirical justification because it changes the user's cost and latency. Blind smoothing or revision is not justified merely by conceptual neatness.

## Scope and stage graph

The core compilation path is:

```text
authoritative source
      |
      v
   realise
      |
      v
 peer review
      |
      v
review decision
   /       |        \
 PASS   REVISE_      BLOCKED_SOURCE
  |      REALISATION      |
  |          |             `--> diagnostic + failure
  |          v
  |    final revision
  |          |
  +----------+
       |
       v
    final.tex
```

Optional bibliography metadata may accompany the source. It supplies stable identifiers and publication metadata for citations already authored in the source; it is not conceptual input and does not itself require visible formal citation apparatus.

`make summarize` is an independent source-to-LaTeX transform. It is not part of the `final` dependency chain.

## Authority model

### Authoritative conceptual source

The file supplied as `IN=...` is the sole source of conceptual authorship. It defines claims, argument, conceptual scope, distinctions, authored examples, evidence, citations, attributions, unresolved choices, epistemic stance, and conceptual topology: dependencies, qualification scope, taxonomy membership, semantically meaningful ordering, hierarchy of importance, and support relationships.

Changing a generated artefact never changes the source retroactively.

### Stage prompts

`prompts/*.md` define transformations. They constrain realisation, review, and failure behaviour but may not author new conceptual content.

### Target requirements

`prompts/targets/*.md` define audience/venue-specific realisation: register, reading level, coverage and compression, formatting, rhetorical form, explanatory explicitness, evidence/attribution/citation presentation, rigour, and whether illustrative scaffolding is permitted.

Coverage is exhaustive by default. A target may explicitly authorise summarisation, compression, or selective omission, but omission must not make retained content false or misleading or detach necessary qualifications, dependencies, uncertainty, attribution, or support.

Conceptual topology and presentation topology are deliberately separate. Logical dependencies, qualification scope, taxonomy membership, genuine procedures or sequences, hierarchy of importance, scope, and evidence/attribution/citation attachment are authoritative. Bullets, numbering, heading depth, adjacency, fragment boundaries, and navigation order are presentation topology unless they encode one of those substantive relationships. Realisation may synthesize, consolidate, split, rhetorically group, and reorder material without a special target permission when only presentation topology changes. Semantically meaningful ordering must survive.

Rhetorical reorganisation cannot invent connective reasoning, categories, dependencies, causes, equivalences, contrasts, or warrants. Qualifications and support remain attached to the content they govern.

Evidence, attribution, and citation **presentation** is target-owned; evidentiary authority remains source-owned. A target may require formal scholarly citations, ordinary narrative attribution, or no visible formal citation apparatus. It may never invent a source, citation, attribution, or evidentiary relationship.

A target may explicitly permit illustrative scaffolding. Generated analogies, hypotheticals, comparisons, concrete restatements, or similar devices must only illuminate source-authorised concepts. They may not become evidence, a missing warrant, scope, interpretation, or conceptual authority and must be removable without changing the work's claims.

### Bibliographic rendering metadata

When `BIBLIOGRAPHY=...` is supplied, `tools/render_prompt.py` includes²È="25Ñ…Ñ¥½¸µÁÉ•Í•¹Ñ…Ñ¥½¸ÉÕ±•ÌÉ•µ…¥¸¡…É‰½Õ¹‘…É¥•Ì¸M½ÕÉ”¥¹ÍÕ™™¥¥•¹äÑ¡…ÐÝ½Õ±É•ÅÕ¥É”½¹•ÁÑÕ…°¥¹Ù•¹Ñ¥½¸ÕÍ•Ì%1€¸((ŒŒŒ€È¸A••ÈÉ•Ù¥•Ü((¨©5…­”Ñ…É•Ðè¨¨É•Ù¥•Ý€€€(¨©MÑ…”ÁÉ½µÁÐè¨¨ÁÉ½µÁÑÌ¼ÐÁ}Á••É}É•Ù¥•Ü¹µ‘€€€(¨©%¹ÁÕÑÌè¨¨…ÕÑ¡½É¥Ñ…Ñ¥Ù”Í½ÕÉ”Á±ÕÌÉ•…±¥Í”¹Ñ•á€°Ñ…É•ÐÉ•ÅÕ¥É•µ•¹ÑÌ°…¹½ÁÑ¥½¹…°‰¥‰±¥½É…Á¡äµ•Ñ…‘…Ñ„€€(¨©=ÕÑÁÕÐè¨¨€¡	U%1}%H¤½Á••É}É•Ù¥•Ü¹µ‘€()A••ÈÉ•Ù¥•Ü¥Ì½¹•ÁÑÕ…±±ä¥¹‘•Á•¹‘•¹Ð™É½´É•…±¥Í…Ñ¥½¸¸%Ð™¥ÉÍÐ©Õ‘•ÌÑ¡”É•…±¥Í•…ÉÑ•™…Ð…ÌÑ¡½Õ ¥ÐÝ•É”ÍÕ‰µ¥ÑÑ•‘¥É•Ñ±ä…Ì™¥¹¥Í¡•ÝÉ¥Ñ¥¹œ™½ÈÑ¡”Í•±•Ñ•Ñ…É•Ð¸¥‘•±¥Ñä°ÑÉ…•…‰¥±¥Ñä°…¹Ù¥Í¥‰±”ÁÉ•Í•ÉÙ…Ñ¥½¸½˜Í½ÕÉ”ÍÑÉÕÑÕÉ”…É”¹½ÐÁ½Í¥Ñ¥Ù”•Ù¥‘•¹”½˜ÝÉ¥Ñ¥¹œÅÕ…±¥Ñä¸Q¡”É•Ù¥•Ý•ÈÑ¡•¸½µÁ…É•Ì¥‘•¹Ñ¥™¥•‘•™•ÑÌÝ¥Ñ Ñ¡”Í½ÕÉ”Ñ¼±…ÍÍ¥™äÑ¡•´…ÌM=UI€½ÈI1%MQ%=9€°…¹™¥¹…±±ä¡•­Ì½µÁ¥±…Ñ¥½¸¥¹Ñ•É¥Ñä™½È‘É¥™Ð…¹Í½ÕÉ”µ…ÍÍÕÉ…¹”™…¥±ÕÉ•Ì¸()½È©½ÕÉ¹…±}……‘•µ¥€°Ñ…É•ÐÅÕ…±¥Ñä¥¹±Õ‘•Ì¹½Ù•±Ñä°Í¥¹¥™¥…¹”°…¹Í¡½±…É±äÁ½Í¥Ñ¥½¹¥¹œ¸Q¡”É•Ù¥•Ý•ÈÁ•É™½ÉµÌ„ÁÉ½Á½ÉÑ¥½¹…°…‘Ù•ÉÍ…É¥…°Í•…É ™½ÈÁÉ¥½È™½ÉµÕ±…Ñ¥½¹Ì°•ÍÑ…‰±¥Í¡•Ñ•Éµ¥¹½±½ä½Ñ¡•½É¥•Ì°…‘©…•¹ÐÝ½É¬Ñ¡…Ð¹…ÉÉ½ÝÌÑ¡”½¹ÑÉ¥‰ÕÑ¥½¸°µ…Ñ•É¥…±±ä‘¥™™•É•¹Ð•áÁ±…¹…Ñ¥½¹Ì°…¹™½Õ¹‘…Ñ¥½¹…°½µ¥ÍÍ¥½¹Ì¸™…¥±•Í•…É ¹•Ù•ÈÙ•É¥™¥•Ì¹½Ù•±Ñä¸¹äµ…Ñ•É¥…°•áÑ•É¹…±±ä‘¥Í½Ù•É•™¥¹‘¥¹œ¥ÌM=UI€‰•…ÕÍ”Ñ¡”…ÕÑ¡½ÈµÕÍÐ‘•¥‘”Ý¡•Ñ¡•È…¹¡½ÜÑ¼¡…¹”Ñ¡”Í½ÕÉ”¸((¨©=Á•¹$ÑÉ…¹ÍÁ½ÉÐ½¹™¥ÕÉ…Ñ¥½¸è¨¨Ý¡•¸Ñ¡”ÍÑ…”¥Ì•á…Ñ±äÁÉ½µÁÑÌ¼ÐÁ}Á••É}É•Ù¥•Ü¹µ‘€…¹Ñ…É•Ð•á…Ñ±äÁÉ½µÁÑÌ½Ñ…É•ÑÌ½©½ÕÉ¹…±}……‘•µ¥Œ¹µ‘€°Ñ½½±Ì½½Á•¹…¥}É•ÍÁ½¹Í•Ì¹Áå€ÍÕÁÁ±¥•Ì¡½ÍÑ•Ý•‰}Í•…É¡€Ý¥Ñ É•ÅÕ¥É•Ñ½½°ÕÍ”¸9¼ÁÉ½Í”µÁÉ½‘Õ¥¹œÍÑ…”½È½Ñ¡•È‰Õ¥±Ðµ¥¸Ñ…É•ÐÉ••¥Ù•ÌÑ¡…Ð…Á…‰¥±¥Ñä¸((ŒŒŒ€Ì¸I•Ù¥•Ü‘•¥Í¥½¸…Ñ”((¨©%µÁ±•µ•¹Ñ…Ñ¥½¸è¨¨Ñ½½±Ì½É•Ù¥•Ý}‘•¥Í¥½¸¹Áå€€€(¨©%¹ÁÕÑÌè¨¨Á••É}É•Ù¥•Ü¹µ‘€°É•…±¥Í”¹Ñ•á€€€(¨©I•ÍÕ±Ðè¨¨‘•Ñ•Éµ¥¹¥ÍÑ¥ŒÁÉ½µ½Ñ¥½¸°Á•Éµ¥ÍÍ¥½¸™½È½¹”™¥¹…°É•Ù¥Í¥½¸°½È™…¥±ÕÉ”()Q¡”™¥ÉÍÐ¹½¸µ•µÁÑä±¥¹”µÕÍÐ‰”•á…Ñ±ä½¹”½˜è()Ñ•áÐ)MQQULèAML)MQQULèIY%M}I1%MQ%=8)MQQULè	1=-}M=UI)€()Ù•Éä±…Ñ•È¹½¸µ•µÁÑä±¥¹”µÕÍÐ‰”è()Ñ•áÐ(´m5)=Iñ5%9=IumM=UIñI1%MQ%=9t€ñ±½…Ñ¥½¸ø€èè€ñ™¥¹‘¥¹œø)€()MÑ…ÑÕÌ¥Ìµ•¡…¹¥…±±ä½¹Í¥ÍÑ•¹ÐÝ¥Ñ ™¥¹‘¥¹Ìè((´…¹äM=UI€™¥¹‘¥¹œ€´ø	1=-}M=UI€ì(´½Ñ¡•ÉÝ¥Í”½¹”½Èµ½É”I1%MQ%=9€™¥¹‘¥¹Ì€´øIY%M}I1%MQ%=9€ì(´¹¼™¥¹‘¥¹Ì€´øAMM€¸()•¥Í¥½¸‰•¡…Ù¥½ÕÈè((´AMM€…Ñ½µ¥…±±ä½Á¥•ÌÉ•…±¥Í”¹Ñ•á€Ñ¼™¥¹…°¹Ñ•á€Ý¥Ñ €¨©¹¼µ½‘•°…±°¨¨ì(´IY%M}I1%MQ%=9€±•…Ù•Ì™¥¹…°¹Ñ•á€…‰Í•¹Ð…¹Á•Éµ¥ÑÌ•á…Ñ±ä½¹”½¹‘¥Ñ¥½¹…°™¥¹…°µÉ•Ù¥Í¥½¸…±°ì(´	1=-}M=UI€É•µ½Ù•Ì…¹äÍÑ…±”™¥¹…°½ÕÑÁÕÐ°ÝÉ¥Ñ•Ì€¡	U%1}%H¤½•ÉÉ½ÉÌ½É•Ù¥•Ü¹µ‘€°…¹•á¥ÑÌ¹½¸µé•É¼ì(´µ…±™½Éµ•½¥¹½¹Í¥ÍÑ•¹ÐÉ•Ù¥•Ü±¥­•Ý¥Í”™…¥±Ì±½Í•Ý¥Ñ …¸•áÑ•É¹…°‘¥…¹½ÍÑ¥Œ¸()I•Ù¥•ÜÑ•áÐÉ•µ…¥¹Ì‘¥…¹½ÍÑ¥Œ¸%Ð…¹¹½Ð¥¹ÑÉ½‘Õ”Í½ÕÉ”…ÕÑ¡½É¥ÑäÑ¡É½Õ Ñ¡¥Ì…Ñ”¸((ŒŒŒ€Ð¸½¹‘¥Ñ¥½¹…°™¥¹…°É•Ù¥Í¥½¸((¨©5…­”Ñ…É•Ðè¨¨É•…¡•½¹±äÑ¡É½Õ ™¥¹…±€€€(¨©MÑ…”ÁÉ½µÁÐè¨¨ÁÉ½µÁÑÌ¼ÔÁ}™¥¹…°¹µ‘€€€(¨©AÉ•½¹‘¥Ñ¥½¸è¨¨Ù…±¥‘…Ñ•IY%M}I1%MQ%=9€É•Ù¥•Ü€€(¨©%¹ÁÕÑÌè¨¨…ÕÑ¡½É¥Ñ…Ñ¥Ù”Í½ÕÉ”°É•…±¥Í”¹Ñ•á€°Í•±•Ñ•Ñ…É•Ð°Ù…±¥‘…Ñ•Á••ÈµÉ•Ù¥•Ü™¥¹‘¥¹Ì°…¹½ÁÑ¥½¹…°‰¥‰±¥½É…Á¡äµ•Ñ…‘…Ñ„€€(¨©=ÕÑÁÕÐè¨¨€¡	U%1}%H¤½™¥¹…°¹Ñ•á€()Q¡¥Ì¥Ì½¹”‰½Õ¹‘•ÝÉ¥Ñ¥¹œÁ…ÍÌ©ÕÍÑ¥™¥•‰äÑ¡”¹•Ü¥¹™½Éµ…Ñ¥½¸ÍÕÁÁ±¥•‰äÁ••ÈÉ•Ù¥•Ü¸%ÐµÕÍÐ…‘‘É•ÍÌÙ…±¥‘…Ñ•É•…±¥Í…Ñ¥½¸™¥¹‘¥¹ÌÕÍ¥¹œ½¹±ä½ÉÉ•Ñ¥½¹Ì™Õ±±ä‘•Ñ•Éµ¥¹•‰äÍ½ÕÉ”…¹Ñ…É•Ð¸I•Ù¥•Ü½µµ•¹ÑÌ…É”‘¥…¹½ÍÑ¥Œ½¹Ñ•áÐ°¹½Ð…ÕÑ¡½É¥Ñä¸%˜„É•ÅÕ•ÍÑ•É•Á…¥È…ÑÕ…±±äÉ•ÅÕ¥É•Ì„¹•ÜÝ…ÉÉ…¹Ð°±…¥´°•Ù¥‘•¹”¥Ñ•´°Í½ÕÉ”°¥Ñ…Ñ¥½¸°½¹•ÁÑÕ…°É•±…Ñ¥½¹Í¡¥À°Í½Á”¡½¥”°¥¹Ñ•ÉÁÉ•Ñ…Ñ¥½¸°½È½Ñ¡•È…ÕÑ¡½É¥…°‘•¥Í¥½¸°Ñ¡”ÍÑ…”™…¥±ÌÉ…Ñ¡•ÈÑ¡…¸¥µÁÉ½Ù¥Í¥¹œ¸()Q¡•É”¥Ì¹¼…ÕÑ½µ…Ñ¥ŒÉ½ÕÑ”‰…¬Ñ¼Á••ÈÉ•Ù¥•Ü…¹¹¼É•ÕÉÍ¥Ù”É•Ù¥Í¥½¸±½½À¸((ŒŒÕá¥±¥…ÉäÍÕµµ…É¥é”ÑÉ…¹Í™½É´((¨©5…­”Ñ…É•Ðè¨¨ÍÕµµ…É¥é•€€€(¨©MÑ…”ÁÉ½µÁÐè¨¨ÁÉ½µÁÑÌ¼ÀÕ}ÍÕµµ…É¥é”¹µ‘€€€(¨©%¹ÁÕÐè¨¨…ÕÑ¡½É¥Ñ…Ñ¥Ù”Í½ÕÉ”…¹½ÁÑ¥½¹…°‰¥‰±¥½É…Á¡äµ•Ñ…‘…Ñ„€€(¨©=ÕÑÁÕÐè¨¨€¡	U%1}%H¤½ÍÕµµ…Éä¹Ñ•á€()Q¡¥ÌÑÉ…¹Í™½É´¥Ì¥¹‘•Á•¹‘•¹Ð½˜Ñ¡”ÁÕ‰±¥…Ñ¥½¸É…Á …¹µ…ä‘•™¥¹”¥¹ÑÉ¥¹Í¥Œ½Ù•É…”É•‘ÕÑ¥½¸¸((ŒŒ	Õ¥±‘¥É•Ñ½Éä…¹™¥±”±¥™•å±”()	U%1}%H€üô‰Õ¥±‘€¥ÌÑ¡”•¹•É…Ñ•µ½ÕÑÁÕÐÉ½½Ð…¹µ…ä‰”½Ù•ÉÉ¥‘‘•¸è()‰…Í )µ…­”	U%1}%Hô½ÑµÀ½½µÁ¥±•µÁÉ½Í”™¥¹…°%8õ½ÕÑ±¥¹”¹µ)€()-¹½Ý¸½É”½ÕÑÁÕÑÌ…É”É•…±¥Í”¹Ñ•á€°Á••É}É•Ù¥•Ü¹µ‘€°™¥¹…°¹Ñ•á€°½ÁÑ¥½¹…°™¥¹…°¹Á‘™€°…¹•áÑ•É¹…°‘¥…¹½ÍÑ¥Ì¸Q¡”Í•±˜µ•á…µÁ±”…±Í¼½Á¥•Ì¥ÑÌ…Õ‘¥Ñ•‰¥‰±¥½É…Á¡ä¥¹Ñ¼Ñ¡”‰Õ¥±É½½Ð¸µ…­”±•…¹€É•µ½Ù•Ì­¹½Ý¸•¹•É…Ñ•½ÕÑÁÕÑÌìµ…­”±½‰‰•É€É•µ½Ù•ÌÑ¡”Í•±•Ñ•‰Õ¥±É½½Ð•¹Ñ¥É•±ä¸()ÍÕ•ÍÍ™Õ°É•Ñ…¥¹•Í•±˜µ•á…µÁ±”…¹‘¥‘…Ñ”É•ÅÕ¥É•ÌÉ•…±¥Í”¹Ñ•á€°Á••É}É•Ù¥•Ü¹µ‘€°™¥¹…°¹Ñ•á€°…¹™¥¹…°¹Á‘™€Á±ÕÌÍ½ÕÉ”½ÁÉ½Ù•¹…¹”™¥±•Ì¸Q¡”ÁÕ‰±¥…Ñ¥½¸½Í¡½Ý…Í”…ÍÍ•µ‰±•È½¹ÍÕµ•Ì™¥¹…°½ÕÑÁÕÐ°É•Ù¥•Ü°Í½ÕÉ”°…¹ÁÉ½Ù•¹…¹”…¹‘½•Ì¹½ÐÉ•ÅÕ¥É”É•µ½Ù•ÁÉ”µÉ•Ù¥•Ü¥¹Ñ•Éµ•‘¥…Ñ”…ÉÑ•™…ÑÌ¸((ŒŒ	±½­¥¹œÍ•µ…¹Ñ¥Ì()AÉ½µÁÐµ½¹ÑÉ…Ð‰±½­¥¹œ½¹‘¥Ñ¥½¹Ì¥¹±Õ‘”…¹ä¹••Ñ¼¥¹Ù•¹Ð„±…¥´°Ý…ÉÉ…¹Ð°½¹Ñ•¹Ðµ‰•…É¥¹œ•á…µÁ±”°•Ù¥‘•¹”°Í½ÕÉ”°…ÑÑÉ¥‰ÕÑ¥½¸°¥Ñ…Ñ¥½¸°½¹•ÁÑÕ…°É•±…Ñ¥½¹Í¡¥À°½¹¹•Ñ¥Ù”¥¹™•É•¹”°Í½Á”‘•¥Í¥½¸°½È¥¹Ñ•ÉÁÉ•Ñ…Ñ¥½¸ì¡½½Í”‰•ÑÝ••¸Õ¹É•Í½±Ù•¥¹Ñ•ÉÁÉ•Ñ…Ñ¥½¹Ìì¡…¹”±…¥´ÍÑÉ•¹Ñ ½Èµ•…¹¥¹™Õ°½É‘•ÈìÍ…Ñ¥Í™äÑ…É•ÐµÉ•ÅÕ¥É•ÍÕÁÁ½ÉÐ…‰Í•¹Ð™É½´Ñ¡”Í½ÕÉ”ì½ÈÉ•Á…¥È‘É¥™ÐÝ¡•¸Í½ÕÉ”…¹Ñ…É•Ð‘¼¹½Ð‘•Ñ•Éµ¥¹”Ñ¡”½ÉÉ•Ñ¥½¸¸()5•¡…¹¥…°‰±½­¥¹œ½¹‘¥Ñ¥½¹Ì¥¹±Õ‘”‰…­•¹½ÁÉ½µÁÐµÉ•¹‘•È™…¥±ÕÉ”°•µÁÑä½ÕÑÁÕÐ°µ…±™½Éµ•Í•¹Ñ¥¹•°ÕÍ”°½ÕÑÁÕÐµÁÉ½Ñ½½°Ù¥½±…Ñ¥½¸°µ…±™½Éµ•½¥¹½¹Í¥ÍÑ•¹ÐÉ•Ù¥•ÜÉ…µµ…È°Ù…±¥‘…Ñ•	1=-}M=UI€°½È%1€™É½´½¹‘¥Ñ¥½¹…°™¥¹…°É•Ù¥Í¥½¸¸()…¥±ÕÉ•Ì…É”•áÑ•É¹…±¥Í•É…Ñ¡•ÈÑ¡…¸•µ‰•‘‘•¥¸•¹•É…Ñ•1…Q•`¸((ŒŒ%Ñ•É…Ñ¥½¸…¹É•ÑÉäÁ½±¥ä()Q¡”¥µÁ±•µ•¹Ñ•½É”¥Ì„Í¥¹±”™½ÉÝ…ÉÁ…Ñ è()Ñ•áÐ)É•…±¥Í”€´øÁ••ÈÉ•Ù¥•Ü€´ø‘•¥Í¥½¸€´ø½ÁÑ¥½¹…°™¥¹…°É•Ù¥Í¥½¸)€()Q¡•É”¥Ì¹¼É•Ù¥•Üµ……¥¸•‘”°É•ÕÉÍ¥Ù”5…­”É•ÑÉä°…ÕÑ½µ…Ñ¥ŒÍ½ÕÉ”É•Á…¥È°‰±¥¹Íµ½½Ñ¡¥¹œÍÑ…”°½ÈÁÉ”µÉ•Ù¥•ÜÉ•Ù¥Í¥½¸ÍÑ…”¸()‘‘¥¹œ…¹½Ñ¡•Èµ½‘•°µ‰…­•ÍÑ…”¥Ì¹½Ð…¸½É‘¥¹…ÉäÉ•™…Ñ½È¸%Ð¡…¹•ÌÕÍ•È½ÍÐ…¹É•ÅÕ¥É•Ì•µÁ¥É¥…°•Ù¥‘•¹”Ñ¡…ÐÑ¡”É•ÍÁ½¹Í¥‰¥±¥Ñä…¹¹½Ð‰”¡…¹‘±•É•±¥…‰±äÝ¥Ñ¡¥¸Ñ¡”•á¥ÍÑ¥¹œ‰½Õ¹‘•ÍÑ…•Ì¸((ŒŒ	…­•¹¥¹‘•Á•¹‘•¹”()	…­•¹Í•±•Ñ¥½¸½ÕÉÌ¥¸Ñ½½±Ì½±±µ}ÉÕ¸¹Í¡€¸	½Ñ ÍÕÁÁ½ÉÑ•‰…­•¹‘Ì½¹ÍÕµ”É•¹‘•É•ÁÉ½µÁÑÌ½¸ÍÑ…¹‘…É¥¹ÁÕÐ…¹•áÁ½Í”µ½‘•°É•ÍÕ±ÑÌÑ¼Ñ¡”Í…µ”•¹™½É•µ•¹Ð±…å•È¸AÉ½Ù¥‘•È…‘…ÁÑ•ÉÌµ…ä¡…¹‘±”ÑÉ…¹ÍÁ½ÉÐµÍÁ•¥™¥Œ…Á…‰¥±¥Ñ¥•Ì°‰ÕÐ…ÕÑ¡½É¥ÑäÍ•µ…¹Ñ¥Ì°ÁÉ½µÁÑÌ°É•ÍÕ±ÐÉ½ÕÑ¥¹œ°‘¥…¹½ÍÑ¥Ì°…¹É•Ù¥•ÜÁ½±¥äÉ•µ…¥¸‰…­•¹µ¥¹‘•Á•¹‘•¹Ð¸()Q¡”……‘•µ¥ŒµÉ•Ù¥•ÜÝ•ˆµÍ•…É É…¹Ð¥Ì„¹…ÉÉ½ÜÁÉ½Ù¥‘•È…Á…‰¥±¥Ñä°¹½Ð…¸…ÕÑ¡½É¥Ñä¡…¹¹•°¸((ŒŒI•ÁÉ½‘Õ¥‰¥±¥Ñä‰½Õ¹‘…Éä()Q¡”ÁÉ½©•ÐÑ…É•ÑÌÍ•µ…¹Ñ¥Œ…¹ÍÁ•¥™¥…Ñ¥½¸µ±•Ù•°É•ÁÉ½‘Õ¥‰¥±¥Ñä°¹½Ð‰åÑ”µ±•Ù•°‘•Ñ•Éµ¥¹¥ÍÑ¥ŒÁÉ½Í”¸M½ÕÉ”°ÁÉ½µÁÑÌ°Ñ…É•ÐÉ•ÅÕ¥É•µ•¹ÑÌ°½ÁÑ¥½¹…°‰¥‰±¥½É…Á¡äµ•Ñ…‘…Ñ„°5…­”‘•Á•¹‘•¹¥•Ì°‰…­•¹½µ½‘•°½¹™¥ÕÉ…Ñ¥½¸°…¹½µµ½¸•¹™½É•µ•¹ÐÉÕ±•Ì…É”¥¹ÍÁ•Ñ…‰±”¥¹ÁÕÑÌ¸5½‘•°Ý½É‘¥¹œµ…äÙ…Éä…É½ÍÌÉÕ¹Ì°ÁÉ½Ù¥‘•ÉÌ°…¹µ½‘•°É•Ù¥Í¥½¹Ì¸()=¹”‰åÑ”µ±•Ù•°ÁÉ½Á•ÉÑä¥Ìµ•¡…¹¥…±±äÕ…É…¹Ñ••è…™Ñ•È„AMM€É•Ù¥•Ü°™¥¹…°¹Ñ•á€¥Ì…¸•á…Ð½Áä½˜É•…±¥Í”¹Ñ•á€‰•…ÕÍ”¹¼™¥¹…°ÝÉ¥Ñ¥¹œ…±°½ÕÉÌ¸((ŒŒ¥±”µ‘É¥Ù•¸Ñ½½±¡…¥¸‘•Í¥¸()Q¡”É•Á½Í¥Ñ½ÉäÕÍ•Ì½É‘¥¹…Éä™¥±•Ì…¹5…­”‘•Á•¹‘•¹¥•ÌÉ…Ñ¡•ÈÑ¡…¸¡¥‘‘•¸½¹Ù•ÉÍ…Ñ¥½¹…°ÍÑ…Ñ”¸M½ÕÉ”°ÁÉ½µÁÑÌ°Ñ…É•ÑÌ°‰¥‰±¥½É…Á¡äµ•Ñ…‘…Ñ„°‘•É¥Ù•…ÉÑ•™…ÑÌ°…¹‘¥…¹½ÍÑ¥Ì…¸‰”¥¹ÍÁ•Ñ•…¹‘¥™™•Ý¥Ñ ¹½Éµ…°‘•Ù•±½Áµ•¹ÐÑ½½±Ì¸Q¡¥Ì¥ÌÑ¡”½É”½˜Ñ¡”½µÁ¥±•È™É…µ¥¹œè•áÁ±¥¥Ð…ÕÑ¡½É¥Ñä°•áÁ±¥¥Ð™…¥±ÕÉ”°‰½Õ¹‘•µ½‘•°…±±Ì°ÍÑ…‰±”ÁÉ½µÁÐ½µÁ½Í¥Ñ¥½¸°…¹‘¥ÍÁ½Í…‰±”•¹•É…Ñ•½ÕÑÁÕÑÌ¸