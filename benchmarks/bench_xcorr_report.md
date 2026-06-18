# batch_xcorr_cpp Benchmark

- data shape: (128, 256)
- dtype: float32
- mode: full
- repeat: 5 median timing
- original Madagascar comparison: unavailable

| implementation | backend | time_s | speedup_vs_python | peak_mem_mib | max_abs_error |
| --- | --- | ---: | ---: | ---: | ---: |
| python_numpy | python_numpy | 0.001133 | 1.000 | 0.252 | reference |
| hybrid_cpp | unavailable | n/a | n/a | n/a | n/a |
