"""Administrator-only advisory page; API is opt-in and read-only."""
import os
import streamlit as st
from .. import research_catalog as catalog
from ..ai_research_advisor import build_context,local_advice,ask_llm
def show(actor):
    if actor.get('RoleName')!='Admin':st.error('Administrator only.');return
    st.title('✨ AI Research Advisor')
    st.caption('AI recommendations are advisory only. They never change gateway policy, trigger alarms, or deploy models.')
    version=st.selectbox('Evidence protocol',list(catalog.FILES),key='ai_proto')
    table=st.selectbox('Evidence table',list(catalog.FILES[version]),key='ai_table')
    rows=catalog.load(version,table)
    model=st.selectbox('Model',['All']+catalog.options(rows,'Model'),key='ai_model')
    split=st.selectbox('Split',['All']+catalog.options(rows,'Split'),key='ai_split')
    fold=st.selectbox('Fold',['All']+catalog.options(rows,'Fold'),key='ai_fold')
    bal=st.selectbox('Balancing',['All']+catalog.options(rows,'Balancing'),key='ai_bal')
    ctx=build_context(version,table,None if model=='All' else model,None if split=='All' else split,None if fold=='All' else fold,None if bal=='All' else bal)
    st.info(local_advice(ctx))
    st.caption('Source SHA256: '+ctx['source_sha256']+' · rows matching: '+str(ctx['count']))
    with st.expander('Exact evidence supplied to AI'):
        st.json(ctx)
    st.divider()
    st.subheader('Ask a genuine generative AI (optional)')
    st.warning('Requires your own OpenAI API key, internet connectivity and API billing. Only selected evidence and your question are sent. Never paste secrets or personal information into the question.')
    model_name=st.text_input('API model name',value=os.getenv('QUANTUMSAFE_AI_MODEL','gpt-4.1-mini'))
    key=st.text_input('OpenAI API key (not stored by this app)',type='password')
    question=st.text_area('Question',placeholder='Which model has lower FPR across folds, and what evidence is still missing?')
    if st.button('Ask AI',type='primary'):
        if not key:st.error('API key required; local evidence advisor above works without it.')
        else:
            try:
                with st.spinner('Querying AI API...'):
                    answer=ask_llm(ctx,question,key,model_name)
                st.markdown(answer)
            except Exception as e:st.error(str(e))
