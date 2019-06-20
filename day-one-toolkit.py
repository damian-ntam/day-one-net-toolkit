from nornir import InitNornir
from nornir.plugins.tasks.networking import napalm_get
from nornir.plugins.functions.text import print_result
from nornir.plugins.tasks.files import write_file
from nornir.plugins.tasks.networking import napalm_cli
import json
import requests
import pathlib
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import datetime as dt
from timeit import default_timer as timer
import pandas as pd
import yaml
from pandas.io.json import json_normalize

# Disable urllib3 warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Functions


def collect_filters(task, filter, dir=False):
    '''
    TODO: Insert doco
    :param task:
    :param filter:
    :param dir:
    :return:
    '''
    # Assign facts directory to variable
    fact_dir = "facts"
    # Assign hostname directory to a variable
    host_dir = task.host.name
    # Assign the destination directory to a variable. i.e facts/hostname/
    entry_dir = fact_dir + '/' + host_dir
    # If Else to handle creating directories. Default is to create them
    if dir is False:
        # Create facts directory
        pathlib.Path(fact_dir).mkdir(exist_ok=True)
        # Create entry directory
        pathlib.Path(entry_dir).mkdir(exist_ok=True)
    # Try/except block to catch exceptions, such as NotImplementedError
    try:
        # Gather facts using napalm_get and assign to a variable
        facts_result = task.run(task=napalm_get, getters=[filter])
        # Write the results to a JSON, using the convention <filter_name>.json
        task.run(
            task=write_file,
            content=json.dumps(facts_result[0].result[filter], indent=2),
            # filename=f"facts/" + str(host_dir) + "/" + str(filter) + ".json",
            filename=f"" + str(entry_dir) + "/" + str(filter) + ".json",
        )
    # Handle NAPALM Not Implemented Error exceptions
    except NotImplementedError:
        return 'Filter Not Implemented'
    except AttributeError:
        return "AttributeError: Driver has no attribute"


def collect_config(task, filter, dir=False):
    '''
    TODO: Insert doco
    :param task:
    :param filter:
    :param dir:
    :return:
    '''
    # Assign configs directory to variable
    config_dir = "configs"
    # Assign hostname directory to a variable
    host_dir = task.host.name
    # Assign the destination directory to a variable. i.e configs/hostname/
    entry_dir = config_dir + '/' + host_dir
    # If Else to handle creating directories. Default is to create them
    if dir is False:
        # Create facts directory
        pathlib.Path(config_dir).mkdir(exist_ok=True)
        # Create entry directory
        pathlib.Path(entry_dir).mkdir(exist_ok=True)
    # Try/except block to catch exceptions, such as NotImplementedError
    try:
        # Gather facts using napalm_get and assign to a variable
        config_result = task.run(task=napalm_get, getters=["config"])
        task.run(
            task=write_file,
            content=config_result.result["config"][filter],
            filename=f"" + str(entry_dir) + "/" + str(filter) + ".txt",
        )
    # Handle NAPALM Not Implemented Error exceptions
    except NotImplementedError:
        print("NAPALM get filter not implemented " + str(filter))


# https://napalm.readthedocs.io/en/latest/support/


def filter_collector():
    '''
    This function performs a collection of supported filters based on
    the official NAPALM supported filter list:
    https://napalm.readthedocs.io/en/latest/support/

    It has been written in a way whereby one simply updates the appropriate <os>_filters
    list to add or remove supported filters

    For now, all filters are stored in the facts/ directory using the following convention:
    <hostname>_<filter_name>.json


    :return:
    '''
    '''
    The following block of code is used to generate a log file in a directory.
    These log files will indicate the success/failure of filter collector for retrospective analysis.
    '''
    # Capture time
    cur_time = dt.datetime.now()
    # Cleanup time, so that the format is clean for the output file 2016-12-01-13-04-59
    fmt_time = cur_time.strftime('%Y-%m-%d-%H-%M-%S')
    # Set log directory variable
    log_dir = "logs"
    # Create log directory if it doesn't exist.
    pathlib.Path(log_dir).mkdir(exist_ok=True)
    # Create log file name, with timestamp in the name
    filename = (str('DISCOVERY-LOG') + '-' + fmt_time + '.txt')
    # Join the log file name and log directory together into a variable
    log_file_path = log_dir + "/" + filename
    # Create the log file
    log_file = open(log_file_path, 'w')
    # Start of logging output
    print('STARTING DISCOVERY: ' + str(fmt_time))
    log_file.write('STARTING DISCOVERY: ' + str(fmt_time) + '\n\n')
    '''
    Initialise two counters, so that success and failure can be counted
    and incremented as the filters are collected.
    '''
    # Success Counter
    success_count = 0
    # Fail Counter
    fail_count = 0
    # Initialize Nornir and define the inventory variables.
    nr = InitNornir(
        inventory={
            "options": {
                "host_file": "inventory/hosts.yaml",
                "group_file": "inventory/groups.yaml",
                "defaults_file": "inventory/defaults.yaml",
            }
        }
    )
    # The following block of lists are the supported filters per OS.
    # ios supported filters
    # environment and network instances removed.
    # ios_filters = ["arp_table", "bgp_neighbors", "bgp_neighbors_detail", "environment", "facts", "interfaces",
    #                "interfaces_counters", "interfaces_ip", "ipv6_neighbors_table", "lldp_neighbors",
    #                "lldp_neighbors_detail", "mac_address_table", "network_instances", "ntp_peers", "ntp_servers",
    #                "ntp_stats", "optics", "snmp_information", "users"]
    ios_filters = ["arp_table", "bgp_neighbors", "bgp_neighbors_detail", "facts", "interfaces",
                   "interfaces_counters", "interfaces_ip", "ipv6_neighbors_table", "lldp_neighbors",
                   "lldp_neighbors_detail", "mac_address_table", "ntp_peers", "ntp_servers",
                   "ntp_stats", "optics", "snmp_information", "users"]
    # junos supported filters
    # junos_filters = ["arp_table", "bgp_config", "bgp_neighbors", "bgp_neighbors_detail", "environment",
    #                  "facts", "interfaces", "interfaces_counters", "interfaces_ip", "ipv6_neighbors_table",
    #                  "lldp_neighbors", "lldp_neighbors_detail", "mac_address_table", "network_instances", "ntp_peers",
    #                  "ntp_servers", "ntp_stats", "optics", "snmp_information", "users"]
    junos_filters = ["arp_table", "bgp_config", "bgp_neighbors", "bgp_neighbors_detail",
                     "facts", "interfaces", "interfaces_counters", "interfaces_ip", "ipv6_neighbors_table",
                     "lldp_neighbors", "lldp_neighbors_detail", "network_instances", "ntp_peers",
                     "ntp_servers", "ntp_stats", "optics", "snmp_information", "users"]
    # eos supported filters
    eos_filters = ["arp_table", "bgp_config", "bgp_neighbors", "bgp_neighbors_detail",  "environment", "facts",
                   "interfaces", "interfaces_counters", "interfaces_ip", "lldp_neighbors", "lldp_neighbors_detail",
                   "mac_address_table", "network_instances", "ntp_servers", "ntp_stats", "optics", "snmp_information",
                   "users"]
    # nxos supported filters
    nxos_filters = ["arp_table", "bgp_neighbors", "facts", "interfaces", "interfaces_ip", "lldp_neighbors",
                    "lldp_neighbors_detail", "mac_address_table", "ntp_peers", "ntp_servers", "ntp_stats",
                    "snmp_information", "users"]
    # There is a bug with LLDP and interfaces IP with my NX-OS
    # nxos_filters = ["arp_table", "bgp_neighbors", "facts", "interfaces","mac_address_table",
    #                 "ntp_peers", "ntp_servers", "ntp_stats", "snmp_information", "users", "interfaces_ip" ]
    # iosxr supported filters
    iosxr_filters = ["arp_table", "bgp_config", "bgp_neighbors", "bgp_neighbors_detail", "environment",
                     "facts", "interfaces", "interfaces_counters", "interfaces_ip", "lldp_neighbors",
                     "lldp_neighbors_detail", "mac_address_table", "ntp_peers", "ntp_servers", "ntp_stats",
                     "snmp_information", "users"]
    '''
    The following block of code assigns a filter based on platform to a variable. This variable is used later on to
    apply logic in for loops
    '''
    ios_devices = nr.filter(platform="ios")
    junos_devices = nr.filter(platform="junos")
    eos_devices = nr.filter(platform="eos")
    nxos_devices = nr.filter(platform="nxos")
    iosxr_devices = nr.filter(platform="iosxr")
    '''
    The following block is the main component of the program. Each OS collects the running config, all supported
    filters and the startup/candidate config based on the OS.
    Each OS block is as uniform as possible.
    '''
    # IOS Platform Block
    for host in ios_devices.inventory.hosts.items():
        # Starting processing of a host
        print("** Start Processing Host: " + str(host))
        log_file.write('** Start Processing Host: ' + str(host) + '\n')
        # Start collecting the running config
        print('Processing Running Config ... ')
        log_file.write("Processing Running Config ... " + '\n')
        # Execute the collect_config function
        run_config = nr.run(task=collect_config, filter="running", num_workers=1)
        # Conditional block to record success/fail count of the job
        if run_config.failed is False:
            log_file.write("SUCCESS : Running Config" + '\n')
            print("SUCCESS : Running Config")
            success_count += 1
        else:
            log_file.write("FAILED : Running Config" + '\n')
            print("FAILED : Running Config")
            fail_count += 1
        # Start collecting the running config
        print("PROCESSING STARTUP CONFIG ... ")
        log_file.write("PROCESSING STARTUP CONFIG ... " + '\n')
        # Execute the collect_config function
        start_config = nr.run(task=collect_config, filter="startup", num_workers=1)
        # Conditional block to record success/fail count of the job
        if start_config.failed is False:
            log_file.write("SUCCESS : STARTUP CONFIG" + '\n')
            print("SUCCESS : STARTUP CONFIG")
            success_count += 1
        else:
            log_file.write("FAILED : STARTUP CONFIG" + '\n')
            print("FAILED : STARTUP CONFIG")
            fail_count += 1
        # For block to collect all supported filters
        for entry in ios_filters:
            # Start processing filters
            print("PROCESSING FILTER: " + str(entry))
            log_file.write("PROCESSING FILTER: " + str(entry) + '\n')
            # Execuute collect_filters function
            filters = nr.run(task=collect_filters, filter=entry, num_workers=1)
            # Conditional block to record success/fail count of the job
            if filters.failed is False:
                log_file.write("SUCCESS : " + str(entry) + '\n')
                print("SUCCESS : " + str(entry))
                success_count += 1
            else:
                log_file.write("FAILED : " + str(entry) + '\n')
                print("FAILED : " + str(entry))
                fail_count += 1
        # Ending processing of host
        print("** End Processing Host: " + str(host))
        log_file.write('** End Processing Host: ' + str(host) + '\n\n')
    # EOS Platform Block
    for host in eos_devices.inventory.hosts.items():
        # Starting processing of a host
        print("** Start Processing Host: " + str(host))
        log_file.write('** Start Processing Host: ' + str(host) + '\n')
        # Start collecting the running config
        print('Processing Running Config ... ')
        log_file.write("Processing Running Config ... " + '\n')
        # Execute the collect_config function
        run_config = nr.run(task=collect_config, filter="running", num_workers=1)
        # Conditional block to record success/fail count of the job
        if run_config.failed is False:
            log_file.write("SUCCESS : Running Config" + '\n')
            print("SUCCESS : Running Config")
            success_count += 1
        else:
            log_file.write("FAILED : Running Config" + '\n')
            print("FAILED : Running Config")
            fail_count += 1
        # Start collecting the running config
        print("PROCESSING STARTUP CONFIG ... ")
        log_file.write("PROCESSING STARTUP CONFIG ... " + '\n')
        # Execute the collect_config function
        start_config = nr.run(task=collect_config, filter="startup", num_workers=1)
        # Conditional block to record success/fail count of the job
        if start_config.failed is False:
            log_file.write("SUCCESS : STARTUP CONFIG" + '\n')
            print("SUCCESS : STARTUP CONFIG")
            success_count += 1
        else:
            log_file.write("FAILED : STARTUP CONFIG" + '\n')
            print("FAILED : STARTUP CONFIG")
            fail_count += 1
        # For block to collect all supported filters
        for entry in eos_filters:
            # Start processing filters
            print("PROCESSING FILTER: " + str(entry))
            log_file.write("PROCESSING FILTER: " + str(entry) + '\n')
            # Execuute collect_filters function
            filters = nr.run(task=collect_filters, filter=entry, num_workers=1)
            # Conditional block to record success/fail count of the job
            if filters.failed is False:
                log_file.write("SUCCESS : " + str(entry) + '\n')
                print("SUCCESS : " + str(entry))
                success_count += 1
            else:
                log_file.write("FAILED : " + str(entry) + '\n')
                print("FAILED : " + str(entry))
                fail_count += 1
        # Ending processing of host
        print("** End Processing Host: " + str(host))
        log_file.write('** End Processing Host: ' + str(host) + '\n\n')
    # NX-OS Platform Block
    for host in nxos_devices.inventory.hosts.items():
        # Starting processing of a host
        print("** Start Processing Host: " + str(host))
        log_file.write('** Start Processing Host: ' + str(host) + '\n')
        # Start collecting the running config
        print('Processing Running Config ... ')
        log_file.write("Processing Running Config ... " + '\n')
        # Execute the collect_config function
        run_config = nr.run(task=collect_config, filter="running", num_workers=1)
        # Conditional block to record success/fail count of the job
        if run_config.failed is False:
            log_file.write("SUCCESS : Running Config" + '\n')
            print("SUCCESS : Running Config")
            success_count += 1
        else:
            log_file.write("FAILED : Running Config" + '\n')
            print("FAILED : Running Config")
            fail_count += 1
        # Start collecting the running config
        print("PROCESSING STARTUP CONFIG ... ")
        log_file.write("PROCESSING STARTUP CONFIG ... " + '\n')
        # Execute the collect_config function
        start_config = nr.run(task=collect_config, filter="startup", num_workers=1)
        # Conditional block to record success/fail count of the job
        if start_config.failed is False:
            log_file.write("SUCCESS : STARTUP CONFIG" + '\n')
            print("SUCCESS : STARTUP CONFIG")
            success_count += 1
        else:
            log_file.write("FAILED : STARTUP CONFIG" + '\n')
            print("FAILED : STARTUP CONFIG")
            fail_count += 1
        # For block to collect all supported filters
        for entry in nxos_filters:
            # Start processing filters
            print("PROCESSING FILTER: " + str(entry))
            log_file.write("PROCESSING FILTER: " + str(entry) + '\n')
            # Execuute collect_filters function
            filters = nr.run(task=collect_filters, filter=entry, num_workers=1)
            # Conditional block to record success/fail count of the job
            if filters.failed is False:
                log_file.write("SUCCESS : " + str(entry) + '\n')
                print("SUCCESS : " + str(entry))
                success_count += 1
            else:
                log_file.write("FAILED : " + str(entry) + '\n')
                print("FAILED : " + str(entry))
                fail_count += 1
        # Ending processing of host
        print("** End Processing Host: " + str(host) + '\n')
        log_file.write('** End Processing Host: ' + str(host) + '\n\n')
    # JUNOS Platform Block
    for host in junos_devices.inventory.hosts.items():
        # Starting processing of a host
        print("** Start Processing Host: " + str(host))
        log_file.write('** Start Processing Host: ' + str(host) + '\n')
        # Start collecting the running config
        print('Processing Running Config ... ')
        log_file.write("Processing Running Config ... " + '\n')
        # Execute the collect_config function
        run_config = nr.run(task=collect_config, filter="running", num_workers=1)
        # Conditional block to record success/fail count of the job
        if run_config.failed is False:
            log_file.write("SUCCESS : Running Config" + '\n')
            print("SUCCESS : Running Config")
            success_count += 1
        else:
            log_file.write("FAILED : Running Config" + '\n')
            print("FAILED : Running Config")
            fail_count += 1
        # Start collecting the running config
        print("Processing Candidate Config ... ")
        log_file.write("Processing Candidate Config ... " + '\n')
        # Execute the collect_config function
        start_config = nr.run(task=collect_config, filter="candidate", num_workers=1)
        # Conditional block to record success/fail count of the job
        if start_config.failed is False:
            log_file.write("SUCCESS : Candidate Config" + '\n')
            print("SUCCESS : Candidate Config")
            success_count += 1
        else:
            log_file.write("FAILED : CANDIDATE CONFIG" + '\n')
            print("FAILED : CANDIDATE CONFIG")
            fail_count += 1
        # For block to collect all supported filters
        for entry in junos_filters:
            # Start processing filters
            print("PROCESSING FILTER: " + str(entry))
            log_file.write("PROCESSING FILTER: " + str(entry) + '\n')
            # Execuute collect_filters function
            filters = nr.run(task=collect_filters, filter=entry, num_workers=1)
            # Conditional block to record success/fail count of the job
            if filters.failed is False:
                log_file.write("SUCCESS : " + str(entry) + '\n')
                print("SUCCESS : " + str(entry))
                success_count += 1
            else:
                log_file.write("FAILED : " + str(entry) + '\n')
                print("FAILED : " + str(entry))
                fail_count += 1
        # Ending processing of host
        print("** End Processing Host: " + str(host) + '\n')
        log_file.write('** End Processing Host: ' + str(host) + '\n\n')
    # IOS-XR Platform Block
    for host in iosxr_devices.inventory.hosts.items():
        # Starting processing of a host
        print("** Start Processing Host: " + str(host))
        log_file.write('** Start Processing Host: ' + str(host) + '\n')
        # Start collecting the running config
        print('Processing Running Config ... ')
        log_file.write("Processing Running Config ... " + '\n')
        # Execute the collect_config function
        run_config = nr.run(task=collect_config, filter="running", num_workers=1)
        # Conditional block to record success/fail count of the job
        if run_config.failed is False:
            log_file.write("SUCCESS : Running Config" + '\n')
            print("SUCCESS : Running Config")
            success_count += 1
        else:
            log_file.write("FAILED : Running Config" + '\n')
            print("FAILED : Running Config")
            fail_count += 1
        # Start collecting the running config
        print("PROCESSING STARTUP CONFIG ... ")
        log_file.write("PROCESSING STARTUP CONFIG ... " + '\n')
        # Execute the collect_config function
        start_config = nr.run(task=collect_config, filter="startup", num_workers=1)
        # Conditional block to record success/fail count of the job
        if start_config.failed is False:
            log_file.write("SUCCESS : STARTUP CONFIG" + '\n')
            print("SUCCESS : STARTUP CONFIG")
            success_count += 1
        else:
            log_file.write("FAILED : STARTUP CONFIG" + '\n')
            print("FAILED : STARTUP CONFIG")
            fail_count += 1
        # For block to collect all supported filters
        for entry in iosxr_filters:
            # Start processing filters
            print("PROCESSING FILTER: " + str(entry))
            log_file.write("PROCESSING FILTER: " + str(entry) + '\n')
            # Execuute collect_filters function
            filters = nr.run(task=collect_filters, filter=entry, num_workers=1)
            # Conditional block to record success/fail count of the job
            if filters.failed is False:
                log_file.write("SUCCESS : " + str(entry) + '\n')
                print("SUCCESS : " + str(entry))
                success_count += 1
            else:
                log_file.write("FAILED : " + str(entry) + '\n')
                print("FAILED : " + str(entry))
                fail_count += 1
        # Ending processing of host
        print("** End Processing Host: " + str(host))
        log_file.write('** End Processing Host: ' + str(host) + '\n\n')
    # Add the two variables together to get a total count into a variable
    total_count = success_count + fail_count
    print("SUMMARY" + '\n')
    log_file.write("SUMMARY" + '\n\n')
    print("SUCCESS COUNT : " + str(success_count))
    log_file.write("SUCCESS COUNT : " + str(success_count) + '\n')
    print("FAILURE COUNT : " + str(fail_count))
    log_file.write("FAILURE COUNT : " + str(fail_count) + '\n')
    print("TOTAL COUNT : " + str(total_count))
    log_file.write("TOTAL COUNT : " + str(total_count) + '\n')
    log_file.close()


# Run Functions
filter_collector()