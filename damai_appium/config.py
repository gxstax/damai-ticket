# -*- coding: UTF-8 -*-
"""
__Author__ = "WECENG"
__Description__ = "配置类"
__Created__ = 2023/10/27 09:54
"""
import json


class DeviceConfig:
    def __init__(self, platform_name, platform_version, device_name, automation_name,
                 no_reset, skip_server_installation, adb_exec_timeout,
                 uiautomator2_server_install_timeout):
        self.platformName = platform_name
        self.platformVersion = platform_version
        self.deviceName = device_name
        self.automationName = automation_name
        self.noReset = no_reset
        self.skipServerInstallation = skip_server_installation
        self.adbExecTimeout = adb_exec_timeout
        self.uiautomator2ServerInstallTimeout = uiautomator2_server_install_timeout


class Config:
    def __init__(self, server_url, device_config, keyword, users, city, date, price, price_index, if_commit_order):
        self.server_url = server_url
        self.device = device_config
        self.keyword = keyword
        self.users = users
        self.city = city
        self.date = date
        self.price = price
        self.price_index = price_index
        self.if_commit_order = if_commit_order

    @staticmethod
    def load_config():
        with open('config.jsonc', 'r', encoding='utf-8') as config_file:
            config = json.load(config_file)

        device_cfg = config.get('device', {})
        device_config = DeviceConfig(
            platform_name=device_cfg.get('platformName', 'Android'),
            platform_version=device_cfg.get('platformVersion', ''),
            device_name=device_cfg.get('deviceName', ''),
            automation_name=device_cfg.get('automationName', 'UiAutomator2'),
            no_reset=device_cfg.get('noReset', True),
            skip_server_installation=device_cfg.get('skipServerInstallation', False),
            adb_exec_timeout=device_cfg.get('adbExecTimeout', 20000),
            uiautomator2_server_install_timeout=device_cfg.get('uiautomator2ServerInstallTimeout', 120000)
        )

        return Config(
            server_url=config['server_url'],
            device_config=device_config,
            keyword=config['keyword'],
            users=config['users'],
            city=config['city'],
            date=config['date'],
            price=config['price'],
            price_index=config['price_index'],
            if_commit_order=config['if_commit_order']
        )
