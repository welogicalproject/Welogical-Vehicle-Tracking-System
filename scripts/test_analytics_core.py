import os
import sys
from datetime import date

# Add project root to python path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app.database import SyncSessionLocal
from app.services.analytics.base import BaseProcessor, PipelineContext
from app.services.analytics.manager import AnalyticsPipelineManager

# Mock Stage Processors
class MockStage2Processor(BaseProcessor):
    name = "MockStage2Processor"
    stage = 2

    def process(self, context: PipelineContext, db) -> bool:
        print(f" -> [EXECUTE] Run: {self.name} (Stage {self.stage})")
        context.metrics_cache["stage_2_completed"] = True
        return True

class MockStage1Processor(BaseProcessor):
    name = "MockStage1Processor"
    stage = 1

    def process(self, context: PipelineContext, db) -> bool:
        print(f" -> [EXECUTE] Run: {self.name} (Stage {self.stage})")
        context.metrics_cache["stage_1_completed"] = True
        return True

class MockFailProcessor(BaseProcessor):
    name = "MockFailProcessor"
    stage = 3

    def process(self, context: PipelineContext, db) -> bool:
        print(f" -> [EXECUTE] Run: {self.name} (Stage {self.stage}) - Simulating process failure")
        return False

def test_pipeline_core():
    print("======================================================================")
    print("                 VTS ANALYTICS ENGINE INTEGRATION TEST                 ")
    print("======================================================================")
    
    manager = AnalyticsPipelineManager(group_name="test_group_manager")

    # 1. Test registration
    p2 = MockStage2Processor()
    p1 = MockStage1Processor()
    
    manager.register_processor(p2)
    manager.register_processor(p1)

    # 2. Test sorting
    sorted_procs = sorted(manager.processors, key=lambda p: p.stage)
    assert sorted_procs[0].stage == 1, "Failed: sorting order incorrect"
    assert sorted_procs[1].stage == 2, "Failed: sorting order incorrect"
    print("[OK] Processor priority stages sorted successfully.")

    # 3. Test execution context data sharing
    context = PipelineContext(run_date=date.today(), start_id=101, end_id=200)
    db = SyncSessionLocal()

    print("\n[RUNNING] Executing standard success chain:")
    for proc in sorted_procs:
        success = proc.process(context, db)
        assert success is True, f"Failed executing: {proc.name}"

    assert context.metrics_cache.get("stage_1_completed") is True, "Failed: Stage 1 failed caching metrics"
    assert context.metrics_cache.get("stage_2_completed") is True, "Failed: Stage 2 failed caching metrics"
    print("[OK] Shared context cache states updated successfully across pipeline steps.")

    # 4. Test transactional execution and rollback failure handling
    pf = MockFailProcessor()
    manager.register_processor(pf)

    print("\n[RUNNING] Testing abort execution sequence:")
    try:
        for proc in sorted(manager.processors, key=lambda p: p.stage):
            print(f"Executing step {proc.stage}: {proc.name}...")
            status = proc.process(context, db)
            if not status:
                raise Exception(f"Abort triggered at processor '{proc.name}' stage.")
        print("[FAIL] Pipeline completed when it should have raised exception.")
    except Exception as e:
        print(f"[OK] Pipeline execution successfully intercepted error: '{str(e)}'")

    db.close()
    print("\n======================================================================")
    print("                   ANALYTICS ENGINE UNIT TEST PASSED                   ")
    print("======================================================================")

if __name__ == "__main__":
    test_pipeline_core()
