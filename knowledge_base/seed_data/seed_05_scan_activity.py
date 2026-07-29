import allure
import pytest
from hamcrest import *
from event_nodes.nodes_scan_activity import ScanActivity


class TestScanActivity:
    def setup_class(self):
        self.scan_activity = ScanActivity()

    @pytest.mark.Scenario
    @allure.testcase('https://tman.devops.rivtower.com/zentao/testcase-view-3853-1.html', '用例地址')
    def test_scan_activity(self):
        """
        创建、上架活动，扫码领取奖励。断言：
        1. 扫码领取流程正确
        2. 奖励发放正确
        :return:
        """
        scan_activity_id = self.scan_activity.create_scan_activity()
        is_flow_success = (self.scan_activity.scan_activity_publish(scan_activity_id).scan(scan_activity_id).
                           get("success"))
        awards_detail = self.scan_activity.admin_activity.scan_detail(
            activity_id=scan_activity_id,
            jmes_expression=
            'data.{activityAwards: activityAwards[*].{qty: qty, realQty: realQty, remindQty: remindQty}, '
            'activityCouponAwards: activityCouponAwards[*].{qty: qty, realQty: realQty, remindQty: remindQty}}'
        )
        expected_awards_detail = {
            'activityAwards': [{'qty': 1, 'realQty': 1, 'remindQty': 0}],
            'activityCouponAwards': [{'qty': 1, 'realQty': 1, 'remindQty': 0}],
        }
        assert_that(is_flow_success, is_(True))
        assert_that(awards_detail, equal_to(expected_awards_detail))
        self.scan_activity.scan_activity_close(scan_activity_id)

    @pytest.mark.SingleAPI
    @allure.testcase('https://tman.devops.rivtower.com/zentao/testcase-view-3854-1.html', '用例地址')
    def test_scan_code_repeatedly(self):
        """
        重复扫码领取奖励的提示
        :return:
        """
        scan_activity_id = self.scan_activity.create_scan_activity()
        self.scan_activity.scan_activity_publish(scan_activity_id).scan(scan_activity_id)
        res = self.scan_activity.scan(scan_activity_id).get("message")
        assert_that(res, equal_to("已领取过该活动奖励"))
        self.scan_activity.scan_activity_close(scan_activity_id)

    @pytest.mark.SingleAPI
    @allure.testcase('https://tman.devops.rivtower.com/zentao/testcase-view-3855.html', '用例地址')
    def test_supply_awards_of_scan_activity(self):
        """
        创建活动，修改奖励内容；断言检查奖励修改是否符合预期
        :return:
        """
        scan_activity_id = self.scan_activity.create_scan_activity()
        is_flow_success = self.scan_activity.supply_scan_activity(scan_activity_id).get("success")
        awards_detail = self.scan_activity.admin_activity.scan_detail(
            activity_id=scan_activity_id,
            jmes_expression=
            'data.{activityAwards: activityAwards[*].{prodName: prodName, qty: qty, sendAwardWay: sendAwardWay}, '
            'activityCouponAwards: activityCouponAwards[*].{prodName: prodName, qty: qty, sendAwardWay: sendAwardWay}}'
        )
        expected_awards_detail = {
            'activityAwards': [{'prodName': 'APIauto_商品2', 'qty': 1, 'sendAwardWay': 11}],
            'activityCouponAwards': [{'prodName': 'APIauto_权益1', 'qty': 2, 'sendAwardWay': 10}]
        }
        assert_that(is_flow_success, is_(True))
        assert_that(awards_detail, equal_to(expected_awards_detail))
        self.scan_activity.scan_activity_close(scan_activity_id)