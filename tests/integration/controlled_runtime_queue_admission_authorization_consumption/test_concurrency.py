from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from core.controlled_runtime_queue_admission_authorization_consumption import *
from tests.unit.controlled_runtime_queue_admission_authorization_consumption import build_context
def test_six_consumers_one_success(tmp_path):
    c=build_context(tmp_path);barrier=Barrier(6)
    def run(_):barrier.wait();return ControlledRuntimeQueueAdmissionAuthorizationConsumer().consume(**dict(c))
    with ThreadPoolExecutor(max_workers=6) as pool:results=list(pool.map(run,range(6)))
    assert sum(r.claim is not None for r in results)==1
    assert sum(r.replay_detected for r in results)==5
    assert ControlledRuntimeQueueAdmissionAuthorizationConsumptionRegistry(c["database_path"],allowed_root=tmp_path).count_claims()==1
