import argparse
import sys
import time

import pytest
import pexpect

import yakonfig

def toy_main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--thing')
    modules = [yakonfig]
    args = yakonfig.parse_args(parser, modules)
    config = yakonfig.get_global_config()
    #dblogger.configure_logging(config)

@pytest.mark.parametrize(('dump_config',), [
        ('full',),
        ('default',),
        ('effective',),
        ])
def test_cli_dump(request, dump_config):

    cmd = 'python -m yakonfig.tests.test_dump_config --thing foo --dump-config %s' % dump_config

    child = pexpect.spawn(cmd)
    child.logfile = sys.stdout
    time.sleep(2)

    ## TODO: extend this so that --thing shows up in the config and
    ## check that it is present in the dump

    child.expect(pexpect.EOF, timeout=180)
    time.sleep(0.2)
    assert not child.isalive()
    assert child.exitstatus == 0

if __name__ == '__main__':
    toy_main()
