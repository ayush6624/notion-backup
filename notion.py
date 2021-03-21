import os
import json
import time
import urllib
import urllib.request
from datetime import datetime

TZ = os.getenv("TZ", "Asia/Calcutta")
NOTION_API = os.getenv('NOTION_API', 'https://www.notion.so/api/v3')
NOTION_TOKEN_V2 = os.getenv("NOTION_TOKEN_V2")
NOTION_SPACE_ID = os.getenv("NOTION_SPACE_ID")
IS_CI = os.getenv("CI", False)


def request(endpoint: str, params: object):
    req = urllib.request.Request(
        f'{NOTION_API}/{endpoint}',
        data=json.dumps(params).encode('utf8'),
        headers={
            'content-type': 'application/json',
            'cookie': f'token_v2={NOTION_TOKEN_V2}; '
        },
    )
    response = urllib.request.urlopen(req)
    return json.loads(response.read().decode('utf8'))


def export(format: str):
    ENQUEUE_TASK_PARAM = {
        "task": {
            "eventName": "exportSpace", "request": {
                "spaceId": NOTION_SPACE_ID,
                "exportOptions": {"exportType": format, "timeZone": TZ, "locale": "en"}
            }
        }
    }
    EXPORT_FILENAME = f'export_{format}_{datetime.now().date().__str__()}.zip'

    task_id = request('enqueueTask', ENQUEUE_TASK_PARAM).get('taskId')
    print(f'Enqueued task {task_id}')

    while True:
        time.sleep(4)
        tasks = request("getTasks", {"taskIds": [task_id]}).get('results')
        task = next(t for t in tasks if t.get('id') == task_id)
        if IS_CI == False:
            print(
                f'\rPages exported: {task.get("status").get("pagesExported")}', end="")

        if task.get('state') == 'success':
            print('Success from the API')
            break

    export_url = task.get('status').get('exportURL')
    print(f'\n {format} export created, downloading...')

    urllib.request.urlretrieve(
        export_url, EXPORT_FILENAME,
        reporthook=lambda c, bs, ts: print(
            f"\r{int(c * bs * 100 / ts)}%", end="")
    )
    print(f'\nDownload complete:')
    if IS_CI == False:
        print(EXPORT_FILENAME)


if __name__ == "__main__":
    export("html")
    export("markdown")
