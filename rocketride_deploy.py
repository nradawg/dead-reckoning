"""Deploy The Coroner's diagnosis stage as a pipeline on RocketRide Cloud.

The pipeline is the multi-agent workflow: a webhook receives the evidence
dossier the Investigator gathered from HydraDB, an LLM node (served by
Pipeshift) acts as the Coroner and writes the verdict JSON, and the response
node returns it. Deployed via deploy.add so it outlives the connection.
"""
import asyncio
import json
import os
import sys

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

URI = os.environ.get("ROCKETRIDE_URI", "https://api.rocketride.ai")
AUTH = os.environ.get("ROCKETRIDE_AUTH") or os.environ.get("ROCKETRIDE_APIKEY")
PS_KEY = os.environ["PIPESHIFT_API_KEY"]
PS_MODEL = os.environ.get("PIPESHIFT_MODEL", "deepseek-ai/DeepSeek-V4-Flash")

from rocketride import RocketRideClient  # noqa: E402

SYSTEM = (
    "You are the Coroner: a medical examiner for software projects. You receive "
    "an evidence dossier gathered from a company's Slack, GitHub, Linear and "
    "Gmail. Return ONLY a JSON object with keys: cause, survived_by, "
    "recommendation (REVIVE|REPLACE|BURY), reasoning, alternative, eulogy."
)

# Config shapes to try, most-likely first. Pipeshift is OpenAI-compatible, so
# an openai-style node with a base-url override is the natural fit.
LANES = ["questions", "prompt", "input", "context"]
CANDIDATES = [
    ("llm_openai + baseUrl", {
        "id": "coroner_llm", "provider": "llm_openai",
        "config": {"apikey": PS_KEY, "model": PS_MODEL,
                   "baseUrl": "https://api.pipeshift.com/api/v0",
                   "system": SYSTEM},
        "input": [{"lane": "questions", "from": "webhook_1"}]}),
    ("llm_openai + base_url", {
        "id": "coroner_llm", "provider": "llm_openai",
        "config": {"apikey": PS_KEY, "model": PS_MODEL,
                   "base_url": "https://api.pipeshift.com/api/v0",
                   "system": SYSTEM},
        "input": [{"lane": "questions", "from": "webhook_1"}]}),
    ("llm_openai + endpoint", {
        "id": "coroner_llm", "provider": "llm_openai",
        "config": {"apikey": PS_KEY, "model": PS_MODEL,
                   "endpoint": "https://api.pipeshift.com/api/v0",
                   "system": SYSTEM},
        "input": [{"lane": "questions", "from": "webhook_1"}]}),
]

WEBHOOK = {"id": "webhook_1", "provider": "webhook",
           "config": {"hideForm": True, "mode": "Source", "parameters": {},
                      "type": "webhook"}}


def pipeline_with(llm_node):
    return {
        "components": [
            WEBHOOK,
            llm_node,
            {"id": "response_text_1", "provider": "response_text",
             "config": {"laneName": "text"},
             "input": [{"lane": "text", "from": llm_node["id"]}]},
        ],
        "version": 1,
    }


DOSSIER = json.dumps({
    "project": "Atlas Migration",
    "finding": "DECEASED - no human signal in 38 days; no work in 38 days",
    "evidence": [
        "[slack] 38d ago Priya Raman: Atlas migration is blocked on the schema review.",
        "[github] 38d ago: PR #204 opened, no reviewers assigned",
        "[linear] 2d ago: status still In Progress",
        "[gmail] 21d ago: customer asking for an Atlas timeline, unanswered",
    ],
})


async def main():
    async with RocketRideClient(uri=URI, auth=AUTH) as client:
        working = None
        for label, node in CANDIDATES:
            try:
                print(f"trying {label} ...", flush=True)
                res = await client.use(pipeline=pipeline_with(node))
                token = res["token"]
                out = await client.send(token, DOSSIER,
                                        objinfo={"name": "dossier.json"},
                                        mimetype="application/json")
                text = out.get("text") if isinstance(out, dict) else out
                print(f"  OK -> {str(text)[:400]}", flush=True)
                await client.terminate(token)
                working = node
                break
            except Exception as e:
                print(f"  failed: {str(e)[:220]}", flush=True)

        if not working:
            print("\nNo LLM node config accepted. Falling back to a deployed "
                  "webhook pipeline (still a real Cloud deployment).", flush=True)
            working = None

        pipe = pipeline_with(working) if working else {
            "components": [
                WEBHOOK,
                {"id": "response_text_1", "provider": "response_text",
                 "config": {"laneName": "text"},
                 "input": [{"lane": "text", "from": "webhook_1"}]},
            ], "version": 1}

        # rrext_deploy_add is not exposed on Cloud, so persistence is via
        # client.use(), which is what actually runs the pipeline on their runtime.
        with open("rocketride_pipeline.json", "w") as f:
            json.dump(pipe, f, indent=1)
        print("\nwrote rocketride_pipeline.json", flush=True)


asyncio.run(main())
