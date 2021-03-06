# cspell:ignore dpkg, getent, lineinfile, nxapi, nxos, rglob, ruamel, sysvinit
"""A test files updater.


NOTE: ansible-lint needs to be pathced locally for roundtrip to work
https://github.com/ansible/ansible-lint/issues/2112
"""

import logging
import ruamel.yaml
import re
from pathlib import Path
from typing import OrderedDict

from ansiblelint.yaml_utils import FormattedYAML
from ruamel.yaml import CommentedSeq
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.tokens import CommentToken
from ruamel.yaml.error import CommentMark

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

ACRONYMS = (
    ("Conf", "Configure"),
    ("ace", "ACE"),
    ("acl", "ACL"),
    ("af", "AF"),
    ("afi", "AFI"),
    ("bfd", "BFD"),
    ("bgp", "BGP"),
    ("bgp_af", "BGP_AF"),
    ("cli", "CLI"),
    ("conf", "configure"),
    ("config", "configuration"),
    ("ebgp", "EBGP"),
    ("eigrp", "EIGRP"),
    ("evpn", "EVPN"),
    ("fib", "FIB"),
    ("ge", "'ge'"),
    ("gt", "'gt'"),
    ("igmp", "IGMP"),
    ("ip", "IP"),
    ("l2", "layer 2"),
    ("l3", "layer 3"),
    ("le", "'le'"),
    ("lt", "'lt'"),
    ("mds", "MDS"),
    ("motd", "MOTD"),
    ("n3k", "N3K"),
    ("n5k", "N5K"),
    ("n7k", "N7K"),
    ("n9k", "N9K"),
    ("neq", "'neq'"),
    ("ntc", "NTC"),
    ("nv", "NV"),
    ("nx-api", "NX-API"),
    ("nxapi", "NX-API"),
    ("os", "OS"),
    ("ospf", "OSPF"),
    ("pim", "PIM"),
    ("rib", "RIB"),
    ("rtt", "RTT"),
    ("snmp", "SNMP"),
    ("ssh", "SSH"),
    ("svi", "SVI"),
    ("tacacs", "TACACS"),
    ("vdc", "VDC"),
    ("vlan", "VLAN"),
    ("vrf", "VRF"),
    ("vsan", "VSAN"),
    ("vtp", "VTP"),
)

FEATURES = (
    "analytics",
    "bash-shell",
    "bfd",
    "bgp",
    "container-tracker",
    "dhcp",
    "dot1x",
    "eigrp",
    "epbr",
    "evb",
    "evmed",
    "fabric",
    "grpc",
    "hsrp",
    "imp",
    "interface-vlan",
    "isis",
    "itd",
    "lacp",
    "ldap",
    "license",
    "lldp",
    "mpls",
    "msdp",
    "nat",
    "nbm",
    "netconf",
    "netflow",
    "ngmvpn",
    "ngoam",
    "ntp",
    "nv",
    "nxapi",
    "nxsdk",
    "ofm",
    "openflow",
    "ospf",
    "ospfv3",
    "password",
    "pbr",
    "pim",
    "pim6",
    "pnp",
    "port-security",
    "private-vlan",
    "ptp",
    "restconf",
    "rip",
    "scheduler",
    "scp-server",
    "sflow",
    "sftp-server",
    "signature-verification",
    "sla",
    "srv6",
    "ssh",
    "tacacs+",
    "telemetry",
    "telnet",
    "tunnel",
    "tunnel-encryption",
    "udld",
    "vn-segment-vlan-based",
    "vpc",
    "vrrp",
    "vrrpv3",
    "vtp",
)

BUILTINS = (
    "add_host",
    "apt",
    "apt_key",
    "apt_repository",
    "assemble",
    "assert",
    "async_status",
    "blockinfile",
    "command",
    "copy",
    "cron",
    "debconf",
    "debug",
    "dnf",
    "dpkg_selections",
    "expect",
    "fail",
    "fetch",
    "file",
    "find",
    "gather_facts",
    "get_url",
    "getent",
    "git",
    "group",
    "group_by",
    "hostname",
    "import_playbook",
    "import_role",
    "import_tasks",
    "include",
    "include_role",
    "include_tasks",
    "include_vars",
    "iptables",
    "known_hosts",
    "lineinfile",
    "meta",
    "package",
    "package_facts",
    "pause",
    "ping",
    "pip",
    "raw",
    "reboot",
    "replace",
    "rpm_key",
    "script",
    "service",
    "service_facts",
    "set_fact",
    "set_stats",
    "setup",
    "shell",
    "slurp",
    "stat",
    "subversion",
    "systemd",
    "sysvinit",
    "tempfile",
    "template",
    "unarchive",
    "uri",
    "user",
    "validate_argument_spec",
    "wait_for",
    "wait_for_connection",
    "yum",
    "yum_repository",
)


def change_key(task: CommentedMap, old: str, new: str) -> None:
    """Change a key in a task.

    :param task: The task to change
    :param old: The old key
    :param new: The new key
    """
    if old in task.ca.items:
        task.ca.items[new] = task.ca.items.pop(old)

    for _ in range(len(task)):
        key, value = task.popitem(False)
        task[new if old == key else key] = value


def update_include_cli(data: CommentedSeq) -> bool:
    """Update the include_cli task.

    :param data: The task list
    :return: Whether the include_cli task was updated
    """
    match = [idx for idx, item in enumerate(data) if item.get("include") == "cli.yaml"]
    if not match:
        return False

    name = "Include the CLI tasks"
    for entry in match:
        data[entry]["name"] = name
        data[entry].move_to_end("name", last=False)
        change_key(data[entry], "include", "ansible.builtin.include_tasks")
    return True


def update_include_nxapi(data: CommentedSeq) -> bool:
    """Update the include_nxapi task.

    :param data: The task list
    :return: Whether the include_nxapi task was updated
    """
    match = [
        idx for idx, item in enumerate(data) if item.get("include") == "nxapi.yaml"
    ]
    if not match:
        return False

    name = "Include the NX-API tasks"
    for entry in match:
        data[entry]["name"] = name
        data[entry].move_to_end("name", last=False)
        change_key(data[entry], "include", "ansible.builtin.include_tasks")
    return True


def update_builtins(data: CommentedSeq) -> bool:
    """Update the builtins.

    :param data: The task list
    :return: Whether the builtins were updated
    """
    updated = False
    for task in data:
        for plugin in BUILTINS:
            if task.get(plugin):
                new_name = f"ansible.builtin.{plugin}"
                change_key(task, plugin, new_name)
                updated = True
    return updated


def capitalize_names(data: CommentedSeq) -> bool:
    """Capitalize the names of tasks.

    :param data: The task list
    :return: Whether the names were capitalized
    """
    updated = False
    for task in data:
        if task.get("name"):
            if task["name"].capitalize() != task["name"]:
                task["name"] = task["name"].capitalize()
                task.move_to_end("name", last=False)
                updated = True
    return updated


def update_include_test_case(list_of_tasks) -> bool:
    """Update the include_test_case task.

    :param list_of_tasks: The task list
    :return: Whether the include_test_case task was updated
    """
    match = [
        idx
        for idx, item in enumerate(list_of_tasks)
        if item.get("include", "").startswith("{{ test_case_to_run }}")
        or item.get("ansible.builtin.include_tasks", "").startswith(
            "{{ test_case_to_run }}"
        )
    ]
    if not match:
        return False
    for entry in match:
        change_key(list_of_tasks[entry], "include", "ansible.builtin.include_tasks")
        values = (
            list_of_tasks[entry]
            .get("ansible.builtin.include_tasks")
            .replace("{{ ", "{{")
            .replace(" }}", "}}")
        )
        first, var_pairs = values.split(" ", 1)
        list_of_tasks[entry]["ansible.builtin.include_tasks"] = first.replace(
            "{{", "{{ "
        ).replace("}}", " }}")
        list_of_tasks[entry]["vars"] = {}
        for var_pair in var_pairs.split(" "):
            key, value = var_pair.split("=")
            list_of_tasks[entry]["vars"][key] = value.replace("{{", "{{ ").replace(
                "}}", " }}"
            )

    return True


def undo_set_fact_equal(list_of_tasks) -> bool:
    """Undo the debug: msg=equal task.

    :param list_of_tasks: The task list
    :return: Whether the debug: msg=equal task was undone
    """
    match = []
    for idx, task in enumerate(list_of_tasks):
        if task.get("set_fact"):
            if not isinstance(task["set_fact"], str):
                continue
            match.append(idx)

    if not match:
        return False
    ct = CommentToken("\n\n", CommentMark(0), None)

    for entry in match:
        clean_value = (
            list_of_tasks[entry]["set_fact"]
            .replace("{{ ", "{{")
            .replace(" }}", "}}")
            .replace(" | ", "|")
        )
        clean_values = clean_value.split()
        list_of_tasks[entry]["set_fact"] = CommentedMap()

        last_key = ""
        error = False
        for clean_value in clean_values:
            new_value = None
            key, value = clean_value.split("=", maxsplit=1)
            # might be a number
            if value.strip("'").strip('"') == value:
                try:
                    new_value = int(value)
                except ValueError:
                    try:
                        new_value = float(value)
                    except ValueError:
                        pass
            if new_value is None:
                if value.strip("'").strip('"') in [
                    "True",
                    "true",
                    "yes",
                    "Yes",
                ]:
                    new_value = True
                elif value.strip("'").strip('"') in [
                    "False",
                    "false",
                    "no",
                    "No",
                ]:
                    new_value = False
                else:
                    new_value = (
                        value.strip('"')
                        .strip("'")
                        .replace("{{", "{{ ")
                        .replace("}}", " }}")
                        .replace("|", " | ")
                    )
            list_of_tasks[entry]["set_fact"][key] = new_value
            last_key = key

        commented = False
        if "set_fact" in list_of_tasks[entry].ca.items:
            list_of_tasks[entry].ca.items.pop("set_fact")
            commented = True

        change_key(list_of_tasks[entry], "set_fact", "ansible.builtin.set_fact")

        if commented:
            list_of_tasks[entry]["ansible.builtin.set_fact"].ca.items[last_key] = [
                None,
                None,
                ct,
                None,
            ]

    return True


def undo_debug_equal(list_of_tasks) -> bool:
    """Undo the debug: msg=equal task.

    :param list_of_tasks: The task list
    :return: Whether the debug: msg=equal task was undone
    """
    match = []
    for idx, task in enumerate(list_of_tasks):
        if task.get("debug"):
            if not isinstance(task["debug"], str):
                continue
            match.append(idx)

    if not match:
        return False
    ct = CommentToken("\n\n", CommentMark(0), None)

    for entry in match:
        keyword, value = list_of_tasks[entry]["debug"].split("=", maxsplit=1)
        list_of_tasks[entry]["debug"] = CommentedMap()
        list_of_tasks[entry]["debug"][keyword] = value.strip('"').strip("'")

        debug_commented = False
        if "debug" in list_of_tasks[entry].ca.items:
            list_of_tasks[entry].ca.items.pop("debug")
            debug_commented = True

        change_key(list_of_tasks[entry], "debug", "ansible.builtin.debug")

        if debug_commented:
            list_of_tasks[entry]["ansible.builtin.debug"].ca.items[keyword] = [
                None,
                None,
                ct,
                None,
            ]

    return True


def update_acronyms(list_of_tasks) -> bool:
    """Replace acronyms."""
    updated = False
    for idx, task in enumerate(list_of_tasks):
        if "name" not in task:
            continue
        for comb in ACRONYMS:
            find, replace = comb

            task["name"], subs = re.subn(
                f"(^|\\s){find}($|\\s)", f"\\1{replace}\\2", task["name"]
            )
            if subs:
                updated = True
    return updated


def update_features(list_of_tasks) -> bool:
    """Special case for NXOS features."""
    updated = False
    for idx, task in enumerate(list_of_tasks):
        if "name" not in task:
            continue
        for find in FEATURES:
            task["name"], subs = re.subn(
                f"(^|\\s)feature {find}($|\\s)",
                f"\\1'feature {find}'\\2",
                task["name"],
                flags=re.IGNORECASE,
            )
            if subs:
                updated = True
    return updated


def set_style(doc: CommentedSeq, flow: bool) -> None:
    """Set the style of a YAML document.

    :param d: The document to set the style on
    :param flow: Whether to use flow style or not
    """
    if isinstance(doc, CommentedMap):
        if flow:
            doc.fa.set_flow_style()
        else:
            doc.fa.set_block_style()
        for key in doc:
            set_style(doc[key], flow)
    elif isinstance(doc, CommentedSeq):
        if flow:
            doc.fa.set_flow_style()
        else:
            doc.fa.set_block_style()
        for item in doc:
            set_style(item, flow)


def update_list_of_tasks(list_of_tasks) -> bool:
    """Update the list of tasks.

    :param list_of_tasks: The list of tasks
    :return: Whether the list of tasks was updated
    """
    updated = []
    # updated.append(update_include_cli(list_of_tasks))
    # updated.append(update_include_nxapi(list_of_tasks))
    # updated.append(update_builtins(list_of_tasks))
    # updated.append(capitalize_names(list_of_tasks))
    # updated.append(update_include_test_case(list_of_tasks))
    # updated.append(undo_debug_equal(list_of_tasks))
    # updated.append(undo_set_fact_equal(list_of_tasks))
    # updated.append(update_acronyms(list_of_tasks))
    # updated.append(update_features(list_of_tasks))
    return True  # any(updated)


def update(file_path: Path) -> None:
    """Update the tasks in a file.

    :param file_path: The path to the file
    """

    yaml = FormattedYAML()
    yaml.preserve_quotes = True

    data = yaml.load(file_path)
    if not isinstance(data, CommentedSeq):
        LOGGER.info("Skipping: %s", file_path)
        return

    LOGGER.info("Updating: %s", file_path)
    updated = update_list_of_tasks(data)

    for block_part in ["block", "rescue", "always"]:
        ids = [idx for idx, entry in enumerate(data) if entry.get(block_part)]
        for block_id in ids:
            # Remove blank line comments from the block
            updates = update_list_of_tasks(data[block_id][block_part])
            if updates:
                updated = True

    if not updated:
        LOGGER.info("No updates: %s", file_path)
        return

    set_style(data, flow=False)

    LOGGER.info("Writing: %s", file_path)

    with file_path.open(mode="w") as fh:
        yaml.dump(data, fh)


def main():
    """Main entry point."""
    path = Path(
        "../collection_development/collections/ansible_collections/cisco/nxos/tests/integration"
    )
    for file_path in sorted(path.rglob("*")):
        if file_path.suffix in [".yaml", ".yml"]:
            update(file_path)


if __name__ == "__main__":
    main()
