"""Read-only, evidence-based interactive charts for all authenticated users."""
from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from .. import analytics_data

# Consistent semantic palette: azure observations, mint authorized, coral rejected,
# amber caution, neutral steel. These are user-approved visual design tokens.
COLORS={'allow':'#2DD4A7','block':'#FF5C79','accent':'#56B5FF',
        'warning':'#FBBF55','text':'#DCE9FA','grid':'rgba(127,160,200,.17)',
        'background':'rgba(0,0,0,0)'}


def _style(fig,height=310):
    fig.update_layout(
        height=height,margin=dict(t=36,b=36,l=24,r=24),
        paper_bgcolor=COLORS['background'],plot_bgcolor=COLORS['background'],
        font=dict(family='Inter, Segoe UI, Arial',color=COLORS['text'],size=12),
        legend=dict(orientation='h',yanchor='bottom',y=1.02,x=0),
        hoverlabel=dict(bgcolor='#172A42',font_color='#F1F7FF'),
        hovermode='x unified',
    )
    fig.update_xaxes(gridcolor=COLORS['grid'],zeroline=False)
    fig.update_yaxes(gridcolor=COLORS['grid'],zeroline=False,rangemode='tozero')
    return fig


def _card():
    st.markdown('''<style>
    .qs-chart-title{font:650 16px 'Segoe UI',Arial;color:#8BCBFF;margin:.45rem 0 .1rem}
    .qs-chart-note{font:12px 'Segoe UI',Arial;color:#829AB6;margin-bottom:.45rem}
    .stPlotlyChart{border:1px solid rgba(94,148,191,.22);border-radius:16px;
      background:linear-gradient(145deg,rgba(8,23,41,.74),rgba(12,38,66,.43));
      padding:8px;box-shadow:0 15px 26px rgba(0,0,0,.14)}
    </style>''',unsafe_allow_html=True)


def _title(name,description):
    st.markdown(f'<div class="qs-chart-title">{name}</div><div class="qs-chart-note">{description}</div>',unsafe_allow_html=True)


def build_timeline(agg):
    items=list(agg['by_bucket'].items());fig=go.Figure()
    for decision,col in [('ALLOW',COLORS['allow']),('BLOCK',COLORS['block'])]:
        fig.add_bar(name='Allowed' if decision=='ALLOW' else 'Rejected',x=[k for k,_ in items],
                    y=[v[decision] for _,v in items],marker_color=col,
                    hovertemplate='%{x|%Y-%m-%d %H:%M} UTC<br>Requests %{y}<extra></extra>')
    fig.update_layout(barmode='stack',title=None)
    return _style(fig)


def build_outcomes(agg):
    fig=go.Figure(go.Pie(labels=['Allowed','Blocked'],values=[agg['allow'],agg['block']],
                         hole=.72,marker=dict(colors=[COLORS['allow'],COLORS['block']]),
                         textinfo='label+percent',sort=False,
                         hovertemplate='%{label}: %{value} requests<extra></extra>'))
    fig.update_layout(showlegend=False,annotations=[dict(text=str(agg['total']),font=dict(size=29,color=COLORS['text']),showarrow=False)])
    return _style(fig)


def build_reasons(agg):
    items=sorted(agg['reasons'].items(),key=lambda x:x[1],reverse=True)[:10]
    fig=go.Figure(go.Bar(x=[c for _,c in items][::-1],y=[r for r,_ in items][::-1],orientation='h',
                         marker_color=COLORS['block'],text=[str(c) for _,c in items][::-1],textposition='outside',
                         hovertemplate='%{y}: %{x}<extra></extra>'))
    fig.update_layout(margin=dict(l=22,r=30,t=36,b=30))
    return _style(fig,height=max(290,40*len(items)+100))


def build_devices(agg):
    items=sorted(agg['by_device'].items(),key=lambda x:sum(x[1].values()),reverse=True)[:14]
    fig=go.Figure()
    for key,col,name in [('ALLOW',COLORS['allow'],'Authorized'),('BLOCK',COLORS['block'],'Rejected')]:
        fig.add_bar(name=name,x=[k for k,_ in items],y=[v[key] for _,v in items],marker_color=col)
    fig.update_layout(barmode='group')
    fig.update_xaxes(tickangle=-25)
    return _style(fig,height=350)


def build_readings(data):
    fig=go.Figure()
    colors=[COLORS['accent'],COLORS['allow'],COLORS['warning'],'#9D85FF','#FD8B65']
    for i,(device,values) in enumerate(sorted(data.items())[:5]):
        fig.add_scatter(name=device,mode='lines+markers',x=[x['time_utc'] for x in values],
                        y=[x['reading'] for x in values],line=dict(color=colors[i],width=2.4,shape='spline',smoothing=.3),
                        marker=dict(size=4),hovertemplate='%{x|%H:%M:%S} UTC<br>Reading %{y:.2f}<extra>'+device+'</extra>')
    return _style(fig,360)


def build_model_performance(models):
    fig=go.Figure()
    eligible=[m for m in models if isinstance(m.get('macro_f1'),(int,float)) and isinstance(m.get('latency_ms_per_row'),(int,float))]
    for alg in sorted({m['algorithm'] for m in eligible}):
        grp=[m for m in eligible if m['algorithm']==alg]
        fig.add_scatter(name=alg,mode='markers',x=[m.get('latency_ms_per_row') for m in grp],
                        y=[m['macro_f1']*100 for m in grp],text=[f"Model #{m['id']} · {m['status']}" for m in grp],
                        marker=dict(size=[max(9,min(24,9+(m['features'] or 0)/2)) for m in grp],
                                    line=dict(color='#D8EAFF',width=.8)),
                        hovertemplate='%{text}<br>Latency %{x:.4f} ms/row<br>Macro F1 %{y:.2f}%<extra></extra>')
    fig.update_xaxes(title='Inference latency (ms per row)')
    fig.update_yaxes(title='Held-out Macro-F1 (%)',range=[0,101])
    return _style(fig,350)


@st.fragment(run_every='10s')
def _live_dashboard():
    from .security_console import collect
    data,sql_status=collect()
    # Only real collected events, with timestamp and decision validation.
    hours=st.session_state.get('qs_analytics_hours',24)
    agg=analytics_data.aggregate(data['events'],hours=hours)
    cols=st.columns(5)
    cols[0].metric('Observed requests',agg['total'])
    cols[1].metric('Authorized',agg['allow'])
    cols[2].metric('Rejected',agg['block'])
    cols[3].metric('Rejection rate',f"{100*agg['block']/agg['total']:.1f}%" if agg['total'] else '—')
    cols[4].metric('Devices observed',len(agg['by_device']))
    st.caption(f'{sql_status} · Time labels UTC · Available virtual gateway events (telemetry and encrypted messages, not captured IP packets). '
               f'History is bounded; a 24h filter does not guarantee full 24h retention. Updated every 10 seconds.')
    if agg['total']<1:
        st.info('No gateway activity in the selected time window. Start the gateway and generate real virtual-device readings or security tests to populate charts.')
    else:
        l,r=st.columns([1.7,1])
        with l:
            _title('Activity timeline','Observed authorized vs rejected virtual gateway requests · 15-minute intervals')
            st.plotly_chart(build_timeline(agg),key='qs_timeline',use_container_width=True,config={'displaylogo':False})
        with r:
            _title('Request outcomes','Actual decisions in the visible event history')
            st.plotly_chart(build_outcomes(agg),key='qs_outcomes',use_container_width=True,config={'displaylogo':False})
        l,r=st.columns(2)
        with l:
            _title('Threat reason distribution','Rejected requests grouped by actual gateway reason')
            if agg['reasons']:st.plotly_chart(build_reasons(agg),key='qs_reasons',use_container_width=True,config={'displaylogo':False})
            else:st.success('No rejected requests in this observation window')
        with r:
            _title('Device activity','Authorized and rejected requests for each observed virtual identity')
            st.plotly_chart(build_devices(agg),key='qs_device_bars',use_container_width=True,config={'displaylogo':False})
        _title('Virtual device telemetry','Real received, authenticated readings · last 300 readings per device')
        if agg['readings']:
            st.plotly_chart(build_readings(agg['readings']),key='qs_readings',use_container_width=True,config={'displaylogo':False})
        else:st.info('No authenticated numeric readings yet.')
    st.divider()
    st.subheader('🧠 ML Model performance · measured held-out results')
    try:
        from ..ml_engine import registry
        model_rows=analytics_data.model_summary(registry.models())
    except Exception as exc:
        model_rows=[];st.warning('ML model registry unavailable: '+type(exc).__name__)
    if model_rows:
        st.plotly_chart(build_model_performance(model_rows),key='qs_ml_perf',use_container_width=True,config={'displaylogo':False})
        st.dataframe(pd.DataFrame(model_rows),hide_index=True,use_container_width=True)
        st.caption('This chart compares stored test metrics. It does not prove real-time physical network detection. Imported but unverified models may lack metrics.')
    else:st.info('No saved model evaluations found. Administrator can train and validate models in ML & AI Control.')
    st.divider()
    st.subheader('📑 Recent observed security evidence')
    if agg['rows']:
        display=[{'Time UTC':x['time_utc'].isoformat(timespec='seconds'),
                  'Device ID':x['device'],'Decision':x['decision'],'Reason':x['reason'],
                  'Source IP':x['source_ip'],'Reading':x['reading']} for x in analytics_data.newest_rows(agg, 200)]
        st.dataframe(pd.DataFrame(display),use_container_width=True,hide_index=True)
    if st.session_state.get('qs_analytics_actor_role')=='Admin' and agg['rows']:
        csvbuf=pd.DataFrame([{**x,'time_utc':x['time_utc'].isoformat()} for x in agg['rows']]).to_csv(index=False).encode('utf-8-sig')
        st.download_button('⬇ Export observed events CSV',csvbuf,'QuantumSafe_Observed_Analytics.csv','text/csv',key='qs_graphs_export')


def show(actor):
    if actor.get('RoleName') not in ('Admin','Researcher'):
        raise PermissionError('Authenticated monitoring access required')
    st.title('📈 Security Analytics & Intelligence')
    st.caption('Modern interactive visualizations from genuine local virtual gateway events and saved model evaluations.')
    _card()
    st.session_state['qs_analytics_actor_role']=actor['RoleName']
    st.select_slider('Observation window',options=[1,3,6,12,24],value=24,
                     format_func=lambda v:f'Last {v} hour'+('s' if v!=1 else ''),key='qs_analytics_hours')
    _live_dashboard()
