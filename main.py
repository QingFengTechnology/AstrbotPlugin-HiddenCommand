import sys
from astrbot.api.star import Context, Star
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api import AstrBotConfig, logger

class HiddenCommand(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config: dict = config
        self.blocked_cmds: list = self.config.get("HiddenCommands")
        self.command_prefixes: list = self.config.get("CommandPrefixes")
        self.release_admin: bool = self.config.get("ReleaseAdministrator")
        logger.info(f"[HiddenCommand] 插件已启动。")

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
            if event.is_admin() and self.release_admin:
                logger.debug(f"[HiddenCommand] 已检测到命令 {matched_format} 被触发，但调用者为管理员，忽略。")
                return
            else:
                logger.info(f"[HiddenCommand] 已拦截命令 {matched_format}。")
                event.stop_event()
                return