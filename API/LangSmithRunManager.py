import uuid, requests
import datetime, os
from typing import Optional

class LangSmithRunManager:
    def post_run(
            self, data: dict, name: str, run_id: str, parent_run_id: Optional[str] = None
    ) -> None:
        _LANGSMITH_API_KEY = os.environ["LANGCHAIN_API_KEY"]
        project_name = "default"
        requests.post(
            "https://api.smith.langchain.com/runs",
            json={
                "id": run_id,
                "name": name,
                "run_type": "chain",
                "parent_run_id": parent_run_id,
                "inputs": data,
                "start_time": datetime.datetime.utcnow().isoformat(),
                "session_name": project_name,
            },
            headers={"x-api-key": _LANGSMITH_API_KEY},
        )

    def patch_run(
            self, run_id: str, output: Optional[dict] = None, error: Optional[str] = None
    ) -> None:
        _LANGSMITH_API_KEY = os.environ["LANGCHAIN_API_KEY"]
        project_name = "default"
        requests.patch(
            f"https://api.smith.langchain.com/runs/{run_id}",
            json={
                "error": error,
                "outputs": output,
                "end_time": datetime.datetime.utcnow().isoformat(),
            },
            headers={"x-api-key": _LANGSMITH_API_KEY},
        )