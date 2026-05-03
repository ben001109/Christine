# Formula Inventory

All current formula implementations are `legacy research` and must be extracted from core runtime. This inventory is not a request to implement replacement formulas.

## Source Paper

- File: `/home/ben001109/Downloads/A_Five_Tensor_Formalism_for_Intersubjective_Cognition.pdf`
- Title: `A Five-Tensor Formalism for Intersubjective Cognition`
- Version: `Version 7 — Expanded Edition with Information Singularity Control`
- Pages: 41
- SHA-256: `17d53f3889b89345622227ad561912f8b3605627d6f43ba49289fd040163e1b1`

## Inventory

| ID | Concept | Paper Reference | Legacy Source | Status | Decision | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| F001 | Prefix complexity `K(x)`, conditional `K(x | y)` | Def 2.9, Thm 2.10-2.12 | `brain/intersubjective.py:74-89`, Appendix D | legacy | re-audit | Runtime uses gzip delta approximation; must separate theoretical K from computable proxy. |
| F002 | MCAP system and axioms | Def 3.1, Axiom 3.2, Def 3.3-3.4 | `christine_final.py:116969-117320`, `brain/intersubjective.py` | legacy | re-audit | Need define what `C_t`, `M_t`, `E` mean in Christine runtime before formulas. |
| F003 | Time simplex `Delta_T` and volume | Def 4.1, Lemma 4.2-4.3 | `brain/intersubjective.py:357-380`, `christine_final.py:118782-118813` | legacy | re-audit | Legacy code mixes discrete sums and continuous scaling; must define discrete approximation explicitly. |
| F004 | MCAP kernel `Phi` | Def 4.6, Lemma 4.7-4.9 | `brain/intersubjective.py:268-290`, `brain/intersubjective_v6_backup.py:104-120` | legacy | re-audit | Old v6 used vector triple-correlation, not Def 4.6. Current v7 uses gzip but not paper toy table values. |
| F005 | Existence tensor `T(M)` and `N(2)` | Def 5.1-5.2 | `brain/intersubjective.py:293-326` | legacy | re-audit | Need confirm indices, horizon, floor behavior, and scaling factor `T^2`. |
| F006 | Existence density `Psi` | Def 5.4, Thm 5.6-5.8 | `brain/intersubjective.py:358-385`, `christine_final.py:118811` | legacy | re-audit | Legacy self-test returns `35945.802` vs paper target `6.00`; not trusted. |
| F007 | Wisdom tensor and `N(4)` | Def 6.1-6.3 | `brain/intersubjective.py:300-340` | legacy | re-audit | Need validate temporal weights and reduction theorem before use. |
| F008 | Wisdom density `Psi_hat` and `WI` | Def 6.5, Def 6.8, Thm 6.6-6.9 | `brain/intersubjective.py:358-401` | legacy | re-audit | Legacy self-test returns `8506.665` vs paper target `7.56`; not trusted. |
| F009 | Perspective definition and canonical gauge | Def 7.1-7.6 | `brain/intersubjective.py:113-160`, Appendix D | legacy | re-audit | Paper says `M+1=2` in toy setup but lists `P0`, `P1`, `P2` and three raw weights. |
| F010 | Five-tensor `T_tilde` and `N(5)` | Def 7.8-7.9 | `brain/intersubjective.py:303-355`, Appendix D | legacy | re-audit | Need confirm `m` sum outside square and how conditional complexity includes perspective. |
| F011 | Empathy density `Psi_tilde` and `EI` | Def 7.11, Def 11.2 | `brain/intersubjective.py:358-406`, Appendix D | legacy | re-audit | Appendix D sanity check returns `8759.506`, not paper target `12.4`; not trusted. |
| F012 | Upper bounds | Thm 5.7, 6.7, 9.1 | `brain/intersubjective.py:424-433`, `christine_final.py:118600-118617` | legacy | re-audit | Legacy `Thm5.7` bound check fails in self-test. |
| F013 | Empathy threshold `beta*` | Thm 9.5, 9.10, Table 9.1 | `brain/intersubjective.py:415-422`, `christine_final.py:118619+` | legacy | re-audit | Monolith line `118507` documents a different formula (`Delta^2`) than paper Thm 9.10. |
| F014 | Solipsism/narcissism reductions | Thm 10.1, Cor 10.2 | `brain/intersubjective.py:459-474`, Appendix E | legacy | re-audit | Reduction depends on trusted `Psi_hat` and `Psi_tilde`, which are currently inconsistent. |
| F015 | Compassion decomposition | Def 10.5, Thm 10.6 | `brain/intersubjective.py:435-457`, Appendix E | legacy | re-audit | Structure may be mechanically true in legacy code but cannot validate paper until base formulas pass. |
| F016 | Trichotomy and convergence | Thm 11.1, 11.3 | Appendix E, `brain/intersubjective.py:490-566` | legacy | re-audit | Needs independent numerical fixtures, not random synthetic residuals. |
| F017 | Blow-up, retrieval, predictor | Def 13.1, 13.5, 13.9; Thm 13.2, 13.7, 13.10 | `brain/intersubjective.py:132-151`, `brain/intersubjective.py:476-566`, Appendix D/E | legacy | re-audit | Appendix E predictor test generates artificial data from the predictor itself; not a theorem validation. |
| F018 | Philosophy proxies `Phi_IIT`, qualia gap, AIXI, LIDA | Related-work/proxy layer, not Five-Tensor core | `brain/philosophy.py` | legacy | separate | These are heuristic proxies, not validated formulas from this PDF. |

## Immediate Decisions

- Do not expose old `Psi`, `PsiHat`, `PsiTilde`, `WI`, `EI`, `beta*`, theorem checks, or regime labels in core runtime.
- Preserve old code only as isolated research material during migration.
- Extract the formula subsystem out of `boot_christine.py`, `brain/`, GUI/status paths, and the monolith refactor target.
- Do not create replacement formula modules unless that is explicitly approved as a separate future project.
