"""Admin-only practical ML advice, tied to actual training evidence."""
import os
import streamlit as st
from ..ai_research_advisor import ask_llm
from ..ml_decision_support import summarize_training, practical_guidance

def show_embedded(actor):
    if actor.get('RoleName')!='Admin': st.error('Administrator only.');return
    st.subheader('✨ AI-assisted model improvement')
    st.caption('Works with your most recently trained model. AI cannot secretly alter training code, enable live inference, or deploy a model.')
    result=st.session_state.get('qs_training_result')
    if not result:
        st.info('First train a model in Train & compare. This assistant will then examine its REAL held-out and fold metrics.')
        return
    evidence=summarize_training(result)
    st.info(practical_guidance(evidence))
    with st.expander('Metrics sent to AI (never the model file or raw training rows)'):
        st.json(evidence)
    st.divider()
    st.markdown('**Optional generative AI feedback**')
    st.caption('Requires an API key and internet. Only metrics and your question are sent to the provider; never paste private data or credentials.')
    model=st.text_input('AI model ID',value=os.getenv('QUANTUMSAFE_AI_MODEL','gpt-4.1-mini'),key='ml_ai_model')
    key=st.text_input('API key (session only)',type='password',key='ml_ai_key')
    question=st.text_area('What should the model improve?',value='Review false positives, fold consistency, and readiness for IoT gateway use. Suggest safe next training experiments.',key='ml_ai_question')
    if st.button('✨ Analyze training results',type='primary',key='ml_ai_ask'):
        if not key:st.error('Enter an API key, or use the offline recommendations above.')
        else:
            try:
                with st.spinner('Analyzing metrics...'):reply=ask_llm(evidence,question,key,model)
                st.markdown(reply)
            except Exception as exc:st.error('AI request failed: '+str(exc))

def show(actor):show_embedded(actor)
