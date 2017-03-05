#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Convert log data to short / long span csv file for visualization
"""

import argparse
import datetime
from logging import getLogger
from logging import StreamHandler
from logging import INFO
import os

import numpy as np
import pandas as pd


# setup logger
logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(INFO)
logger.addHandler(handler)
logger.setLevel(INFO)


def get_args():
    """Get command line arguments"""
    parser = argparse.ArgumentParser(description="Convert to CSV for visualization")
    parser.add_argument("logdata", type=str, help="Path to log data csv file")
    parser.add_argument("--output-dir", "-o", type=str, default="data",
                        help="Path to output directory (default: data)")
    parser.add_argument("--days", "-d", type=int, default=30,
                        help="Number of days used for short term data CSV" +\
                             "(default: 30)")
    args = parser.parse_args()
    return args


def load_log_csv(log_path):
    """Load log csv file"""
    df = pd.read_csv(log_path, index_col=0,
                     dtype={"remote_user": str})
    return df


def preprocess(df):
    """Common preprocessing for short and long span data"""

    # devide 'request' column
    df['method'] = df['request'].str.split().str.get(0)
    df['url'] = df['request'].str.split().str.get(1)
    df['protocol'] = df['request'].str.split().str.get(2)

    # use only normal request
    df = df[(df['method'] == 'GET') & (df['status'] == 200)]

    # ignore static files 
    # NOTE: This implementation assumes that urls of all articles end with "/".
    #       If you use different url rule, please modify this line.
    df = df[(df['url'].str.startswith('/')) & (df['url'].str.endswith('/'))]

    # use only necessary columns
    df = df[['local_time', 'url']].copy()

    # use local time as index
    df.index = pd.to_datetime(df["local_time"])

    return df


def convert_for_short_span_csv(df, span_days):
    """Convert data frame for short span CSV file"""

    # add day of the week info
    weekday_names = "Sun,Mon,Tue,Wed,Thu,Fri,Sat".split(',')
    df_short = df[['url']].copy()
    df_short['day_of_week'] = [weekday_names[i] for i in df_short.index.weekday]

    # use the recent N days data (N: span_days)
    today = datetime.date.today()
    span = datetime.timedelta(span_days)
    date_from = (today - span).strftime("%Y%m%d")
    df_short = df_short[date_from:]

    return df_short


def convert_for_long_span_csv(df):
    """Convert data frame for long span CSV file"""
    df_long = df[['url']].copy()

    # week start date
    ws = df_long.index - df_long.index.weekday.astype('timedelta64[D]')
    df_long['week_start'] = ws.strftime('%Y-%m-%d')

    # dummy column for counting
    df_long['count'] = 1

    # group by week and url
    df_long = df_long.groupby(['week_start', 'url']).count()

    return df_long


def main():
    """Main"""
    args = get_args()
    logger.info("Load csv file ({})".format(args.logdata))
    df = load_log_csv(args.logdata)

    logger.info("Preprocessing")
    df = preprocess(df)

    logger.info("Preparing short span csv file")
    df_short = convert_for_short_span_csv(df, args.days)

    logger.info("Preparing long span csv file")
    df_long = convert_for_long_span_csv(df)

    logger.info("Save to csv files")
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    df_short.to_csv(os.path.join(args.output_dir, 'short.csv'))
    df_long.to_csv(os.path.join(args.output_dir, 'long.csv'))

    logger.info("Done.")


if __name__ == "__main__":
    main()
