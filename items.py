munin_config = node.metadata.get('munin', {})

symlinks = {}
actions = {}
files = {}
pkg_apt = {}
svc_systemd = {}

trigger_reload = []
if munin_config.get('type', 'c') == 'c':
    node_type = 'munin-node-c'

    pkg_apt['munin-node-c'] = {
        'installed': True,
    }
    pkg_apt['munin-node'] = {
        'installed': False,
    }

    files['/etc/xinetd.d/munin'] = {
        'content_type': 'jinja2',
        'owner': 'root',
        'group': 'root',
        'mode': '0644',
        'context': {
            'port': munin_config.get('port', 4949),
            'ips': ' '.join(sorted(munin_config.get('server_ips', []))),
        },
        'needs': [
            'pkg_apt:xinetd',
            'pkg_apt:munin-node-c',
        ],
        'triggers': [
            'svc_systemd:xinetd:restart',
        ]
    }

    files['/etc/munin/munin-node.conf'] = {
        'delete': True,
    }

elif munin_config.get('type', 'c') == 'perl':
    node_type = 'munin-node'

    pkg_apt['munin-node'] = {
        'installed': True,
    }
    pkg_apt['munin-node-c'] = {
        'installed': False,
    }

    files['/etc/xinetd.d/munin'] = {
        'delete': True,
    }

    svc_systemd['munin-node'] = {
        'needs': ['pkg_apt:munin-node'],
    }

    files['/etc/munin/munin-node.conf'] = {
        'content_type': 'jinja2',
        'owner': 'root',
        'group': 'root',
        'mode': '0644',
        'context': {
            'port': munin_config.get('port', 4949),
            'allow': '\n'.join(sorted(map(
                lambda x: "allow ^{}$".format(x.replace('.', '\\.')),
                munin_config.get('server_ips', [])
            ))),
            'hostname': munin_config.get('hostname', node.hostname),
        },
        'needs': [
            'pkg_apt:munin-node',
        ],
        'triggers': [
            'svc_systemd:munin-node:restart',
        ]
    }

    trigger_reload += ['svc_systemd:munin-node:restart']


needed_apt_pkg = set()

for plugin, plugin_config in munin_config.get('plugins', {}).items():
    executable = plugin_config.get('executable', '/usr/share/munin/plugins/{}'.format(plugin))

    if 'apt' in plugin_config:
        needed_apt_pkg.add(plugin_config['apt'])

    if executable == 'munin-plugins-c':
        # we know, which package this is in so add it automaticaly
        needed_apt_pkg.add('munin-plugins-c')
        target = '/usr/lib/munin-c/plugins/munin-plugins-c'

    elif "/" not in executable:
        target = "/usr/share/munin/plugins/{}".format(executable)
    else:
        target = executable

    symlinks['/etc/munin/plugins/{}'.format(plugin)] = {
        'target': target,
        'owner': 'root',
        'group': 'root',
        'needs': [
            'pkg_apt:xinetd',
            'pkg_apt:{}'.format(node_type),
        ],
        'triggers': trigger_reload,
    }

    if len(plugin_config.get('config', {})) > 0:
        config_content = [
            '# Written by bundlewrap, do not change',
            '',
        ]
        for name, config in sorted(plugin_config['config'].items(), key=lambda x: x[0]):
            config_content += ['[{}]'.format(name), ] + config + ['', ]

        files['/etc/munin/plugin-conf.d/{}'.format(plugin)] = {
            'content': '\n'.join(config_content) + '\n',
            'owner': 'root',
            'group': 'root',
            'needs': [
                'pkg_apt:{}'.format(node_type),
            ],
            'triggers': trigger_reload,
        }
    else:
        files['/etc/munin/plugin-conf.d/{}'.format(plugin)] = {
            'delete': True,
        }


for pkg in list(needed_apt_pkg):
    pkg_apt[pkg] = {
        'installed': True,
        'needs': [
            'pkg_apt:{}'.format(node_type),
        ],
    }
