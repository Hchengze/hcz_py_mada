# My Workflows

This directory contains small local workflows that combine existing
`pymadagascar` APIs. They do not require original Madagascar, external datasets,
or C++ extensions.

Run from the project root after editable install:

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe examples\my_workflows\basic_rsf_io_workflow.py
```

File-writing workflow scripts accept an optional output directory:

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe examples\my_workflows\fft_bandpass_workflow.py examples\my_workflows\_outputs\fft_test
```

Without an argument, file-writing workflow outputs go to a newly created system temporary directory.
For persistent outputs, pass a directory explicitly:

```text
examples/my_workflows/_outputs/<workflow-name>/
```

## Workflow Inventory

| Workflow | Purpose | Main modules | Outputs | Status |
| --- | --- | --- | --- | --- |
| `basic_rsf_io_workflow.py` | Write, read, and copy a small RSF file with axis metadata. | `pymadagascar.io.rsf` | `basic_input.rsf`, `basic_copy.rsf` | stable subset |
| `spike_math_window_workflow.py` | Generate a spike panel, create a coordinate expression, and window it. | `generic.spike`, `generic.math`, `generic.window`, `core.Axis` | `spike_panel.rsf`, `math_panel.rsf`, `math_window.rsf` | stable subset |
| `fft_bandpass_workflow.py` | Build a mixed-frequency trace, compute an RFFT, and apply a bandpass. | `signal.fft`, `signal.filter`, `io.rsf` | `mixed_trace.rsf`, `mixed_trace_rfft.rsf`, `mixed_trace_bandpass.rsf` | stable subset |
| `lsqr_minimal_example.py` | Compare bounded LSQR with dense least squares and demonstrate `LeastSquaresProblem` regularization. | `generic.operators`, `generic.least_squares`, `generic.regularization`, `generic.solvers` | printed model/residual/objective summary only | learning prototype |
| `plot_grey_graph_workflow.py` | Save quicklook graph and grey PNGs from synthetic data. | `plot.graph`, `plot.grey`, `io.rsf` | `plot_trace.rsf`, `plot_panel.rsf`, `plot_trace_graph.png`, `plot_panel_grey.png` | partial plotting substitute |
| `seismic_basic_agc_mute_stack_workflow.py` | Process a tiny synthetic gather with AGC, mute, stack, and graph. | `seismic.agc`, `seismic.mute`, `seismic.stack`, `plot.graph`, `io.rsf` | `synthetic_gather.rsf`, `synthetic_gather_agc.rsf`, `synthetic_gather_mute.rsf`, `synthetic_stack.rsf`, `synthetic_stack_graph.png` | stable subset |
| `das_void_diffraction_workflow.py` | Generate a kinematic DAS shot gather, apply the existing FK prototype, overlay void diffraction curves, invert simulated picks, and write regular-linear DAS geometry metadata. | `signal.wavelet`, `seismic.fk`, `plot.grey`, `io.rsf`, workflow-only NumPy helpers | raw/filtered RSF gathers, two PNGs, picks CSV, inversion JSON with `das_geometry` | workflow prototype |
| `seismic_signal_contract_workflow.py` | Run the S1 deterministic gather contract through existing conditioning, bandpass, AGC, mute, stack, PSD, and quicklook APIs. | `testing.seismic_fixtures`, `signal.qc`, `signal.filter`, `seismic.agc/mute/stack`, `signal.spectral`, `plot.grey` | raw/processed/stack/PSD RSFs, quicklook PNG, metrics JSON | internal contract regression |
| `seismic_signal_metrics_workflow.py` | Evaluate the S1 gather pipeline with deterministic SNR, band-energy, mute, stack, finite-value, and header-axis metrics. | `testing.seismic_fixtures`, `testing.seismic_metrics`, existing signal/seismic processing APIs, `plot.grey` | raw/intermediate/processed/stack RSFs, quicklook PNG, internal QC report JSON | internal QC regression |
| `seismic_nmo_contract_workflow.py` | Exercise the existing NMO prototype on the S1 signed-offset fixture and compare correct, absent, and wrong velocity behavior with S2 metrics. | `seismic.nmo`, `seismic.stack`, `testing.seismic_fixtures`, `testing.seismic_metrics`, `plot.grey` | raw/corrected gathers, pre/post/wrong-velocity stacks, quicklook PNG, internal QC report JSON | prototype contract regression |
| `seismic_semblance_contract_workflow.py` | Exercise the existing Semblance prototype on the S1 signed-offset fixture and compare true-velocity versus wrong-velocity response after the S3 source audit. | `seismic.semblance`, `seismic.nmo`, `seismic.stack`, `testing.seismic_fixtures`, `testing.seismic_metrics`, `plot.grey` | raw gather, velocity panel, true/wrong NMO stacks, quicklook PNG, internal QC report JSON | prototype contract regression |
| `seismic_geometry_contract_workflow.py` | Design-check the S4-2 small-gather geometry boundary between regular RSF offsets, explicit offset vectors, and minimal source/receiver tables. | `testing.seismic_fixtures`, `testing.seismic_geometry`, `testing.seismic_metrics`, `io.rsf` | S1-compatible gather RSF, explicit offset-vector RSF, minimal source/receiver table RSF, internal JSON report | internal geometry contract |
| `seismic_fk_contract_workflow.py` | Validate the existing FK prototype on deterministic regular plane-wave panels and compare fan-filter target-slope preservation versus reject-slope suppression after source audit. | `seismic.fk`, `plot.grey`, `testing.seismic_metrics`, `io.rsf` | raw panel RSF, FK spectrum RSF, filtered panel RSF, quicklook PNG, internal QC report JSON | prototype contract regression |
| `seismic_small_gather_processing_workflow.py` | Combine S1-S4 fixture, metrics, geometry, NMO, Semblance, and FK contracts into one deterministic small-gather processing regression. | `testing.seismic_fixtures`, `testing.seismic_geometry`, `testing.seismic_metrics`, `signal.qc/filter`, `seismic.nmo/semblance/fk/stack`, `plot.grey` | raw/processed/NMO/Semblance/FK RSFs, stacks, quicklook PNGs, internal JSON report | integrated workflow regression |
| `seismic_slant_stack_contract_workflow.py` | Validate the existing Radon/slant prototype as a small sfslant-style adjoint/modeling pair with analytic slope focusing and dot-test checks. | `seismic.radon`, `plot.grey`, `testing.seismic_metrics`, `io.rsf` | analytic gather RSF, slant panel RSF, model RSF, modeled gather RSF, quicklook PNG, internal QC report JSON | prototype contract regression |

## Notes

- All inputs are generated synthetically inside the script.
- No script reads `src-master` or calls original `sf*` programs.
- Plot workflows require Matplotlib, which is included in the project test extra.
- The LSQR minimal example is in-memory only. It writes no files, calls no CLI,
  and does not enable preconditioned LSQR.
- These examples are meant to be copied and edited for local work. They prefer
  small, explicit arrays and simple metadata over clever abstractions.
- The DAS void workflow is deliberately kinematic. Its `das_geometry` JSON
  contract records regular-linear local metadata for tests and future workflow
  design, but it is not a DAS file adapter, gauge-response model, elastic
  forward model, or production void-detection method.
- The S1 contract workflow is deterministic testing infrastructure. It defines
  a regular signed-offset small-gather baseline and is not a production
  processing recipe.
- The S2 metrics workflow reports broad regression checks for the S1 fixture.
  Its JSON schema is internal and its thresholds are not field-data acceptance
  criteria.
- The S3 NMO workflow requires `half=n` for the S1 full signed-offset axis. It
  validates a small regular CMP-like fixture and is not a velocity-analysis or
  production NMO workflow.
- The S4-1 Semblance workflow references `../src-master/system/seismic/Mvscan.c`
  as the source-audit target, but it does not call original Madagascar and is
  not a full `sfvscan` clone.
- The S4-2 geometry workflow references Madagascar NMO/Vscan/slant/Radon and
  header-table source boundaries, but it does not call original Madagascar,
  implement SEG-Y trace headers, or create a production survey geometry model.
- The S4-3 FK workflow references `../src-master/system/generic/Mdipfilter.c`
  as the nearest source-audit target and records that no direct `Mfk.c` clone
  was found. It does not call original Madagascar and is not a full
  `sfdipfilter` implementation.
- The S5 integrated small-gather workflow combines existing S1-S4 contracts into
  one path-free internal JSON report. It adds no algorithm and is not production
  velocity analysis, field-scale processing, SEG-Y/header work, Radon, inversion,
  modeling, or imaging.
- The S6-2 slant-stack workflow treats `radon` as `m=A^T d` and `iradon` as
  `d=A m` for a small deterministic fixture. It is not full `sfslant`, not
  high-resolution `sfradon`, not solved inversion, and not velocity picking.
- Imaging/modeling, NMO/Semblance/FK/Radon, and SEG-Y remain prototype areas in
  the broader project; workflows using them retain that prototype status.
