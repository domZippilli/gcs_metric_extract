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
from datetime import datetime
from typing import Dict, List

import time

from google.cloud import monitoring_v3

from gcs_metric_extract.output import simple_latest_to_stdout

####################
# PUBLIC FUNCTIONS #
####################


def default_command(OPTIONS,
                    project_ids: List[str],
                    metric_url: str,
                    resource_label: str,
                    metric_label: str,
                    lookback_seconds: int = 660,
                    max_points: int = 1) -> None:
    """Most metrics in GCS have a similar shape. Getting the latest metrics is
    very boilerplate. Use this function to add support for a simple report of
    a metric with one resource and a few labels.

    Args:
        OPTIONS (Dict): Command line options like output format.
        project_ids (List[str]): The projects to query.
        metric_url (str): The metric to query.
        resource_label (str): The resource label, e.g., "bucket_name"
        metric_label (str): The metric (group) label, e.g., "storage_class"
    """
    # First, authenticate and get a monitoring client session.
    client = monitoring_v3.MetricServiceClient()
    # Our results will go here.
    results = dict()
    for p in project_ids:
        results[p] = _last_n_for_project(p, client, metric_url, resource_label,
                                         metric_label, OPTIONS["LOOKBACK"],
                                         OPTIONS["POINTS"])
    simple_latest_to_stdout(OPTIONS["FORMAT"], results)


#####################
# PRIVATE FUNCTIONS #
#####################


def _last_n_for_project(project_id: str,
                        client: monitoring_v3.MetricServiceClient,
                        metric_url: str, resource_label: str,
                        metric_labels: List[str], lookback_seconds: int,
                        max_points: int) -> Dict[str, Dict]:
    """Get latest metric values for the project.

    Args:
        project_id (str): The project
        client (monitoring_v3.MetricServiceClient): An initialized client.
        metric_url (str): The URL/type of the metric.
        resource_label (str): The resource label to dereference the resource
            (e.g., "bucket_name").
        metric_labels (List[str]): _description_
        lookback_seconds (int): _description_
        max_points (int): _description_

    Returns:
        Dict[str, Dict]: _description_
    """
    project_name = f"projects/{project_id}"

    result = defaultdict(dict)
    # Compose the request for this metric, send it, and store the result in
    # memory.
    for total_bytes_metric in _get_time_series(
            client, project_name, metric_url,
            lookback_seconds=lookback_seconds):
        _report_last_N(total_bytes_metric,
                       resource_label,
                       metric_labels,
                       n=max_points,
                       report=result)

    # Parse the time series into a dictionary.
    return result


def _get_time_series(client, project_name, metric, lookback_seconds):
    """Generate time series results. Automatically paginates; each yield will
    be a page of results.

    Args:
        client (monitoring_v3.client): A Google Cloud Monitoring client.
        project_name (string): The name of the project to request the time
            series from.
        metric (string): The full name/type of the metric.
            e.g., storage.googleapis.com/storage/total_bytes.
        lookback_seconds (int, optional): How far back to look for the time
            series. Larger means more data. Defaults to 660.

    Yields:
        monitoring_v3.ListTimeSeriesResponse: A page of results for a list
            time series request.
    """
    interval = monitoring_v3.TimeInterval()
    now = time.time()
    seconds = int(now)
    nanos = int((now - seconds) * 10**9)
    interval = monitoring_v3.TimeInterval({
        "end_time": {
            "seconds": seconds,
            "nanos": nanos
        },
        "start_time": {
            "seconds": (seconds - lookback_seconds),
            "nanos": nanos
        },
    })

    # Compose the request for this metric, send it, and yield the result,
    # stored in memory.
    request_info = {
        "name": project_name,
        "filter": 'metric.type = "%s"' % metric,
        "interval": interval,
        "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
    }
    while True:
        result = client.list_time_series(request=request_info)
        yield result
        if not result.next_page_token:
            # we are at the last page.
            break
        # we have another page to get.
        request_info["next_page_token"] = result.next_page_token


# TODO: I think there's a better way, but I can't find it in this SDK.
metric_type_map = {2: "int64", 3: "double"}


def _get_metric_type(enum_value: int) -> str:
    if enum_value in metric_type_map.keys():
        return metric_type_map[enum_value]
    raise Exception("Unsupported metric value type.")


def _report_last_N(time_series_response,
                   resource_label: str,
                   metric_labels: List[str],
                   n=1,
                   report=defaultdict(dict)) -> defaultdict[dict]:
    """Produces a nested array report of the latest values of a time series
    metric. Suitable for reports of how many bytes are in a bucket now, or how
    many objects, etc.

    This supports time series with a single resource grouping, and a single
    metric grouping (e.g., bucket and storage class).

    Args:
        time_series_response (monitoring_v3.ListTimeSeriesResponse): A list
            time series response.
        resource_label (string): The resource label. For Cloud Storage buckets,
            this is "bucket_name", for example.
        metric_label (string): The metric label. For many Cloud Storage storage
            metrics, this is "storage_class", for example.
        n (string): The number of points to return, from the end of the list.
            Use 0 or less for all.
        report (defaultdict[dict], optional): An existing report to use. Useful
            for paginating results into one report. If not provided, a new
            report dictionary is created and returned.

    Returns:
        defaultdict[dict]: The report data.
    """
    for metric in time_series_response:
        # get the resource
        resource_grouping = metric.resource.labels[resource_label]
        # dereference the label values, e.g. bucket_name = myBucket
        metric_labels_deref = []
        for label in metric_labels:
            metric_labels_deref.append(metric.metric.labels[label])
        value_type = _get_metric_type(metric.value_type)
        # produce an array of the last N points, where point is endtime: value
        # TODO: This might be broken for pagination. Since the results come in
        # descending order by date, a new page may overwrite newer points.
        last_n_points = []
        for point in metric.points[:n]:
            value = getattr(point.value, value_type + "_value")
            end_epoch = point.interval.end_time.seconds
            end_datetime = str(datetime.utcfromtimestamp(int(end_epoch)))
            last_n_points.append({end_datetime: value})
        # store the data in the report
        report[resource_grouping][",".join(
            metric_labels_deref)] = last_n_points
    return report
