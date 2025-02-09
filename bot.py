import nonebot
from nonebot.adapters.onebot.v11 import Adapter as ONEBOT_V11Adapter
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nonebot")


# 定义自定义适配器，继承自 OneBot V11 Adapter，并添加 request 方法
class CustomONEBOT_V11Adapter(ONEBOT_V11Adapter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.http_client = httpx.AsyncClient()
        self.logger = logger

    async def request(self, req):
        """
        自定义的 HTTP 请求方法，用于插件需要发送 HTTP 请求的场景。
        """
        try:
            method = getattr(req, 'method', 'GET')
            url = getattr(req, 'url', '')
            if hasattr(url, 'human_repr'):
                url = url.human_repr()
            elif hasattr(url, '__str__'):
                url = str(url)
            else:
                url = ''

            headers = getattr(req, 'headers', {})
            data = getattr(req, 'content', None) or getattr(req, 'data', None) or getattr(req, 'body', None)

            self.logger.debug(f"发送 HTTP 请求: {method} {url}")
            self.logger.debug(f"请求头: {headers}")
            self.logger.debug(f"请求体: {data}")

            response = await self.http_client.request(
                method=method,
                url=url,
                headers=headers,
                data=data
            )
            response.raise_for_status()
            return response
        except AttributeError as attr_err:
            self.logger.error(f"Request 对象属性错误: {attr_err}")
            raise attr_err
        except Exception as e:
            self.logger.error(f"HTTP 请求失败: {e}")
            raise e

    async def close(self):
        await self.http_client.aclose()
        await super().close()

nonebot.init()

driver = nonebot.get_driver()

driver.register_adapter(CustomONEBOT_V11Adapter)

nonebot.load_builtin_plugins('echo')

nonebot.load_from_toml("pyproject.toml")

@driver.on_shutdown
async def shutdown_handler():
    await driver.adapter.close()

if __name__ == "__main__":
    nonebot.run()
