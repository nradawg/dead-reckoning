import asyncio, json, os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
URI=os.environ.get("ROCKETRIDE_URI","https://api.rocketride.ai")
AUTH=os.environ.get("ROCKETRIDE_AUTH")
PS=os.environ["PIPESHIFT_API_KEY"]; M=os.environ.get("PIPESHIFT_MODEL")
from rocketride import RocketRideClient
SYS=("You are the Coroner, a medical examiner for software projects. Given an "
     "evidence dossier from Slack, GitHub, Linear and Gmail, return ONLY JSON with "
     "keys cause, survived_by, recommendation (REVIVE|REPLACE|BURY), reasoning, eulogy.")
WEB={"id":"webhook_1","provider":"webhook","config":{"hideForm":True,"mode":"Source","parameters":{},"type":"webhook"}}
DOSSIER=json.dumps({"project":"Atlas Migration","finding":"DECEASED, 38 days no work",
 "evidence":["[slack] 38d Priya: Atlas blocked on schema review","[github] 38d PR #204 no reviewers",
             "[linear] 2d status In Progress","[gmail] 21d customer asking timeline, unanswered"]})
async def main():
    async with RocketRideClient(uri=URI, auth=AUTH) as c:
        for out_lane in ("answers","text","response","result","completion"):
            pipe={"components":[WEB,
              {"id":"llm","provider":"llm_openai",
               "config":{"apikey":PS,"model":M,"baseUrl":"https://api.pipeshift.com/api/v0","system":SYS},
               "input":[{"lane":"questions","from":"webhook_1"}]},
              {"id":"resp","provider":"response_text","config":{"laneName":out_lane},
               "input":[{"lane":out_lane,"from":"llm"}]}],"version":1}
            try:
                r=await c.use(pipeline=pipe); t=r["token"]
                o=await c.send(t, DOSSIER, objinfo={"name":"d.json"}, mimetype="application/json")
                print(f"out_lane={out_lane} -> keys={list(o.keys()) if isinstance(o,dict) else type(o)}", flush=True)
                print("   FULL:", json.dumps(o, default=str)[:600], flush=True)
                await c.terminate(t)
                if isinstance(o,dict) and any(o.get(k) for k in (out_lane,"text")):
                    print("   *** WORKING LANE:", out_lane, flush=True); break
            except Exception as e:
                print(f"out_lane={out_lane} failed: {str(e)[:160]}", flush=True)
asyncio.run(main())
