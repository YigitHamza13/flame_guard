# Validation and operation

Release 2.2.0 is an independent research workspace, not NASA-approved flight safety software.

Implemented: immutable SQLite imports, original row preservation, source PDF hashes and page references, separate combustion outcomes, disputed SIBAL counts, restored study pressure, condition comparisons, contextual exports, robust optional excerpt selection and regression tests.

Open scientific acceptance tasks: independently approve the 11 reviewed rows; reconcile reused SIBAL specimens; establish mission-specific geometry, airflow and uncertainty requirements. All human approvals remain pending. No risk score is calculated.

User-study protocol (not yet performed): recruit 5–8 relevant researchers; counterbalance document-only versus application workflows; ask participants to locate WIF pressure, distinguish Saffire ignition from sustained burning, identify the SIBAL discrepancy and export a lunar evidence gap. Record completion time, source correctness, unsupported conclusions and task success. Report anonymized observations before claiming improved speed or accuracy.

Demo: choose ISS, enter oxygen 21% and pressure 101.325 kPa, select WIF, inspect four outcomes and source pages, change to lunar habitat, inspect gravity mismatch, include PMMA, export the research brief and CSV.

Operating assumptions: one Streamlit process with writable local data storage; snapshots can be rebuilt from packaged inputs. Multi-instance shared writes require a database architecture review. Sessions and research history are temporary. No authentication is supplied; use hosting access controls for a private research deployment. Public source data only.

Costs: hosting and optional Gemini charges depend on the selected provider and usage; no current price is asserted. Estimate monthly cost as hosting + requests × input/output token usage × provider rates + maintenance hours. Planning assumption: 2–4 maintenance hours per month, plus domain-expert review per new source; these are estimates, not measured costs. Local search has no model API charge. Benchmark workload and verify provider prices before deployment.

NASA BASS-II photo ISS038-E-046394 is used for educational experiment context with attribution, without endorsement claims. Source: https://www.nasa.gov/image-article/astronaut-mike-hopkins-sets-up-bass-experiment/ . Media guidance checked 2026-11-14: https://www.nasa.gov/nasa-brand-center/images-and-media/ . Planet textures remain credited to Solar System Scope under CC BY 4.0.
