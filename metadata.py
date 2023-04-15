defaults = {
    'munin': {
        'plugins': {},
    },
}


@metadata_reactor
def add_iptables_rules(metadata):
    if not node.has_bundle("iptables"):
        raise DoNotRunAgain

    munin_server = repo.get_node(metadata.get('munin/server', ''))

    if munin_server.partial_metadata == {}:
        return {}

    munin_server_ips = []
    interfaces = [metadata.get('main_interface'), ]
    interfaces += metadata.get('munin/additional_interfaces', [])

    for interface, interface_config in munin_server.partial_metadata.get('interfaces', {}).items():
        if interface not in interfaces and interface != munin_server.partial_metadata.get('main_interface'):
            continue

        munin_server_ips += interface_config.get('ip_addresses', [])
        munin_server_ips += interface_config.get('ipv6_addresses', [])

    iptables_rules = {}

    for interface in interfaces:
        for ip in munin_server_ips:
            iptables_rules += repo.libs.iptables.accept(). \
                input(interface). \
                state_new(). \
                tcp(). \
                source(ip). \
                dest_port(metadata.get('munin/port', 4949))

    return {
        'iptables': iptables_rules['iptables'],
        'munin': {
            'server_ips': list(dict.fromkeys(munin_server_ips))
        }
    }


@metadata_reactor
def add_munin_plugin_for_interfaces(metadata):
    plugins = {}
    for interface, config in metadata.get('interfaces', {}).items():
        if ':' in interface:
            continue

        plugins['if_{}'.format(interface)] = {
            'executable': 'if_',
            'apt': 'munin-plugins-core',
        }
        plugins['if_err_{}'.format(interface)] = {
            'executable': 'if_err_',
            'apt': 'munin-plugins-core',
        }

        # iptables rules disable for now, since we need root
        # for ip in config.get('ip_addresses', []):
        #     plugins['ip_{}'.format(ip)] = {
        #         'executable': 'ip_',
        #         'apt': 'munin-plugins-core',
        #     }

    return {
        'munin': {
            'plugins': plugins,
        },
    }
