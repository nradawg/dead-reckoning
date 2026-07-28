"""Compute every certificate (all scopes) and store them in InsForge.

The demo UI then reads InsForge directly. No Python runs during the demo, so
the on-stage scope toggle cannot be broken by a slow import, a flaky TLS
connection, or a model that decides to think for thirty seconds.
"""
import json
import sys
import time

from agents import coroner, morgue

SCOPES = [None, ["linear"]]


def main():
    rows = []
    for slug, meta in coroner.CORPUS.items():
        for scope in SCOPES:
            label = "all" if not scope else ",".join(scope)
            t = time.time()
            try:
                cert = coroner.autopsy(slug, scope)
            except Exception as e:
                print(f"  {slug}/{label} FAILED: {str(e)[:160]}")
                continue

            try:
                morgue.save({
                    "project": cert["project"], "scope": cert["scope"],
                    "verdict": cert["verdict"], "confidence": cert["confidence"],
                    "time_of_death": cert.get("time_of_death"),
                    "cause": cert.get("cause"),
                    "survived_by": cert.get("survived_by"),
                    "recommendation": cert.get("recommendation"),
                    "alternative": cert.get("alternative"),
                    "evidence": cert["evidence"],
                    "evidence_count": cert["evidence_count"],
                })
                stored = "stored"
            except Exception as e:
                stored = f"STORE FAILED {str(e)[:80]}"

            print(f"  {meta['display']:<22} {label:<7} {cert['verdict']:<12} "
                  f"ev={cert['evidence_count']:<3} {time.time() - t:.1f}s  {stored}")
            rows.append(cert)

    with open("certificates.json", "w") as f:
        json.dump(rows, f, indent=1)
    print(f"\nwrote {len(rows)} certificates to certificates.json")


if __name__ == "__main__":
    print("computing certificates (first import is slow, be patient)...")
    sys.stdout.flush()
    main()
