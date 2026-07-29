import logging
from pprint import pformat

import allure
import pytest
from hamcrest import *
from apis.dap.activity_apply_api import ActivityApplyApi
from event_nodes.nodes_educational_activity import EducationalActivity
from db.db_operations import DBOperations


class TestEducationalActivity:
    def setup_class(self):
        self.educational_activity = EducationalActivity()
        self.activity_apply = ActivityApplyApi()
        self.db_operations = DBOperations()

    @pytest.fixture(scope='class')
    def _precondition_of_apply(self):
        """
        报名用例前置条件
        :return:
        """
        activity_id_0 = self.educational_activity.create_educational_activity(case='case_0')
        self.educational_activity.educational_activity_publish(activity_id_0)
        activity_id_1 = self.educational_activity.create_educational_activity(case='case_1')
        self.educational_activity.educational_activity_publish(activity_id_1)

        yield {
            'case_0': {'req': {'activityId': str(activity_id_0)}, 'exp': '未填写报名信息必填项'},
            'case_1': {'req': {'activityId': str(activity_id_1)}, 'exp': '账户积分不足'},
        }

    @pytest.mark.SingleAPI
    @allure.testcase('https://tman.devops.rivtower.com/zentao/testcase-view-3839-1.html', '用例地址')
    @pytest.mark.parametrize(
        "case_key", ["case_0", "case_1"],
        ids=["未填写报名信息必填项", "报名积分兑换不足"]
    )
    def test_batch_order_create(self, _precondition_of_apply, case_key):
        """
        报名单接口测试
        :return:
        """
        req_data = _precondition_of_apply.get(case_key).get('req')
        logging.info(f'请求参数：\n{pformat(req_data)}')
        resp = self.activity_apply.batch_order_create(
            req_data=req_data,
            jmes_expression='@'
        )
        logging.info(f'返回结果：\n{pformat(resp)}')
        assert_that(resp, all_of(
            has_entry('success', is_(False)),
            has_entry('message', equal_to(_precondition_of_apply.get(case_key).get('exp')))
        ))

    @pytest.fixture(scope='function')
    def create_activity_need_educational_codes(self):
        activity_id = self.educational_activity.create_educational_activity(case="case_2")
        yield activity_id

    @pytest.mark.SingleAPI
    @allure.testcase('https://tman.devops.rivtower.com/zentao/testcase-view-3847.html', '用例地址')
    def test_bind_without_publish(self, create_activity_need_educational_codes):
        """
        未上架时绑定研学码，预期需要上架才能绑定
        :param create_activity_need_educational_codes:
        :return:
        """
        resp = self.educational_activity.bind_educational_codes(
            educational_activity_id=create_activity_need_educational_codes
        )
        assert_that(resp, all_of(
            has_entry('success', is_(False)),
            has_entry('message', equal_to('活动不是上架状态'))
        ))