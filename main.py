
import re
import sys
from astrbot.api.star import Context, Star, register
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api import logger

def build_cmd_pattern(cmds):
    if not cmds:
        return None
    pat = r'^/(%s)(\s|$)' % '|'.join(re.escape(cmd) for cmd in cmds)
    return re.compile(pat)

@register("astrbot_plugin_restrict_syscmd", "木有知", 
          "系统指令权限控制插件 - 防止非管理员恶意重置和探测机器人身份", 
          "0.2.0", 
          "https://github.com/muyouzhi6/astrbot_plugin_restrict_syscmd")
class RestrictSysCmd(Star):
    def __init__(self, context: Context, config=None):
        super().__init__(context)
        self.config = config or {}
        self.blocked_cmds = self.config.get("blocked_commands", [
            "new", "reset", "help", "start", "stop", "about", "status", "config", "settings"
        ])
        self.cmd_pattern = build_cmd_pattern(self.blocked_cmds)
        logger.info(f"restrict_syscmd 插件已加载，拦截指令: {self.blocked_cmds}")
        logger.info(f"支持格式: /command、command（私聊）、@机器人 command（群聊）")

    def is_restricted_command(self, msg, event):
        """检测是否为受限制的系统命令（支持多种格式）"""
        clean_msg = msg.strip()
        
        # 检查各种命令格式
        for blocked_cmd in self.blocked_cmds:
            # 格式1: /command
            if clean_msg == f"/{blocked_cmd}" or clean_msg.startswith(f"/{blocked_cmd} "):
                return True, f"/{blocked_cmd}"
                
            # 格式2: 纯command（私聊或@消息）
            if clean_msg == blocked_cmd or clean_msg.startswith(f"{blocked_cmd} "):
                return True, blocked_cmd
                
        return False, None

    @filter.event_message_type(filter.EventMessageType.ALL, priority=sys.maxsize-1)
    async def restrict_syscmd_handler(self, event: AstrMessageEvent):
        msg = event.get_message_str().strip()
        
        # 详细调试信息
        logger.info(f"🔍 [DEBUG] 拦截器被调用，处理消息: '{msg}'")
        logger.info(f"🔍 [DEBUG] 是否私聊: {event.is_private_chat()}")
        logger.info(f"🔍 [DEBUG] 是否@或唤醒命令: {event.is_at_or_wake_command}")
        logger.info(f"🔍 [DEBUG] 用户权限: {'管理员' if event.is_admin() else '普通用户'}")
        logger.info(f"🔍 [DEBUG] 事件当前状态: 已停止={event.is_stopped()}")
        
        # 检查是否为受限制的系统指令
        is_restricted, matched_format = self.is_restricted_command(msg, event)
        
        logger.info(f"🔍 [DEBUG] 命令检测结果: {is_restricted}")
        logger.info(f"🔍 [DEBUG] 匹配格式: {matched_format}")
        logger.info(f"🔍 [DEBUG] 被拦截的命令列表: {self.blocked_cmds}")
        
        if is_restricted:
            user_info = f"{event.get_sender_name()}({event.get_sender_id()})"
            
            if not event.is_admin():
                logger.info(f"🚫 [INTERCEPT] 检测到非管理员使用受限指令!")
                logger.info(f"🚫 [INTERCEPT] 用户: {user_info} | 原始: '{msg}' | 匹配: '{matched_format}'")
                logger.info(f"🚫 [INTERCEPT] 静默拦截，防止恶意重置和身份探测")
                
                # 静默拦截，不回复任何内容，防止暴露机器人身份
                event.stop_event()
                
                logger.info(f"🚫 [INTERCEPT] 拦截完成，静默处理，事件状态: {event.is_stopped()}")
                return
            else:
                logger.info(f"✅ [ALLOW] 管理员使用系统指令 | 用户: {user_info} | 指令: '{matched_format}'")
        else:
            logger.info(f"🔍 [DEBUG] 非受限指令，继续传播: '{msg}'")
        
        logger.info(f"🔍 [DEBUG] 拦截器处理完成，事件继续传播")

    async def terminate(self):
        logger.info("restrict_syscmd 插件已卸载")
