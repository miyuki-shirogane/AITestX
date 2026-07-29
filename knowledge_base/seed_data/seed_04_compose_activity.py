import allure
import pytest
from hamcrest import *

from apis.dap.activity_api import ActivityApi
from customize_matcher.compose_activity_matcher import MatchComposeActivityDataFlowRules
from event_nodes.nodes_compose_activity import ComposeActivity


class TestComposeActivity:
    def setup_class(self):
        self.compose_activity = ComposeActivity()
        self.activity = ActivityApi()

    @pytest.mark.Scenario
    @allure.testcase('https://tman.devops.rivtower.com/zentao/testcase-view-3841-1.html', '用例地址')
    def test_scenario_compose_activity(self):
        """
        操作步骤：
            Step1: 创建合成活动
            Step2: 上架活动，否则无法参与
            Step3: 发放素材 -> 合成
        断言逻辑：
            1. 流程是否顺利走完（是则继续，否则断言失败）
            2. B端合成数量校验
            3. C端合成次数校验
        :return:
        """
        compose_activity_id = self.compose_activity.create_compose_activity()
        is_flow_success = (self.compose_activity.compose_activity_publish(compose_activity_id).
                           grant_material_to_user().compose(compose_activity_id).get('success'))
        expects = {
            'is_flow_success': True,
            'compose_count': 2,
            'compose_times': 1
        }
        assert_that(
            {"activity_id": compose_activity_id, "is_flow_success": is_flow_success},
            is_(MatchComposeActivityDataFlowRules(expects))
        )

    @pytest.fixture(scope="function")
    def _precondition_of_edit(self):
        compose_activity_params = self.compose_activity.get_create_compose_activity_params(
            product_awards_cases=[],
            coupon_awards_cases=['case_2', 'case_3']
        )
        compose_activity_id = self.compose_activity.create_compose_activity(
            params=compose_activity_params
        )
        yield compose_activity_id
        self.compose_activity.compose_activity_close(compose_activity_id)

    @pytest.mark.SingleAPI
    @allure.testcase('https://tman.devops.rivtower.com/zentao/testcase-view-3843.html', name="用例地址")
    def test_edit_compose_activity(self, _precondition_of_edit):
        """
        修改合成活动奖励和素材，关闭活动后校对活动详情中相关数据正确
        :param _precondition_of_edit:
        :return:
        """
        (self.compose_activity.compose_edit_supply(_precondition_of_edit).add_material(_precondition_of_edit).
         delete_material(_precondition_of_edit))
        result_actual = self.compose_activity.get_compose_info_for_edit(_precondition_of_edit)
        assert_that(result_actual, has_entries({
            'awards': contains_inanyorder({'name': 'APIauto_商品2', 'qty': 1}),
            'coupons': contains_inanyorder({'name': 'APIauto_权益2', 'qty': 10}),
            'materials': contains_inanyorder(
                {'expend': 1, 'name': 'APIauto_商品1'},
                {'expend': 1, 'name': 'APIauto_商品3'}
            )
        }))