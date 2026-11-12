"""First-sign-in password change for the pre-provisioned demo administrator."""
import streamlit as st
from .. import db, passwords


def required(actor_id):
    row = db.one('SELECT MustChangePassword FROM dbo.Users WHERE UserId=?', (int(actor_id),))
    return bool(row and row.get('MustChangePassword'))


def show(actor):
    st.title('🔐 Secure your Administrator account')
    st.warning('This account was initialized using temporary demo credentials. Set a private password before using the application.')
    with st.form('rotate_initial_password'):
        current = st.text_input('Current temporary password',type='password')
        new = st.text_input('New private password (12–128 characters)',type='password')
        again = st.text_input('Confirm new password',type='password')
        submit=st.form_submit_button('Change password and sign in',type='primary')
    if not submit:return
    if new!=again:
        st.error('New passwords do not match.');return
    if new==current:
        st.error('Choose a different password from the temporary credential.');return
    try:
        passwords.validate_password(new)
        uid=int(actor['UserId'])
        row=db.one('SELECT PasswordHash,MustChangePassword FROM dbo.Users WHERE UserId=?',(uid,))
        if not row or not row['MustChangePassword'] or not passwords.verify(row['PasswordHash'],current):
            st.error('Current password was not accepted.');return
        updated=db.execute('UPDATE dbo.Users SET PasswordHash=?,MustChangePassword=0 WHERE UserId=? AND PasswordHash=? AND MustChangePassword=1',
                           (passwords.make_hash(new),uid,row['PasswordHash']))
        if updated!=1:
            st.error('Another session changed this account. Sign in again.');return
        st.session_state.clear()
        st.success('Password changed. Please sign in with the new password.')
        st.rerun()
    except Exception as exc:
        st.error('Password change failed: '+type(exc).__name__)
