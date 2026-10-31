"""Buttons to benchmark one or every ML-KEM variant and save to SQL Server."""
import streamlit as st
import pandas as pd
from .. import crypto_engine, experiments


def show(actor):
    st.title('⚡ ML-KEM Benchmark')
    st.caption('Measures actual cryptographic operations on THIS PC. Not ESP32 power/battery.')
    with st.form('benchmark'):
        algorithm = st.selectbox('Algorithm for single test', list(crypto_engine.ALGORITHMS))
        trials = st.number_input('Trials per algorithm', min_value=1,
                                 max_value=1000, value=10, step=1)
        col1, col2 = st.columns(2)
        one = col1.form_submit_button('▶️ Benchmark Selected Algorithm')
        all_three = col2.form_submit_button('🧪 Benchmark ALL 3 Algorithms')
    if not (one or all_three):
        st.info('Every trial measures KeyGen, Encaps and Decaps separately.')
        return
    selected = list(crypto_engine.ALGORITHMS) if all_three else [algorithm]
    collected = []
    progress = st.progress(0)
    for idx, algo in enumerate(selected):
        try:
            with st.spinner('Measuring ' + algo + ' ...'):
                exp_id, summary = experiments.run_and_save(
                    int(actor['UserId']), algo, int(trials),
                    lambda done, total, index=idx: progress.progress(
                        min((index + done / total) / len(selected), 1.0))
                )
            st.success(f'{algo}: experiment #{exp_id} saved.')
            for row in summary:
                collected.append({'Algorithm': algo, 'Experiment ID': exp_id, **row})
        except Exception as exc:
            st.error(f'{algo} failed: {exc}')
            break
    if collected:
        frame = pd.DataFrame(collected)
        st.dataframe(frame, hide_index=True, width='stretch')
        st.download_button('⬇️ Download Summary CSV', frame.to_csv(index=False).encode('utf-8'),
                           'quantumsafe_benchmark_summary.csv', 'text/csv')
