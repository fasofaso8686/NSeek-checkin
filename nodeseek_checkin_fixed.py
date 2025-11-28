#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NodeSeek 自动签到脚本 - 完整修复版本
支持多账号、北京时间自动签到、Telegram 通知
"""

import os
import sys
import time
import json
import random
from datetime import datetime, timedelta
import requests

IS_GITHUB_ACTIONS = os.environ.get('GITHUB_ACTIONS') == 'true'

if IS_GITHUB_ACTIONS:
    print("[初始化] 检测到 GitHub Actions 环境，使用 Selenium 模式")
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    try:
        from webdriver_manager.chrome import ChromeDriverManager
    except ImportError:
        print("[警告] webdriver_manager 未安装，使用系统 ChromeDriver")


class NodeSeekCheckin:
    """NodeSeek 自动签到类"""
    
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.login_url = "https://www.nodeseek.com/signIn.html"
        self.board_url = "https://www.nodeseek.com/board"
        self.points_earned = 0
        self.driver = None
        
        if IS_GITHUB_ACTIONS:
            self.setup_driver()

    def setup_driver(self):
        """设置 Selenium WebDriver"""
        try:
            print("  [WebDriver] 初始化浏览器...")
            chrome_options = Options()
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            except:
                self.driver = webdriver.Chrome(options=chrome_options)
            
            self.wait = WebDriverWait(self.driver, 40)
            self.driver.set_page_load_timeout(40)
            print("  [WebDriver] ✓ 浏览器初始化成功")
        except Exception as e:
            print(f"  [WebDriver] ✗ 失败: {str(e)}")
            raise

    def login(self):
        """登录 NodeSeek"""
        try:
            print("  [登录] 访问登录页面...")
            self.driver.get(self.login_url)
            time.sleep(3)
            
            try:
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            except:
                pass
            
            time.sleep(2)
            print("  [登录] 填写登录信息...")
            
            # 多方法定位邮箱框
            email_input = None
            try:
                email_input = self.wait.until(
                    EC.presence_of_element_located((By.ID, "stacked-email"))
                )
                print("  [登录] ✓ 邮箱框定位成功")
            except TimeoutException:
                try:
                    email_input = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Email']"))
                    )
                except:
                    pass
            
            if not email_input:
                return False, "❌ 无法定位邮箱输入框"
            
            email_input.clear()
            time.sleep(0.5)
            email_input.send_keys(self.email)
            time.sleep(1)
            
            # 多方法定位密码框
            password_input = None
            try:
                password_input = self.driver.find_element(By.ID, "stacked-password")
            except NoSuchElementException:
                try:
                    password_input = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder='Password']")
                except:
                    pass
            
            if not password_input:
                return False, "❌ 无法定位密码输入框"
            
            password_input.clear()
            time.sleep(0.5)
            password_input.send_keys(self.password)
            time.sleep(1)
            
            print("  [登录] 点击登录按钮...")
            
            # 多方法查找登录按钮
            login_button = None
            selectors = [
                (By.XPATH, "//button[contains(text(), '登录')]"),
                (By.XPATH, "//button[contains(., '登录')]"),
                (By.XPATH, "//button[@type='submit']"),
                (By.CSS_SELECTOR, "button[type='submit']"),
            ]
            
            for selector_type, selector_value in selectors:
                try:
                    buttons = self.driver.find_elements(selector_type, selector_value)
                    if buttons:
                        for btn in reversed(buttons):
                            if btn.is_displayed():
                                login_button = btn
                                break
                        if login_button:
                            break
                except:
                    continue
            
            if not login_button:
                return False, "❌ 无法定位登录按钮"
            
            try:
                self.driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
                time.sleep(0.5)
            except:
                pass
            
            try:
                login_button.click()
            except:
                self.driver.execute_script("arguments[0].click();", login_button)
            
            print("  [登录] 等待登录完成...")
            time.sleep(6)
            
            current_url = self.driver.current_url
            print(f"  [登录] 当前 URL: {current_url}")
            
            if "signIn" not in current_url and current_url != self.login_url:
                print("  [登录] ✓ 登录成功！")
                return True, "✅ 登录成功"
            else:
                return False, "❌ 登录失败"
                
        except Exception as e:
            print(f"  [登录] ✗ {str(e)}")
            return False, f"❌ 登录异常: {str(e)[:50]}"

    def do_checkin(self):
        """执行签到"""
        try:
            print("  [签到] 访问签到页面...")
            self.driver.get(self.board_url)
            time.sleep(4)
            
            page_source = self.driver.page_source
            
            # 检查是否已签到
            if "已签到" in page_source or "签到过" in page_source:
                print("  [签到] ℹ 今日已签到")
                return True, "✅ 今日已签到"
            
            # 随机选择签到类型（1:5 概率）
            rand = random.randint(1, 6)
            
            if rand == 1:
                print("  [签到] 选择: 试试手气 (概率 1/6)")
                button_text = "试试手气"
                button_xpaths = [
                    "//button[contains(text(), '试试手气')]",
                    "//button[text()='试试手气']",
                ]
            else:
                print("  [签到] 选择: 鸡腿 x 5 (概率 5/6)")
                button_text = "鸡腿 x 5"
                button_xpaths = [
                    "//button[contains(text(), '鸡腿')]",
                    "//button[text()='鸡腿 x 5']",
                ]
            
            checkin_button = None
            for xpath in button_xpaths:
                try:
                    buttons = self.driver.find_elements(By.XPATH, xpath)
                    if buttons:
                        for btn in buttons:
                            if btn.is_displayed():
                                checkin_button = btn
                                break
                        if checkin_button:
                            break
                except:
                    continue
            
            if not checkin_button:
                return False, f"❌ 未找到按钮: {button_text}"
            
            try:
                self.driver.execute_script("arguments[0].scrollIntoView(true);", checkin_button)
                time.sleep(0.5)
            except:
                pass
            
            try:
                checkin_button.click()
            except:
                self.driver.execute_script("arguments[0].click();", checkin_button)
            
            print(f"  [签到] 已点击: {button_text}")
            time.sleep(5)
            
            page_source = self.driver.page_source
            
            if "签到成功" in page_source or "恭喜" in page_source or "已签到" in page_source:
                if "x 5" in button_text:
                    self.points_earned = 5
                print(f"  [签到] ✓ 签到成功: {button_text}")
                return True, f"✅ 签到成功 - {button_text}"
            else:
                return True, f"✅ 签到完成 - {button_text}"
                
        except Exception as e:
            print(f"  [签到] ✗ {str(e)}")
            return False, f"❌ 签到异常: {str(e)[:50]}"

    def close(self):
        """关闭浏览器"""
        if IS_GITHUB_ACTIONS and self.driver:
            try:
                self.driver.quit()
                print("  [关闭] ✓ 浏览器已关闭")
            except:
                pass


def send_telegram_message(bot_token, chat_id, message):
    """发送 Telegram 通知"""
    try:
        print("\n[通知] 正在发送 Telegram 消息...")
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML'}
        response = requests.post(url, data=data, timeout=15)
        if response.status_code == 200:
            print("[通知] ✓ 发送成功")
            return True
        else:
            print(f"[通知] ✗ 发送失败")
            return False
    except Exception as e:
        print(f"[通知] ✗ {str(e)}")
        return False


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("NodeSeek 自动签到脚本 - 启动")
    print("=" * 80)
    
    beijing_time = datetime.utcnow() + timedelta(hours=8)
    print(f"\n[时间] 北京时间: {beijing_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    accounts_json = os.environ.get('ACCOUNTS', '[]')
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
    
    try:
        accounts = json.loads(accounts_json)
        print(f"[配置] ✓ 加载 {len(accounts)} 个账号")
    except Exception as e:
        print(f"[配置] ✗ 解析失败: {str(e)}")
        sys.exit(1)
    
    if not accounts:
        print("[配置] ✗ 没有配置账号")
        sys.exit(1)
    
    results = []
    success_count = 0
    fail_count = 0
    
    print("\n" + "=" * 80)
    
    for idx, account in enumerate(accounts, 1):
        email = account.get('email', '')
        password = account.get('password', '')
        
        if not email or not password:
            continue
        
        print(f"\n账号 {idx}/{len(accounts)}: {email}")
        print("=" * 80)
        
        checker = None
        try:
            if IS_GITHUB_ACTIONS:
                checker = NodeSeekCheckin(email, password)
                
                login_success, login_msg = checker.login()
                if not login_success:
                    results.append(f"❌ {email}\n{login_msg}")
                    fail_count += 1
                else:
                    time.sleep(2)
                    checkin_success, checkin_msg = checker.do_checkin()
                    if checkin_success:
                        msg = f"✅ {email}\n{checkin_msg}"
                        if checker.points_earned > 0:
                            msg += f"\n💰 积分: {checker.points_earned}"
                        results.append(msg)
                        success_count += 1
                    else:
                        results.append(f"❌ {email}\n{checkin_msg}")
                        fail_count += 1
        except Exception as e:
            results.append(f"❌ {email}\n异常: {str(e)[:50]}")
            fail_count += 1
        finally:
            if checker:
                checker.close()
        
        if idx < len(accounts):
            print(f"\n⏳ 等待 300 秒后处理下一账号...")
            time.sleep(300)
    
    print(f"\n{'=' * 80}")
    print("所有任务完成")
    print(f"{'=' * 80}")
    
    if bot_token and chat_id:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        msg_lines = [
            "🤖 <b>NodeSeek 签到报告</b>",
            "",
            f"⏰ 时间: {current_time}",
            f"📊 统计: ✅ {success_count} | ❌ {fail_count}",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━",
            ""
        ]
        msg_lines.extend(results)
        message = "\n".join(msg_lines)
        send_telegram_message(bot_token, chat_id, message)
    else:
        print("\n[结果] 签到结果:")
        for result in results:
            print(f"\n{result}")
    
    print(f"\n[统计] 成功: {success_count}，失败: {fail_count}")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[系统] 用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n[系统] 错误: {str(e)}")
        sys.exit(1)
