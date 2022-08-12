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
import json

import click


def sanitize_format(format: str) -> str:
    if not format:
        return "json"
    elif format.lower() in ["json", "ldjson", "csv"]:
        return format.lower()
    else:
        raise click.BadParameter("Unsupported format: %s" % format)


def simple_latest_to_stdout(format, data):
    match format:
        case "ldjson":
            for project in data.keys():
                for resource in data[project].keys():
                    for metric in data[project][resource].keys():
                        click.echo(json.dumps({
                            "project": project,
                            "resource": resource,
                            "metric": metric,
                            "values": data[project][resource][metric],
                            }))
        case "csv":
            click.echo("project,resource,metric,end_time,value")
            for project in data.keys():
                for resource in data[project].keys():
                    for metric in data[project][resource].keys():
                        for point in data[project][resource][metric]:
                            # a quick sanity check
                            if len(point.keys()) > 1:
                                raise Exception("Internal error occurred. \
                                    Please file a GitHub issue with the stack \
                                    trace.")
                            end_datetime = list(point.keys())[0]
                            value = point[end_datetime]
                            click.echo('%s,%s,"%s",%s,%s' % (
                                project,
                                resource,
                                metric,
                                end_datetime,
                                value
                                ))
        case _:  # json
            click.echo(json.dumps(data, indent=2))
