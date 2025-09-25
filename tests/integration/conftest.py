"""
Integration Test Configuration

集成测试配置文件，包含通用fixture和测试设置。
"""

import pytest
import os
import sys
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


@pytest.fixture(scope="session")
def integration_test_config():
    """集成测试配置"""
    return {
        'test_timeout': 60,  # 单个测试超时时间(秒)
        'max_retries': 3,    # 最大重试次数
        'cache_enabled': False,  # 集成测试时禁用缓存
        'mock_external_apis': False,  # 是否模拟外部API
    }


@pytest.fixture
def test_stocks():
    """测试用股票代码"""
    return ['002115', '000002', '600000', '600519', '000858', '002415']


@pytest.fixture
def test_concepts():
    """测试用概念名称"""
    return ['人工智能', '新能源汽车', '半导体', '医药生物', '光伏概念', '锂电池']


@pytest.fixture
def test_date_range():
    """测试用日期范围"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    return {
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'start_year': start_date.year,
        'end_year': end_date.year
    }


@pytest.fixture(autouse=True)
def setup_integration_environment():
    """自动设置集成测试环境"""
    # 设置环境变量
    os.environ['INTEGRATION_TEST'] = 'true'
    os.environ['LOG_LEVEL'] = 'INFO'

    yield

    # 清理环境变量
    os.environ.pop('INTEGRATION_TEST', None)


def pytest_configure(config):
    """配置pytest"""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """修改测试收集行为"""
    for item in items:
        # 为集成测试添加标记
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)

        # 为性能测试添加标记
        if "performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)