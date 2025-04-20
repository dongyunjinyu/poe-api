import io
import os
import pickle
import win32con
import win32clipboard
from PIL import Image
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


class Poe:
    def __init__(self, model='https://poe.com/GPT-4.1-nano', cookies_path='poe_cookies.pkl'):
        """
        :param model: Poe模型路径
        :param cookies_path: cookies保存路径
        """
        options = webdriver.EdgeOptions()
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--allow-insecure-localhost')
        options.add_argument("--enable-clipboard-read-write")
        self.driver = webdriver.Edge(options=options)
        self.cookies_path = cookies_path

        # 打开目标网页
        self.driver.get(model)

        # 登录
        if os.path.exists(self.cookies_path):  # 加载 cookies
            with open(cookies_path, 'rb') as file:
                cookies = pickle.load(file)
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
            self.driver.refresh()  # 刷新页面以使 cookies 生效
        else:  # 获取cookies
            input("请手动登录后在终端按Enter后继续...下次无需手动登录")
            cookies = self.driver.get_cookies()  # 获取 Cookies
            with open(cookies_path, 'wb') as file:  # 保存 Cookies
                pickle.dump(cookies, file)

    def set_clipboard_image(self, image_path):
        """将图片写入系统剪贴板"""
        image = Image.open(image_path)
        output = io.BytesIO()
        # 转换为 RGB 模式并保存为 BMP 格式（系统剪贴板图片常用格式）
        image.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]  # 去除 BMP 文件头（前 14 字节为文件头信息）
        output.close()

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        # 以 DIB 格式（设备独立位图）写入剪贴板
        win32clipboard.SetClipboardData(win32con.CF_DIB, data)
        win32clipboard.CloseClipboard()

    def is_session_stop(self):
        """判断当前gpt输出是否结束"""
        try:
            self.driver.find_element(By.CLASS_NAME, 'ChatMessageActionBar_actionBar__gyeEs')  # 需要根据实际类名调整
            return True
        except:
            return False

    def chat(self, text, image=None, clean=True):
        """
        与gpt对话，image不是必需的，当无image时text是必需的。
        :param text: 输入文本
        :param image: 输入图片绝对路径（可选）
        :param clean: 每轮对话后是否清除上下文
        :return: 输出文本
        """
        if text is None and image is None:
            return None

        # 定位输入框
        input_box = self.driver.find_element(By.CLASS_NAME, 'GrowingTextArea_textArea__ZWQbP')

        # 输入文本
        if image:
            self.set_clipboard_image(image)  # 将图片复制到剪贴板
            input_box.send_keys(Keys.CONTROL, 'v')

        # 输入文本
        if text:
            input_box.send_keys(text)

        # 按 Enter 键
        input_box.send_keys(Keys.RETURN)

        # 等待gpt输出结束
        while not self.is_session_stop():
            sleep(1)

        # 获取输出结果
        output_boxes = self.driver.find_elements(By.CLASS_NAME, "pdl")  # 需要根据实际类名调整

        # 清除上下文（可选）
        if clean:
            fresh = self.driver.find_element(By.CSS_SELECTOR, "button.button_ghost__YsMI5")
            self.driver.execute_script("arguments[0].click();", fresh)

        return output_boxes[-1].text
