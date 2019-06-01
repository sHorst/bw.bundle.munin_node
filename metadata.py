@metadata_processor
def add_iptables_rules(metadata):
    metadata.setdefault('munin', {})

    munin_server = repo.get_node(metadata['munin'].get('server', ''))

    if munin_server.partial_metadata == {}:
        return metadata, RUN_ME_AGAIN

    munin_server_ips = []
    interfaces = [metadata.get('main_interface'), ]
    interfaces += metadata['munin'].get('additional_interfaces', [])

    for interface, interface_config in munin_server.partial_metadata.get('interfaces', {}).items():
        if interface not in interfaces and interface != munin_server.partial_metadata.get('main_interface'):
            continue

        munin_server_ips += interface_config.get('ip_addresses', [])
        munin_server_ips += interface_config.get('ipv6_addresses', [])

    metadata['munin']['server_ips'] = list(dict.fromkeys(munin_server_ips))

    if node.has_bundle("iptables"):
        for interface in interfaces:
            for ip in munin_server_ips:
                metadata += repo.libs.iptables.accept(). \
                    input(interface). \
                    state_new(). \
                    tcp(). \
                    source(ip). \
                    dest_port(metadata['munin'].get('port', 4949))

    return metadata, DONE


@metadata_processor
def add_munin_plugin_for_interfaces(metadata):
    metadata.setdefault('munin', {}).setdefault('plugins', {})

    for interface, config in metadata.get('interfaces', {}).items():
        metadata['munin']['plugins']['if_{}'.format(interface)] = {
            'executable': 'if_',
            'apt': 'munin-plugins-core',
        }
        metadata['munin']['plugins']['if_err_{}'.format(interface)] = {
            'executable': 'if_err_',
            'apt': 'munin-plugins-core',
        }

        # iptables rules disable for now, since we need root
        # for ip in config.get('ip_addresses', []):
        #     metadata['munin']['plugins']['ip_{}'.format(ip)] = {
        #         'executable': 'ip_',
        #         'apt': 'munin-plugins-core',
        #     }

    return metadata, DONE
