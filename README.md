# gcs_metric_extract

A prototype CLI for getting Google Cloud Storage metrics out of the Google Cloud Monitoring API.

**DISCLAIMER:** This code is offered as a proof-of-concept only. It should not be used unmodified in production. Your use of this code is at your own risk. See `LICENSE` for more information.

## Usage

The help output should be helpful:

```(shell)
$ gcs_metric_extract --help
Usage: gcs_metric_extract [OPTIONS] COMMAND [ARGS]...

Options:
  --format TEXT       Format of the output. Valid options are json, ldjson,
                      and csv.
  --lookback INTEGER  (Optional) Number of seconds to look back in the query.
                      Use to limit data sent. Default: 660
  --points INTEGER    (Optional) Number of points to report back. Useful for
                      getting a fixed number of points when your lookback may
                      not always return the same number. Use -1 for all.
                      Default: 1.
  --help              Show this message and exit.

Commands:
  api-request-count   Get the number of API calls made against a bucket.
  get-metric          Get any GCS metric.
  object-count        Get the number of objects in a bucket.
  total-byte-seconds  Get the number of byte-seconds used by a bucket.
  total-bytes         Get the number of bytes stored in a bucket.
```

As an example, here's how to get each bucket's bytes, grouped by storage class, 
in pretty JSON output, for the default project in your gcloud CLI settings:
```shell
gcs_metric_extract total-bytes $(gcloud config get project)
```

Resulting in:

```
{
  "myProject": {
    "artifacts.myProject.appspot.com": {
      "MULTI_REGIONAL": [
        {
          "2022-08-12 06:30:00": 38486280.0
        }
      ]
    },
    "myProject_cloudbuild": {
      "MULTI_REGIONAL": [
        {
          "2022-08-12 06:30:00": 32096.0
        }
      ]
    },
    "myBucket": {
      "REGIONAL": [
        {
          "2022-08-12 06:30:00": 8777.0
        }
      ]
    }
  }
}
```

Or, get a similar report of object counts, with line-delimited JSON, a line per project:
```shell
gcs_metric_extract --format ldjson object-count $(gcloud config get project)
```

Resulting in:

```
{"project": "myProject", "resource": "artifacts.myProject.appspot.com", "metric": "MULTI_REGIONAL", "values": [{"2022-08-12 06:45:00": 4}]}
{"project": "myProject", "resource": "myProject_cloudbuild", "metric": "MULTI_REGIONAL", "values": [{"2022-08-12 06:45:00": 1}]}
{"project": "myProject", "resource": "myBucket", "metric": "REGIONAL", "values": [{"2022-08-12 06:45:00": 5}]}
```

CSV is supported, too -- great for databases.

```shell
gcs_metric_extract --format csv total-bytes $(gcloud config get project)
```

Output is like:

```csv
project,resource,metric,end_time,value
myProject,artifacts.myProject.appspot.com,"MULTI_REGIONAL",2022-08-12 06:45:00,38486280.0
myProject,myProject_cloudbuild,"MULTI_REGIONAL",2022-08-12 06:45:00,32096.0
myProject,myBucket,"REGIONAL",2022-08-12 06:45:00,8777.0
```

Especially with the csv and ldjson formats, you might want to do larger queries than the default "snapshot" settings. Use `--lookback` and `--points` to control the query and output. 

For example, use a command like this to get all the API request and status delta counts in the last 2 hours:

```shell
gcs_metric_extract --format csv --lookback $((60*120)) --points -1 api-request-count $(gcloud config get project
```

Here's truncated output:

```
project,resource,metric,end_time,value
myProject,myBucket,"GetObjectMetadata,OK",2022-08-12 06:53:00,34
myProject,myBucket,"GetObjectMetadata,OK",2022-08-12 06:52:00,20
myProject,myBucket,"ListObjects,OK",2022-08-12 06:52:00,10
myProject,myBucket,"ListObjects,OK",2022-08-12 06:51:00,7
myProject,myBucket,"GetObjectMetadata,UNAUTHENTICATED",2022-08-12 06:54:00,1
myProject,myBucket,"GetObjectMetadata,UNAUTHENTICATED",2022-08-12 06:53:00,0
myProject,myBucket,"ListObjects,UNAUTHENTICATED",2022-08-12 06:53:00,1
myProject,myBucket,"ListObjects,UNAUTHENTICATED",2022-08-12 06:52:00,0
```

Finally, with a more involved command you can request any metric in a similar way. This hasn't been tested with every metric, so it may break, but most of them are similarly structured for GCS.

```shell
gcs_metric_extract --format csv --lookback $((60*120)) --points -1 get-metric storage.googleapis.com/api/request_count bucket_name "method,response_code" $(gcloud config get project)
```

The above gets the API request counts, similar to the `api-request-count` command.


## Requirements

This program is written using some Python 3.10 features, so Python 3.10 or greater is required.

## Installation

The easiest way to install this program is with Poetry.

To do this:

1) Install Poetry in your Python ^3.10 environment, if needed: `pip install poetry`.
2) Clone this repo to a local directory.
3) Run `poetry install`

## Copyright

Copyright 2022, Google LLC.

## License Summary (Apache 2.0) 
``` text
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```