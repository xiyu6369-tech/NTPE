from pathlib import Path

from core.adaptive_context_single_real_invocation import FakeSingleInvocationTransport
from core.controlled_multi_chunk_translation_canary import (
    ControlledMultiChunkExecutor, build_multi_chunk_request,
    resolve_multi_chunk_source,
)
from core.controlled_runtime_scheduling_dispatch import (
    verify_controlled_runtime_scheduling_dispatch,
)
from tests.unit.controlled_translation_runtime_integration import (
    build_context as build_stage73_context,
)


FAKE_OUTPUTS = (
    """鄭泰義正陷入為難。他明白遠方那個怪物般的男人仍有理智，也應當知道眼前局面並非出自他的本意。

然而，凱爾早已為這一週假期等待了好幾個月。那個男人因工作延遲歸來，凱爾便不肯讓任何事情侵占難得的休息，索性把仍在鄰國工作的弟弟丟下，只帶著鄭泰義來到遙遠的南方島嶼。

平日理性的凱爾原本不會如此衝動，可弟弟臨行前燒掉了他珍愛的書，害他氣得病倒三天。想到回到柏林後可能爆發的風波，鄭泰義坐在飯店大廳的沙發上，久久吐出一口沉重的氣。""",
    """「事情既然已經發生，再提前煩惱也沒有用。難得來休假，總不能整整一週都只顧著嘆氣。」

鄭泰義作出合理的結論，點了點頭。這座被深青玉色海水環繞的小島既美麗又悠閒。

來時凱爾曾告訴他，島上的飯店幾乎只供幾名富豪當作私人別墅，普通遊客無法進入，因此很適合在不受旁人打擾的情況下度過寬裕假期。

事實的確如此。自從昨天抵達後，鄭泰義見過的人除了管理員與職員之外，少得用十根手指都數不滿。

「到人煙稀少的海邊走走也不錯。」

他一鼓作氣站起身。凱爾此刻應該仍在私人泳池旁的長椅上熟睡；為了這一週假期，那個人直到出發前都徹夜工作，臉色疲憊得嚇人，所以鄭泰義實在無法拒絕他的堅持。""",
    """潟湖離海灘很近，鄭泰義沿著白沙緩步前行。就在他準備離開大廳時，外頭傳來幾道談話聲。

若只想在附近閒晃，也可以沿著伸向海面的木橋散步；但他打算慢慢繞島一圈，便選擇了白沙灘。聽說這座島很小，大約兩個小時就能走完全程。

他穿著及膝短褲，外頭隨意披了一件寬鬆襯衫。正當他要踏出大廳時，外面忽然變得有些熱鬧。其實那只是兩三個人的交談聲，只因四周太安靜，才顯得格外清楚。

熟悉的德語讓鄭泰義不由自主地停住腳步。聲音並不是那個男人，他卻仍反射性屏住呼吸。

來者用冷靜而公事公辦的語氣解釋，他與原定同行的人分開抵達，而對方將在一兩個小時內出現。說話之間，那名德國人隨即走進視野。""",
)


def build_context(tmp_path: Path, *, outputs=FAKE_OUTPUTS):
    stage73 = build_stage73_context(tmp_path / "stage73")
    dispatch = stage73["dispatch_package"]
    verification = verify_controlled_runtime_scheduling_dispatch(
        stage73["schedule"],
        dispatch,
        request=stage73["stage72_request"],
        result=stage73["stage72_result"],
        queue_record=stage73["queue_record"],
        stage71_request=stage73["stage71_request"],
        stage71_result=stage73["stage71_result"],
        stage613_claim=stage73["stage613_claim"],
        stage613_request=stage73["stage613_request"],
        stage613_result=stage73["stage613_result"],
        stage613_verification_context=stage73["stage613_verification_context"],
        persisted_schedule_payload_json=stage73["schedule"].to_json(),
        persisted_dispatch_payload_json=dispatch.to_json(),
        persistence_committed=True,
        schedule_readback_verified=True,
        dispatch_readback_verified=True,
    )
    resolved = resolve_multi_chunk_source(
        dispatch, root=Path(__file__).resolve().parents[3]
    )
    request = build_multi_chunk_request(dispatch, resolved.plans)
    return {
        "request": request,
        "dispatch_package": dispatch,
        "stage72_verification": verification,
        "repository_root": Path(__file__).resolve().parents[3],
        "artifact_root": tmp_path / "artifacts",
        "execution_mode": "fake",
        "transport_factory": lambda index: FakeSingleInvocationTransport(
            outputs=(outputs[index - 1],)
        ),
        "environ": {},
    }
