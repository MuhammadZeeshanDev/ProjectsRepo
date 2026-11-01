from pathlib import Path
from unittest.mock import patch
from quantumsafe.pc_b_launcher import console_is_running, launch_console

def test_running_console_does_not_spawn():
    with patch('quantumsafe.pc_b_launcher.console_is_running', return_value=True), \
         patch('quantumsafe.pc_b_launcher.subprocess.Popen') as spawn, \
         patch('quantumsafe.pc_b_launcher.webbrowser.open') as browser:
        assert launch_console() == 'http://127.0.0.1:8502'
        spawn.assert_not_called()
        browser.assert_called_once()

def test_launch_has_no_secret_arguments():
    with patch('quantumsafe.pc_b_launcher.console_is_running', side_effect=[False, True]), \
         patch('quantumsafe.pc_b_launcher.subprocess.Popen') as spawn:
        assert launch_console(open_browser=False).endswith(':8502')
        args=spawn.call_args.args[0]
        assert 'streamlit' in args and 'attacker_console.py' in ' '.join(args)
        assert '--server.address' in args and '127.0.0.1' in args
        assert not any('token=' in x or 'secret=' in x for x in args)
