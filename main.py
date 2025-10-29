import sys
from astrbot.api.star import Context, Star
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api import logger

class HiddenCommand(Star):
    def __init__(self, context: Context, config=None):
        super().__init__(context)
        self.config = config or {}
        self.blocked_cmds = set(self.config.get("HiddenCommands"))
        self.command_prefixes = self.config.get("CommandPrefixes")
        self.release_admin = self.config.get("ReleaseAdministrator", True)
        logger.info(f"[HiddenCommand] 插件已启动，将拦截前缀为 {self.command_prefixes} 的这些指令: {self.blocked_cmds}。")

    def is_restricted_command(self, msg: str):
        """检测是否为受限制的系统命令"""
        clean_msg = msg.strip()
        matched_prefix = None
        command_text = clean_msg
        for prefix in sorted(self.command_prefixes, key=lambda x: -len(x)):
            if prefix and clean_msg.startswith(prefix):
                matched_prefix = prefix
                command_text = clean_msg[len(prefix):]
                break
            elif prefix == "" and not matched_prefix:
                matched_prefix = ""
                command_text = clean_msg
        if not command_text:
            return False, None
        cmd_part = command_text.split(maxsplit=1)[0]
        if cmd_part in self.blocked_cmds:
            original_cmd_format = clean_msg.split(maxsplit=1)[0]
            return True, original_cmd_format
        return False, None

    @filter.event_message_type(filter.EventMessageType.ALL, priority=sys.maxsize-1)
    async def restrict_syscmd_handler(self, event: AstrMessageEvent):
        """检查命令是否应被拦截"""
        msg = event.get_message_str().strip()
        is_restricted, matched_format = self.is_restricted_command(msg)
        if is_restricted:
            user_info = f"{event.get_sender_name()}({event.get_sender_id()})"
            
            # 检查管理员是否受限制
            release_admin = self.config.get("ReleaseAdministrator", True)
            
            if event.is_admin() and release_admin:
                logger.debug(f"[HiddenCommand] 已检测到指令被触发，但触发用户为管理员，放行命令。")
                return
            else:
                logger.info(f"[HiddenCommand] 已拦截指令 {matched_format}。")
                event.stop_event()
                return

    async def terminate(self):
        logger.info("[HiddenCommand] 插件已停止。")
