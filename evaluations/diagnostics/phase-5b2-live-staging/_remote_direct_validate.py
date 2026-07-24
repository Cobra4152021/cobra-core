
import json, os, urllib.request, urllib.error
token=os.environ["TOKEN"]
base=os.environ["BASE"].rstrip("/")
rev=os.environ["REV"]
sha=os.environ["SHA"]
results=[]

def check(name, ok, detail=""):
    results.append({"name":name,"pass":bool(ok),"detail":str(detail)[:200]})
    print(("PASS" if ok else "FAIL"), name, str(detail)[:120])

def req(method, path, token=None, body=None, rid=None, timeout=300):
    data=None if body is None else json.dumps(body).encode()
    headers={"Accept":"application/json","Content-Type":"application/json"}
    if token is not None:
        headers["Authorization"]=f"Bearer {token}"
    if rid:
        headers["x-request-id"]=rid
    r=urllib.request.Request(base+path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode()), dict(resp.headers)
    except urllib.error.HTTPError as e:
        raw=e.read().decode(errors="replace")
        try: payload=json.loads(raw)
        except Exception: payload={"raw":raw[:200]}
        return e.code, payload, dict(e.headers)

st,body,hdrs=req("GET","/health",token=token,rid="cc_5b2_health")
check("health_auth_ok", st==200 and body.get("protocolVersion")=="1" and body.get("compatibilityVersion")=="1" and body.get("model")=="cobra-core-qwen3-8b" and body.get("reason")=="ok", f"status={st} reason={body.get('reason')}")
check("revision", body.get("revision")==rev, body.get("revision"))
check("gitSha", str(body.get("gitSha","")).startswith(sha[:12]), body.get("gitSha"))
limits=body.get("limits") or {}
check("limits_context", limits.get("maxContext")==8192, limits)
check("limits_output", limits.get("maxOutputTokens")==256, limits)
st,body,_=req("GET","/health",token=None)
check("health_no_auth", st==401, st)
st,body,_=req("GET","/health",token="definitely-wrong")
check("health_bad_auth", st==401, st)
rid="cc_5b2_complete"
st,body,hdrs=req("POST","/v1/chat/completions",token=token,rid=rid,body={"model":"cobra-core-qwen3-8b","stream":False,"max_tokens":48,"messages":[{"role":"user","content":"Reply with exactly: pong"}]},timeout=300)
text=((((body.get("choices") or [{}])[0].get("message") or {}).get("content")) or "")
usage=body.get("usage") or {}
latency=body.get("latency") or {}
check("completion_ok", st==200 and bool(str(text).strip()), f"status={st} len={len(str(text))}")
check("request_id_preserved", hdrs.get("x-request-id")==rid or body.get("requestId")==rid, "")
check("usage", all(k in usage for k in ("prompt_tokens","completion_tokens","total_tokens")) and usage.get("total_tokens")==usage.get("prompt_tokens",-1)+usage.get("completion_tokens",-1), usage)
check("latency", all(k in latency for k in ("queue_ms","provider_latency_ms","inference_ms","total_ms")), latency)
check("no_traceback", "traceback" not in json.dumps(body).lower(), "")
st,body,hdrs=req("POST","/v1/chat/completions",token=token,body={"model":"cobra-core-qwen3-8b","stream":False,"max_tokens":16,"messages":[{"role":"user","content":"id"}]})
gen=hdrs.get("x-request-id") or body.get("requestId") or ""
check("request_id_generated", st==200 and str(gen).startswith("cc_"), str(gen)[:40])
st,body,_=req("POST","/v1/chat/completions",token=token,body={"model":"cobra-core-qwen3-8b","stream":False,"max_tokens":99999,"messages":[{"role":"user","content":"Say hi in under five words."}]},timeout=300)
check("output_limit_cap", st==200 and bool(body.get("choices")), st)
st,body,_=req("POST","/v1/chat/completions",token=token,body={"model":"cobra-core-qwen3-8b","stream":False,"max_tokens":8,"messages":[]})
check("bad_request", st==400 and body.get("code")=="bad_request", st)
check("safe_error", "traceback" not in json.dumps(body).lower(), "")
open("/workspace/logs/direct-results.json","w").write(json.dumps(results, indent=2))
print("RESULTS_JSON_OK")
