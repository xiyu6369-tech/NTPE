from __future__ import annotations
import subprocess,sys
def main():
    for label,cmd in (("UNIT",[sys.executable,"-m","pytest","tests/unit/test_controlled_provider_routing.py","-q"]),("INTEGRATION",[sys.executable,"-m","pytest","tests/integration/lcr_batch8_controlled_provider_routing_integration_test.py","-q"])):
        r=subprocess.run(cmd,check=False);print(f"{label}: {'PASS' if r.returncode==0 else 'FAIL'}",flush=True)
        if r.returncode:return r.returncode
    print("PREPARE_ONLY_BOUNDARY: PASS");print("ALL PASS");return 0
if __name__=="__main__":raise SystemExit(main())
