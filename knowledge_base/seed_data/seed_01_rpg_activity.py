import allure
import pytest
from hamcrest import *
from event_nodes.nodes_rpg_activity import RpgActivity
from customize_matcher.rpg_activity_matcher import MatchRpgActivityDataFlowRules


class TestRpgActivity:
    def setup_class(self):
        self.rpg_activity = RpgActivity()

    @pytest.mark.Scenario
    @allure.testcase('https://tman.devops.rivtower.com/zentao/testcase-view-3850-1.html', '用例地址')
    def test_scenario_rpg_activity(self):
        """
        操作步骤：
            Step1: 创建RPG活动
            Step2: 上架活动，否则无法参与
            Step3: 打卡
        断言逻辑：
            1. 流程是否顺利走完（是则继续，否则断言失败）
            2. B端库存校验
            3. C端打卡状态校验
        :return:
        """
        rpg_activity_id = self.rpg_activity.create_rpg_activity()
        is_flow_success = self.rpg_activity.rpg_activity_publish(rpg_activity_id).clock_in_rpg_activity(rpg_activity_id)
        expects = {
            "inventory_statistics": [{'prodName': 'APIauto_商品1',
                                      'assetType': 10,
                                      'lockQuantity': 0,
                                      'mintQuantity': 1,
                                      'totalLockQuantity': 1},
                                     {'prodName': 'APIauto_权益1',
                                      'assetType': 20,
                                      'lockQuantity': 0,
                                      'mintQuantity': 1,
                                      'totalLockQuantity': 1}],
            "clock_in_status": 2,
            "is_flow_success": True,
        }
        assert_that(
            {"activity_id": rpg_activity_id, "is_flow_success": is_flow_success},
            is_(MatchRpgActivityDataFlowRules(expects))
        )

    @pytest.mark.SingleAPI
    @allure.testcase('https://tman.devops.rivtower.com/zentao/testcase-view-3852.html', '用例地址')
    def test_detail_for_modify(self):
        """
        创建RPG活动，比较活动详情查询和编辑时回填的活动详情内容。预期完全一样
        :return:
        """
        rpg_activity_id = self.rpg_activity.create_rpg_activity()
        result = self.rpg_activity.get_detail_and_detail_for_modify(rpg_activity_id)
        assert_that(result["detail"], is_(equal_to(result["detail_for_modify"])))