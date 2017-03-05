#!/usr/bin/env python
"""
NGINX Log Parser

Note: This script supports the default log format in NGINX.
"""


import argparse
import datetime
from logging import getLogger
from logging import StreamHandler
from logging import INFO
import shlex

import pandas as pd


COLUMN_NAMES = "remote_addr,remote_user,local_time,request,status," +\
               "body_types_sent,http_referer,http_user_agent,gzip_ratio"


# setup logger
logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(INFO)
logger.addHandler(handler)
logger.setLevel(INFO)


def parse_record(record):
    """Parse one record"""
    tmp = shlex.split(record.replace('[', '"').replace(']', '"'))

    # devide into each field
    remote_addr = tmp[0]
    remote_user = tmp[2] if tmp[2] is not "-" else None
    timestamp = tmp[3].split()[0]
    if " " in timestamp:
        fmt = "%d/%b/%Y:%H:%M:%S %z" # with timezone info
    else:
        fmt = "%d/%b/%Y:%H:%M:%S"
    local_time = datetime.datetime.strptime(timestamp, fmt)

    # convert data type
    request = tmp[4]
    status = int(tmp[5])
    body_types_sent = int(tmp[6])
    http_referer = tmp[7] if tmp[7] is not "-" else None
    http_user_agent = tmp[8]
    gzip_ratio = tmp[9] if tmp[9] is not "-" else None

    data = (remote_addr, remote_user, local_time, request, status,
            body_types_sent, http_referer, http_user_agent, gzip_ratio)
    return data


def parse_log(file_path):
    """Parse log file"""
    data = []
    for record in open(file_path):
        try:
            d = parse_record(record)
            data.append(d)
        except:
            logger.warning("Error occured while reading the record" +\
                           " (Ignored):\n {}".format(record))
    return data


def get_args():
    """Get command line arguments"""
    parser = argparse.ArgumentParser(description="NGINX Log Parser")
    parser.add_argument("log", type=str, help="Log file")
    parser.add_argument("--output", "-o", type=str, default="log.csv",
                        help="Path to output csv file (default: log.csv)")
    args = parser.parse_args()
    return args


def main():
    """Main"""
    args = get_args() 
    logger.info("Start parsing the log file: {}".format(args.log))
    data = parse_log(args.log)
    logger.info("Converted {} records".format(len(data)))

    logger.info("Save log data to csv file: {}".format(args.output))
    df = pd.DataFrame(data, columns=COLUMN_NAMES.split(","))
    df.to_csv(args.output)
    logger.info("Done.")


if __name__ == "__main__":
    main()
