# Compiled Prose: Constraint-Driven Outline

## Anchor

This essay is both an argument and an experiment. It asks what happens if academic and technical prose is treated in the way conceptual art has often treated physical execution: as a realisation of an upstream authored specification rather than as the unique locus of the work.

The domain is writing whose primary function includes the reliable transmission of concepts, arguments, procedures, or results. In such contexts, clarity is primal. The claim is not that prose is unimportant, nor that meaning is fully separable from language, nor that expressive writing is obsolete. The claim is that conceptual authorship and linguistic execution can sometimes be separated usefully and made independently inspectable.

*Compiled prose* names a model in which the authoritative intellectual artefact is a sufficiently explicit specification of claims, warrants, dependencies, scope, sources, uncertainty, and constraints. Natural-language prose is then a compiled realisation of that specification. The realisation matters and must be reviewed, but conceptual defects are repaired upstream rather than silently rewritten into the generated prose.

This sounds provocative when applied to writing, but the underlying separation of conception from execution is familiar in art practice. Sol LeWitt made the distinction explicit in conceptual art and in his instruction-based wall drawings, where the artist conceives and plans the work and a draftsman may realise it. [LeWitt 1967; LeWitt 1971]

Applying that distinction to academic prose exposes assumptions about where authorship, legitimacy, and intellectual seriousness are located. Academic writing is not merely a neutral transport layer: its genres and conventions are disciplinary social practices through which arguments are presented, communities recognise competent participation, and academic identities are constructed. [Hyland 2008; Hyland 2012; Hyland 2013]

The essay therefore does two related things:

1. develops the practical idea of a prose compiler; and
2. uses that mechanism as an art-informed critical intervention into academic writing.

The essay is itself produced using the method it describes. Its outline, sources, prompts, compilation passes, review, and generated prose are exposed separately. The repository is therefore not merely software accompanying the essay: the process and its artefacts form part of the work.

---

## I. The Experiment: Where Is the Work?

### I.1 Domain and boundary

- Concerned with academic and technical writing whose dominant purpose includes reliable transmission, coordination, reproducibility, explanation, or argument.
- Distinguish this domain from writing in which linguistic discovery, voice, aesthetic form, ambiguity, or expression is itself a primary part of the work.
- Compiled prose is not proposed as a universal model of writing.
- The model is useful only where a meaningful distinction can be made between what is being argued and the particular sentences used to realise that argument.

### I.2 The authorship question

Consider a human author who explicitly specifies:

- the claims to be made;
- their logical dependencies;
- the warrants connecting them;
- the evidence and sources supporting them;
- qualifications and uncertainty;
- scope and exclusions;
- intended argumentative order;
- material wording constraints where wording itself matters.

A machine then produces grammatical, coherent prose satisfying that specification.

The machine has plainly contributed causal labour. The question is where the intellectually authoritative contribution resides.

Central proposition: if materially different surface texts can faithfully realise the same sufficiently detailed conceptual specification, there is a coherent sense in which the specification rather than any one realisation can function as the primary authored object.

### I.3 Authorship and responsibility are distinct

- Relocating conceptual authorship upstream does not relocate responsibility.
- The human remains responsible for the specification, source selection, interpretation, generated realisation, and final claims presented to readers.
- Contemporary publishing guidance already distinguishes AI participation from accountable human authorship: ICMJE requires disclosure of AI assistance, rejects AI systems as authors, and retains human responsibility for generated material. [ICMJE 2026]
- This is evidence of an emerging practical separation between execution and accountability, not a universal definition of authorship.

---

## II. The Compiled Prose Model

### II.1 Separation of concept and execution

Conceptual source contains, where material:

- claims;
- warrants;
- evidence;
- citations;
- dependencies;
- scope;
- uncertainty;
- exclusions;
- required terminology and wording constraints.

Compiled realisation contains:

- sentences;
- paragraph transitions;
- local syntax;
- register;
- target-specific explanation density;
- conventional formatting and style.

The distinction is architectural, not absolute. Any surface feature that materially changes meaning belongs in the specification.

### II.2 The outline as source code

- The detailed outline is the authoritative artefact rather than a disposable planning aid.
- It must contain enough conceptual information that the execution system is not required to invent the argument.
- A sparse outline that forces the model to supply missing reasoning has delegated conceptual authorship downstream and therefore fails the model.
- Revision of the argument should normally occur by changing the authoritative source and recompiling.

### II.3 The compiler analogy

The software analogy is functional rather than literal.

The outline resembles source code because it is:

- upstream;
- authoritative;
- structured;
- inspectable;
- maintainable;
- capable of supporting multiple downstream realisations.

Generated prose resembles compiled output because it is:

- produced under explicit constraints;
- adapted to a target environment;
- replaceable by another conforming realisation;
- not the preferred location for repairing a conceptual defect.

Natural language is not machine code, and semantic equivalence cannot in general be mechanically guaranteed. The analogy describes an architecture of authorship and revision rather than a formal equivalence between programming and prose.

### II.4 Compilation passes

The current implementation makes transformations explicit:

1. **Draft** — faithful expansion of the specification.
2. **Smooth** — local readability and coherence.
3. **Revise** — cross-sectional consistency and redundancy reduction.
4. **Peer review** — diagnostic challenge to argument and execution.
5. **Final** — bounded response to accepted review findings.

Each pass may alter realisation but must preserve conceptual authority.

A missing argument, unsupported claim, unresolved ambiguity, or absent source is a defect in the specification and should propagate upstream rather than being silently repaired by a model.

### II.5 Targets as stylesheets

- Journals, disciplines, audiences, and genres act as compilation targets.
- Voice, register, formatting, and explanation density can be treated as explicit constraints rather than implicit conceptual authorship.
- One conceptual source can therefore support different legitimate realisations for different audiences.
- Retargeting must not silently change claims, evidence, or scope.
- If a new target genuinely requires different content, that difference belongs in the source or in an explicit source variant.

### II.6 Equivalence rather than byte-level determinism

- Compiled prose does not require identical generated sentences.
- Different models or runs may produce different acceptable surface forms.
- The relevant reproducibility requirement is preservation of source-level invariants: claims, dependencies, scope, evidence, qualifications, and other explicitly authored constraints.
- Surface variation is permitted; conceptual drift is not.

### II.7 LLMs as compilers, not authors

Within this model, an LLM is assigned an execution role:

- faithful expansion;
- grammatical realisation;
- local coherence;
- target-specific adaptation;
- bounded revision.

It is not authorised to:

- invent claims;
- supply missing warrants;
- introduce external theories or examples without source authority;
- invent citations;
- resolve ambiguity without instruction.

The pipeline therefore treats compliance with these constraints as something to verify rather than assume. Calling an LLM a compiler describes the role imposed on it, not a claim that model execution provides formal compilation guarantees.

---

## III. Art Precedent: Authorship Beyond Execution

### III.1 Conceptual art and prior conception

- Conceptual art provides a precedent for locating substantial authorship in conception and specification rather than fabrication alone.
- LeWitt characterises conceptual art as work in which planning and decisions precede execution and the idea functions as the generative mechanism for the work. [LeWitt 1967]
- The importance of the precedent is structural: a work can be substantially conceived before its physical execution.

### III.2 Instruction and delegated execution

LeWitt's wall drawings make the separation concrete:

- the artist conceives and plans the wall drawing;
- a draftsman may realise the plan;
- different draftsmen may interpret the same instructions differently;
- variation in execution is therefore expected rather than necessarily disqualifying;
- LeWitt nevertheless continues to distinguish the artist's plan from the draftsman's execution. [LeWitt 1971]

Structural correspondence:

- plan ↔ conceptual specification;
- draftsman ↔ execution engine;
- wall drawing ↔ prose realisation;
- fidelity to plan ↔ fidelity to authored semantic constraints.

The correspondence is an analogy, not an assertion that wall drawings and academic texts are the same kind of object.

### III.3 Wider conceptual-art context

- LeWitt belongs to a broader period in which artists deliberately questioned the relation among idea, object, process, and fabrication.
- Lippard and Chandler's contemporary discussion of the "dematerialization" of art records this movement away from treating the material object as the sole locus of the work. [Lippard and Chandler 1968]
- Art practice therefore supplies a mature precedent for asking a question that remains uncomfortable in writing: where exactly is the work?

### III.4 What the art analogy establishes

The art precedent does not prove that academic prose should be compiled.

It establishes that it is coherent to investigate whether:

- conception and execution can be distinguished;
- delegated execution can coexist with retained authorship;
- multiple realisations can instantiate a prior specification;
- execution quality can remain important even when execution is not the sole locus of authorship.

Compiled prose applies these possibilities experimentally to writing.

---

## IV. Academic Prose as Disciplinary Performance

### IV.1 Academic writing is not a neutral transport layer

- Academic genres are community-based conventions rather than generic containers for independently formed ideas.
- Texts are recognised as successful partly through forms familiar and convincing to disciplinary communities. [Hyland 2008]
- Specialist academic literacies are embedded in disciplinary beliefs and practices and participate in constructing knowledge, professional standing, and academic identity. [Hyland 2012; Hyland 2013]

Academic prose therefore performs at least two overlapping functions:

1. transmitting and negotiating intellectual content;
2. performing competent participation in a disciplinary community.

### IV.2 Convention is functional

The critique is not that convention is inherently defective.

Shared forms can:

- reduce interpretive uncertainty;
- communicate stance and evidential status;
- establish genre expectations;
- coordinate specialist writers and readers;
- make disciplinary communication more efficient;
- allow participants to recognise relevant forms of expertise and membership.

The problem is not convention itself but the difficulty of distinguishing what is conceptually necessary from what belongs to conventional execution.

### IV.3 Sacred execution

The original claim that academic prose treats execution as "sacred" is retained as an authored critical hypothesis, not as a historical or prevalence claim.

- The discourse account above supports the premise that disciplinary forms participate in recognition, standing, and academic identity. [Hyland 2008; Hyland 2012; Hyland 2013]
- The further inference made here is explicitly interpretive: where recognition attaches to competent performance of accepted prose forms, sentence-level execution can be taken as evidence of intellectual authorship rather than merely as one means of realising it.
- Compiled prose tests that inference by making the surface prose replaceable while holding the authored argument fixed and separately inspectable.
- In this limited sense, the experiment desacralises execution: prose remains important, but it is no longer automatically the authoritative object.

### IV.4 Liturgical prose

The liturgical analogy is an authored critical limit case derived from the same disciplinary-recognition premise, not a claim that academic writing generally behaves this way.

Consider a pathological case in which:

- inherited linguistic forms acquire authority through correct performance;
- insider recognition depends partly on mastery of those forms;
- deviation is penalised independently of underlying argument;
- surface performance therefore contributes to legitimacy as well as communication.

Conditional proposition: if academic style becomes sufficiently ritualised in this sense, correct performance can partly substitute for inspectable argumentative structure.

This is a critical possibility the experiment is designed to make inspectable, not a claim about how frequently academic prose behaves this way. The claim is also not that all specialised or difficult prose is ritual. Difficulty may be conceptually necessary.

### IV.5 Gesture as noise, borrowed weight, or camouflage

"Gesture" names linguistic performance whose principal contribution is neither semantic precision nor necessary argumentative structure but rhetorical or disciplinary effect.

Possible forms include:

- borrowed weight;
- conventional displays of seriousness;
- unnecessary opacity;
- rhetorical camouflage;
- stylistic signals of legitimacy.

A feature that materially communicates uncertainty, stance, disciplinary meaning, relationship among claims, or necessary nuance is not mere gesture.

Compiled prose provides an operational question: must this feature be present in the authoritative specification, or can it vary without changing the work?

---

## V. What the Separation Makes Visible

### V.1 Specification over performance

- Conceptual authority moves upstream into an inspectable artefact.
- Surface prose becomes contingent and replaceable within the limits fixed by that artefact.
- Conceptual changes should therefore be distinguishable from stylistic changes.

### V.2 Two objects of review

Compiled prose permits review of two different things.

**Conceptual source:**

- correctness;
- logic;
- evidence;
- scope;
- omissions;
- citation support;
- ambiguity.

**Compiled realisation:**

- readability;
- fidelity;
- clarity;
- target appropriateness;
- accidental semantic drift.

The separation does not guarantee easy review, but it makes disagreements easier to locate.

### V.3 Explicit revision

Revisions can be classified by where they belong:

- conceptual defect → change source;
- evidential defect → change source or supporting evidence;
- target/style defect → change target constraints;
- execution defect → change compiler behaviour or recompile.

Conventional prose editing often mixes these categories in one surface operation.

### V.4 Responsibility remains human

- The human author remains accountable for both the source and the realisation ultimately presented.
- Generated prose cannot be accepted merely because it conforms stylistically.
- Disclosure and review remain necessary where required by institutional practice. [ICMJE 2026]

---

## VI. Limits and Objections

### VI.1 Writing can itself be thinking

- A central objection is that, for some writers or kinds of work, sentence-level composition may be constitutive of thinking rather than downstream execution.
- In exploratory, literary, philosophical, poetic, or otherwise language-dependent work, conception may not precede execution cleanly.
- Compiled prose does not deny this possibility; it applies where explicit upstream specification is both possible and useful.

### VI.2 Meaning is not fully separable from wording

- Phrasing can change emphasis, implication, ambiguity, rhetorical force, and propositional meaning.
- Surface variation is therefore not automatically harmless.
- Material wording constraints belong in the source when particular language carries conceptual weight.
- Human review of the final realisation remains necessary.

### VI.3 Execution quality still matters

Generated prose can be awkward, unclear, misleading, generic, or inappropriate.

Relocating authorship upstream does not make execution aesthetically or practically irrelevant. It changes the status of the execution layer from authoritative source to evaluated realisation.

### VI.4 Specifications can fail

- An outline that omits a necessary warrant, distinction, source, or transition has not successfully transferred conceptual authorship upstream.
- The correct response is failure or an explicit gap, not downstream invention.
- Repair belongs in the authoritative source before recompilation.

### VI.5 The art analogy is a provocation, not a proof

- Conceptual art and academic prose operate in different institutional, semantic, and aesthetic contexts.
- The analogy is valuable because it makes a hidden assumption available for inspection: must execution be the privileged evidence of authorship?
- Compiled prose investigates the consequences of answering "not necessarily."

---

## VII. The Essay as Executable Artefact

### VII.1 The self-example

This essay is developed through the model it describes.

The public repository exposes:

- this authoritative outline;
- the sources identified below;
- stage prompts;
- target-style constraints;
- compilation tools;
- peer-review output;
- generated prose.

The repository is therefore both implementation and audit trail.

### VII.2 Upstream-only conceptual repair

Strong rule of the self-example:

**Conceptual defects discovered in generated prose are repaired in the authoritative outline rather than silently hand-edited into the final prose.**

Examples of source-level defects:

- missing argument;
- unsupported assertion;
- inadequate scope;
- missing citation;
- ambiguity requiring authorial resolution.

The essay is then recompiled.

### VII.3 What may be repaired downstream

Mechanical or execution-level defects may be addressed downstream only where they do not change conceptual content.

Examples:

- malformed LaTeX;
- formatting failure;
- compiler implementation bug.

If an edit changes what the essay says or why it says it, the change belongs upstream.

### VII.4 What a successful self-compilation demonstrates

A successful worked example would show that:

- a non-trivial argument can be maintained as explicit structured source;
- prose can be generated from that source without intentionally delegating conceptual invention;
- defects can be repaired upstream and propagated by recompilation;
- different surface realisations can be treated as executions of the same authored conceptual object when they preserve its invariants.

It would not show that:

- all writing should be compiled;
- conceptual authorship can always be completely specified;
- LLM output is automatically faithful;
- prose style lacks intellectual or aesthetic value.

---

## VIII. Closing Position

Compiled prose is simultaneously:

- a model of writing;
- a small technical system;
- an art-informed experiment in the location of authorship;
- a critical instrument for examining academic prose.

Its central claim is limited but consequential:

**In forms of writing where conceptual structure can be made sufficiently explicit, the authoritative intellectual artefact need not be identical with its surface prose realisation.**

Conceptual art supplies a precedent for separating conception from execution. Academic discourse research shows that linguistic form also performs disciplinary and social functions, so surface prose cannot simply be treated as a neutral container. Compiled prose brings these observations together by making conceptual source and linguistic performance independently visible.

The objective is not to abolish prose, style, convention, or authorship. It is to separate concerns that conventional writing often fuses:

- conception from execution;
- semantic structure from linguistic realisation;
- intellectual responsibility from causal production of sentences;
- disciplinary convention from conceptual necessity.

The final essay is itself the test. If its argument remains attributable to the human author while its sentences are machine-realised from a public specification, the experiment has made its central question concrete: where, exactly, is the work?

---

## Sources identified for the essay

### Conceptual art

**LeWitt 1967**  
Sol LeWitt, "Paragraphs on Conceptual Art," *Artforum* 5, no. 10 (June 1967): 79–83.

Supports the priority of conception and prior planning in conceptual art, including the formulation that "the idea becomes a machine that makes the art."

**LeWitt 1971**  
Sol LeWitt, "Doing Wall Drawings," *Art Now: New York* 3, no. 2 (June 1971).

Supports the distinction among artist, plan, draftsman, and realised work; delegated execution; and variation among realisations of a plan.

**Lippard and Chandler 1968**  
Lucy R. Lippard and John Chandler, "The Dematerialization of Art," *Art International* 12, no. 2 (February 1968): 31–36.

Provides contemporary context for the wider conceptual-art movement away from treating the material object as the sole locus of artistic work.

### Academic discourse

**Hyland 2008**  
Ken Hyland, "Genre and Academic Writing in the Disciplines," *Language Teaching* 41, no. 4 (2008): 543–562. DOI: 10.1017/S0261444808005235.

Supports the account of genre as community-based convention and the role of familiar disciplinary forms in successful academic texts.

**Hyland 2012**  
Ken Hyland, *Disciplinary Identities: Individuality and Community in Academic Discourse*. Cambridge: Cambridge University Press, 2012.

Supports the account of disciplinary discourse as a site of identity, positioning, conformity, individuality, and legitimate participation in academic communities.

**Hyland 2013**  
Ken Hyland, "Writing in the University: Education, Knowledge and Reputation," *Language Teaching* 46, no. 1 (2013): 53–70. DOI: 10.1017/S0261444811000036.

Supports the claim that specialist academic literacies are embedded in disciplinary practice and central to knowledge construction and professional academic life.

### AI-assisted academic authorship

**ICMJE 2026**  
International Committee of Medical Journal Editors, *Recommendations for the Conduct, Reporting, Editing, and Publication of Scholarly Work in Medical Journals*, current 2026 recommendations, sections on authorship and use of artificial intelligence in publishing.

Supports the limited contemporary example that AI assistance does not transfer responsibility away from human authors and should be disclosed. It is not treated as a universal account of academic authorship.
