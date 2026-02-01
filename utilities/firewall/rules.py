# utilities/firewall/rules.py

def outbound_block_rule_name(app_name: str) -> str:
    return f"{app_name} - BLOCK OUTBOUND ALL"


def outbound_udp_block_rule_name(app_name: str) -> str:
    return f"{app_name} - BLOCK OUTBOUND UDP"


def inbound_block_rule_name(app_name: str) -> str:
    return f"{app_name} - BLOCK INBOUND"
