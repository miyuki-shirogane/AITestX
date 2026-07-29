import allure
import pytest
from hamcrest import *
from event_nodes.nodes_clock_in_activity import ClockInActivity
from util.tool import mock_data


class TestClockInActivity:
    def setup_class(self):
        self.clock_in_activity = ClockInActivity()

    @pytest.mark.SingleAPI
    @allure.testcase(url="https://tman.devops.rivtower.com/zentao/testcase-view-3860.html", name="用例地址")
    def test_unlock_activity_exceed_limit(self):
        """
        超限次解锁活动
        :return:
        """
        clock_in_activity_id = self.clock_in_activity.create_clock_in_activity()
        (self.clock_in_activity.clock_in_activity_publish(clock_in_activity_id).
         unlock_clock_in_activity(clock_in_activity_id))
        resp = self.clock_in_activity.unlock_clock_in_activity(
            clock_in_activity_id=clock_in_activity_id, use_another_account=True
        )
        assert_that(resp["message"], equal_to("库存不足"))

    @pytest.mark.SingleAPI
    @allure.testcase(url="https://tman.devops.rivtower.com/zentao/testcase-view-3861-1.html", name="用例地址")
    def test_clock_in_exceed_limit(self):
        """
        超限次打卡
        :return:
        """
        clock_in_activity_id = self.clock_in_activity.create_clock_in_activity(case="case_1")
        self.clock_in_activity.clock_in_activity_publish(clock_in_activity_id).clock_in_reward(clock_in_activity_id)
        resp = self.clock_in_activity.clock_in_reward(clock_in_activity_id)
        assert_that(resp["message"], equal_to("打卡次数已达上限"))

    @pytest.fixture(scope='function')
    def precondition_of_team_cases(self):
        clock_in_activity_id = self.clock_in_activity.create_clock_in_activity(case="case_1")
        team_id = (self.clock_in_activity.clock_in_activity_publish(clock_in_activity_id).
                   share_my_team_and_gen_team_id(clock_in_activity_id))
        yield team_id

    @pytest.mark.SingleAPI
    @pytest.mark.parametrize(
        "use_another_account", [True, False], ids=["队员编辑队伍名称", "队长编辑队伍名称"]
    )
    @allure.testcase(url="https://tman.devops.rivtower.com/zentao/testcase-view-3862-1.html", name="用例地址")
    def test_edit_team(self, precondition_of_team_cases, use_another_account):
        team_name = mock_data("team_name")
        self.clock_in_activity.join_team(team_id=precondition_of_team_cases, use_another_account=True)
        resp = self.clock_in_activity.edit_team(
            team_id=precondition_of_team_cases, team_name=team_name, use_another_account=use_another_account
        )
        actual_team_name = self.clock_in_activity.get_info(
            team_id=precondition_of_team_cases, use_another_account=False, search_expression="data.team.teamName"
        )
        assert_that(actual_team_name, equal_to(team_name))