#!/usr/bin/env python3
# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from collections import defaultdict

import click

from gcs_metric_extract.cli import default_command
from gcs_metric_extract.output import sanitize_format

OPTIONS = defaultdict(bool)


@click.group
@click.option(
    "--format",
    help="Format of the output. Valid options are json, ldjson, and csv.")
@click.option("--lookback",
              help="(Optional) Number of seconds to look back in the query. "
              "Use to limit data sent. Default: 660",
              type=int,
              default=660)
@click.option(
    "--points",
    help="(Optional) Number of points to report back. Useful for getting a "
    "fixed number of points when your lookback may not always return the same "
    "number. Use -1 for all. Default: 1.",
    type=int,
    default=1)
def main(format: str, lookback: int, points: int):
    OPTIONS["FORMAT"] = sanitize_format(format)
    OPTIONS["LOOKBACK"] = lookback
    OPTIONS["POINTS"] = points


@main.command()
@click.argument("project_ids", nargs=-1)
def api_request_count(project_ids):
    metric_url = "storage.googleapis.com/api/request_count"
    resource_label = "bucket_name"
    metric_labels = ["method", "response_code"]
    return default_command(OPTIONS, project_ids, metric_url, resource_label,
                           metric_labels)


@main.command()
@click.argument("project_ids", nargs=-1)
def object_count(project_ids):
    metric_url = "storage.googleapis.com/storage/object_count"
    resource_label = "bucket_name"
    metric_labels = ["storage_class"]
    return default_command(OPTIONS, project_ids, metric_url, resource_label,
                           metric_labels)


@main.command()
@click.argument("project_ids", nargs=-1)
def total_byte_seconds(project_ids):
    metric_url = "storage.googleapis.com/storage/total_byte_seconds"
    resource_label = "bucket_name"
    metric_labels = ["storage_class"]
    return default_command(OPTIONS, project_ids, metric_url, resource_label,
                           metric_labels)


@main.command()
@click.argument("project_ids", nargs=-1)
def total_bytes(project_ids):
    metric_url = "storage.googleapis.com/storage/total_bytes"
    resource_label = "bucket_name"
    metric_labels = ["storage_class"]
    return default_command(OPTIONS, project_ids, metric_url, resource_label,
                           metric_labels)


if __name__ == '__main__':
    main()
