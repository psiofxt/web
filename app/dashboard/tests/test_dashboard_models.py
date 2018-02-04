# -*- coding: utf-8 -*-
"""Handle dashboard model related tests.

Copyright (C) 2018 Gitcoin Core

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.

"""
from datetime import datetime

from django.test import TestCase

from dashboard.models import Bounty
from economy.models import ConversionRate


class DashboardModelsTest(TestCase):
    """Define tests for dashboard models."""

    def setUp(self):
        """Perform setup for the testcase."""
        ConversionRate.objects.create(
            from_amount=1,
            to_amount=2,
            source='etherdelta',
            from_currency='ETH',
            to_currency='USDT',
        )

    def test_bounty(self):
        """Test the dashboard Bounty model."""
        bounty = Bounty(
            title='foo',
            value_in_token=3,
            token_name='ETH',
            web3_created=datetime(2008, 10, 31),
            github_url='https://github.com/gitcoinco/web',
            token_address='0x0',
            issue_description='hello world',
            fulfiller_github_username='fred',
            bounty_owner_github_username='flintstone',
            is_open=False,
            accepted=True,
            expires_date=datetime(2008, 11, 30),
            fulfiller_address="0x0000000000000000000000000000000000000000",
            idx_project_length = 5,
            bounty_type='Feature',
            experience_level='Intermediate',
        )
        assert str(bounty) == 'foo 3 ETH 2008-10-31 00:00:00'
        assert bounty.url == '/funding/details?url=https://github.com/gitcoinco/web'
        assert bounty.title_or_desc == 'foo'
        assert bounty.issue_description_text == 'hello world'
        assert bounty.org_name == 'gitcoinco'
        assert bounty.is_hunter('fred') == True
        assert bounty.is_hunter('flintstone') == False
        assert bounty.is_funder('fred') == False
        assert bounty.is_funder('flintstone') == True
        assert bounty.get_avatar_url
        assert bounty.status == 'expired'
        assert bounty.value_true == 3e-18
        assert bounty.value_in_eth == 3
        assert bounty.value_in_usdt == 0
        assert 'ago 5 Feature Intermediate' in bounty.desc
        assert bounty.is_legacy == False
        assert bounty.get_github_api_url() == 'https://api.github.com/repos/gitcoinco/web'
