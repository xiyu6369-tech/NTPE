from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from core.controlled_runtime_queue_admission_authorization_consumption import *
from tests.unit.controlled_runtime_queue_admission_authorization_consumption import build_context
def main():
    with TemporaryDirectory() as d:
        c=build_context(Path(d));first=ControlledRuntimeQueueAdmissionAuthorizationConsumer().consume(**c);second=ControlledRuntimeQueueAdmissionAuthorizationConsumer().consume(**c);claim=first.claim
        checks=(("authentic Stage 6.10",first.upstream_verified),("one request",first.authorization_consumption_count==1),("one claim",claim is not None),("29 layers",claim is not None and len(claim.canonical_chain)==29),("authorized consumed",claim is not None and claim.queue_admission_authorized and claim.queue_admission_authorization_consumed),("nonreusable",claim is not None and not claim.queue_admission_authorization_reusable),("no queue admission",first.queue_admission_count==0),("no records",first.queue_record_prepared_count==first.queue_record_created_count==0),("no runtime/provider/network/translation",(first.scheduler_count,first.runtime_execution_count,first.provider_execution_count,first.network_execution_count,first.translation_execution_count)==(0,0,0,0,0)),("replay closed",second.replay_detected))
    for n,v in checks:print(f"{'PASS' if v else 'FAIL'}: {n}")
    return 0 if all(v for _,v in checks) else 1
if __name__=="__main__":raise SystemExit(main())
