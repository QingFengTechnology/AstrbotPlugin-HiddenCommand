
import sys
from astrbot.api.star import Context, Star, register
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api import logger

@register("astrbot_plugin_restrict_syscmd", "木有知", 
          "系统指令权限控制插件 - 防止非管理员恶意重置和探测机器人身份", 
          "0.2.0", 
          "https://github.com/muyouzhi6/astrbot_plugin_restrict_syscmd")
class RestrictSysCmd(Star):
    def __init__(self, context: Context, config=None):
        super().__init__(context)
        self.config = config or {}
        self.blocked_cmds = set(self.config.get("blocked_commands", [
            "new", "reset", "help", "start", "stop", "about", "status", "config", "settings", "plugin", "plugins_ls"
        ]))
        logger.info(f"restrict_syscmd 插件已加载，拦截指令: {self.blocked_cmds}")

    def is_restricted_command(self, msg: str):
        """检测是否为受限制的系统命令（支持多种格式）"""
        clean_msg = msg.strip()
        # 统一移除可选的'/'前缀
        if clean_msg.startswith('/'):
            command_text = clean_msg[1:]
        else:
            command_text = clean_msg
        # 如果消息为空（例如仅输入'/'），则不是有效指令
        if not command_text:
            return False, None
        # 提取指令部分（第一个空格前的内容）
        cmd_part = command_text.split(maxsplit=1)[0]
        if cmd_part in self.blocked_cmds:
            # 为了日志记录，可以返回用户输入的原始格式
            original_cmd_format = clean_msg.split(maxsplit=1)[0]
            return True, original_cmd_format
        return False, None

    @filter.event_message_type(filter.EventMessageType.ALL, priority=sys.maxsize-1)
    async def restrict_syscmd_handler(self, event: AstrMessageEvent):
        msg = event.get_message_str().strip()
        is_restricted, matched_format = self.is_restricted_command(msg)
        if is_restricted:
            user_info = f"{event.get_sender_name()}({event.get_sender_id()})"
            if not event.is_admin():
                logger.info(f"[restrict_syscmd] 非管理员拦截: {user_info} | 指令: '{matched_format}'")
                event.stop_event()
                return
            else:
                logger.info(f"[restrict_syscmd] 管理员放行: {user_info} | 指令: '{matched_format}'")

    async def terminate(self):
        logger.info("restrict_syscmd 插件已卸载")
