"""Screen 5: experiment history, chart and CSV download."""
import io
import pandas as pd
import streamlit as st
from .. import experiments


def show(actor):
    st.title("📊 Saved Results")
    try:
        history = experiments.history(int(actor["UserId"]))
    except Exception:
        st.error("Could not read results. Check your SQL Server connection.")
        return
    if not history:
        st.info("No benchmarks saved yet. Run your first experiment.")
        return
    frame = pd.DataFrame(history)
    st.dataframe(frame, hide_index=True, width='stretch')
    complete = frame.loc[frame.RunStatus == "Completed", "ExperimentId"].tolist()
    if not complete:
        st.info("No completed measurements to chart yet.")
        return
    if st.button('📈 Compare latest saved ML-KEM-512 / 768 / 1024'):
        latest = {}
        for record in history:
            if record['RunStatus'] == 'Completed':
                latest.setdefault(record['Algorithm'], record['ExperimentId'])
        comparison = []
        for algorithm, chosen_id in latest.items():
            entries = experiments.measurements(int(actor['UserId']), int(chosen_id))
            if not entries:
                continue
            frame_alg = pd.DataFrame(entries)
            for op, group in frame_alg.groupby('OperationName'):
                comparison.append({'Algorithm': algorithm, 'Operation': op,
                                   'Median (ms)': group['DurationNs'].median() / 1e6,
                                   'Experiment ID': chosen_id})
        if comparison:
            data_compare = pd.DataFrame(comparison)
            st.dataframe(data_compare, hide_index=True, width='stretch')
            chart = data_compare.pivot(index='Algorithm', columns='Operation',
                                       values='Median (ms)')
            st.bar_chart(chart)
            st.download_button('⬇️ Download Comparison CSV',
                               data_compare.to_csv(index=False).encode('utf-8'),
                               'quantumsafe_algorithm_comparison.csv', 'text/csv')
        else:
            st.warning('No completed benchmark measurements available for comparison.')
    exp_id = st.selectbox("Show experiment", complete)
    samples = experiments.measurements(int(actor["UserId"]), int(exp_id))
    if not samples:
        st.warning("This experiment has no saved measurements.")
        return
    data = pd.DataFrame(samples)
    data["Duration_ms"] = data["DurationNs"] / 1_000_000
    summary = data.groupby("OperationName")["Duration_ms"].median().reset_index()
    st.bar_chart(summary.set_index("OperationName"))
    st.dataframe(summary.rename(columns={"Duration_ms": "Median (ms)"}),
                 hide_index=True, width='stretch')
    csv = data.to_csv(index=False).encode("utf-8")
    st.download_button("Download measured data (CSV)", csv,
                       file_name=f"quantumsafe_experiment_{exp_id}.csv",
                       mime="text/csv")
    st.caption("CSV contains real host timings and experiment identifiers only.")
