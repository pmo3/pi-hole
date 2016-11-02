import pytest
from textwrap import dedent

SETUPVARS = {
    'PIHOLE_INTERFACE' : 'eth99',
    'IPV4_ADDRESS' : '1.1.1.1',
    'IPV6_ADDRESS' : 'FE80::240:D0FF:FE48:4672',
    'PIHOLE_DNS1' : '4.2.2.1',
    'PIHOLE_DNS2' : '4.2.2.2'
}

def test_setupVars_are_sourced_to_global_scope(Pihole):
    ''' currently update_dialogs sources setupVars with a dot, 
    then various other functions use the variables '''
    setup_var_file = 'cat <<EOF> /etc/pihole/setupVars.conf\n'
    for k,v in SETUPVARS.iteritems():
        setup_var_file += "{}={}\n".format(k, v)
    setup_var_file += "EOF\n"
    Pihole.run(setup_var_file)

    script = dedent('''\
    #!/bin/bash -e
    printSetupVars() {
        # Currently debug test function only
        echo "Outputting sourced variables"
        echo "PIHOLE_INTERFACE=\${PIHOLE_INTERFACE}"
        echo "IPv4_ADDRESS=\${IPv4_ADDRESS}"
        echo "IPv6_ADDRESS=\${IPv6_ADDRESS}"
        echo "PIHOLE_DNS1=\${PIHOLE_DNS1}"
        echo "PIHOLE_DNS2=\${PIHOLE_DNS2}"
    }
    update_dialogs() {
        . /etc/pihole/setupVars.conf
    }
    update_dialogs
    printSetupVars
    ''')

    output = run_script(Pihole, script).stdout

    for k,v in SETUPVARS.iteritems():
        assert "{}={}".format(k, v) in output

def test_setupVars_saved_to_file(Pihole):
    ''' confirm saved settings are written to a file for future updates to re-use '''
    set_setup_vars = '\n'  # dedent works better with this and padding matching script below
    for k,v in SETUPVARS.iteritems():
        set_setup_vars += "    {}={}\n".format(k, v)
    Pihole.run(set_setup_vars).stdout

    script = dedent('''\
    #!/bin/bash -e
    echo start
    TERM=xterm
    PHTEST=TRUE
    source /opt/pihole/basic-install.sh
    {}
    finalExports
    cat /etc/pihole/setupVars.conf
    '''.format(set_setup_vars))

    output = run_script(Pihole, script).stdout

    for k,v in SETUPVARS.iteritems():
        assert "{}={}".format(k, v) in output

def run_script(Pihole, script, file="/test.sh"):
    _write_test_script(Pihole, script, file=file)
    result = Pihole.run(file)
    assert result.rc == 0
    return result

def _write_test_script(Pihole, script, file):
    ''' Running the test script blocks directly can behave differently with regard to global vars '''
    ''' this is a cheap work around to that until all functions no longer rely on global variables '''
    Pihole.run('cat <<EOF> {file}\n{script}\nEOF'.format(file=file, script=script))
    Pihole.run('chmod +x {}'.format(file))
