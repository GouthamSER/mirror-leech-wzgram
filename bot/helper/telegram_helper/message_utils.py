from asyncio import sleep
try:
    from wzgram.errors import FloodWait, RPCError
    try:
        from wzgram.errors import FloodPremiumWait
    except ImportError:
        FloodPremiumWait = FloodWait
    from wzgram.types import Message
    try:
        from wzgram.types import ReplyParameters
    except ImportError:
        ReplyParameters = None
    from wzgram import enums
except ImportError:
    try:
        from pyrogram.errors import FloodWait, RPCError
        try:
            from pyrogram.errors import FloodPremiumWait
        except ImportError:
            FloodPremiumWait = FloodWait
        from pyrogram.types import Message
        try:
            from pyrogram.types import ReplyParameters
        except ImportError:
            ReplyParameters = None
        from pyrogram import enums
    except ImportError:
        from pyrogram.errors import FloodWait
        FloodPremiumWait = FloodWait
        from pyrogram.types import Message
        ReplyParameters = None
        enums = None
        RPCError = Exception
from re import match as re_match
from time import time

from ... import LOGGER, status_dict, task_dict_lock, intervals, DOWNLOAD_DIR
from ...core.config_manager import Config
from ...core.telegram_manager import TgClient
from ..ext_utils.bot_utils import SetInterval
from ..ext_utils.exceptions import TgLinkException
from ..ext_utils.status_utils import get_readable_message


async def _reply_rich(
    self,
    rich_message,
    disable_notification=True,
    reply_markup=None,
    quote=True,
    **kwargs,
):
    client = getattr(self, "_client", None) or TgClient.bot
    reply_params = None
    if quote and ReplyParameters is not None:
        try:
            reply_params = ReplyParameters(message_id=self.id)
        except Exception:
            pass
    if hasattr(client, "send_rich_message"):
        try:
            return await client.send_rich_message(
                chat_id=self.chat.id,
                rich_text=rich_message,
                reply_parameters=reply_params,
                disable_notification=disable_notification,
                reply_markup=reply_markup,
                message_thread_id=getattr(self, "message_thread_id", None),
                **kwargs,
            )
        except Exception as err:
            if reply_params is not None and ("REPLY" in str(err) or "MESSAGE_ID" in str(err)):
                return await client.send_rich_message(
                    chat_id=self.chat.id,
                    rich_text=rich_message,
                    disable_notification=disable_notification,
                    reply_markup=reply_markup,
                    message_thread_id=getattr(self, "message_thread_id", None),
                    **kwargs,
                )
            raise err
    html_text = (
        getattr(rich_message, "html", None)
        or getattr(rich_message, "markdown", None)
        or str(rich_message)
    )
    parse_mode = getattr(enums, "ParseMode", None) if enums else None
    return await client.send_message(
        chat_id=self.chat.id,
        text=html_text,
        reply_parameters=reply_params,
        disable_notification=disable_notification,
        reply_markup=reply_markup,
        message_thread_id=getattr(self, "message_thread_id", None),
        parse_mode=parse_mode.HTML if parse_mode else None,
        **kwargs,
    )


Message.reply_rich = _reply_rich
Message.rich_message = None

_orig_message_edit = getattr(Message, "edit", None)


async def _message_edit(self, text=None, *args, rich_message=None, **kwargs):
    if rich_message is not None:
        client = getattr(self, "_client", None) or TgClient.bot
        reply_markup = kwargs.get("reply_markup")
        if hasattr(client, "edit_message_text"):
            try:
                return await client.edit_message_text(
                    chat_id=self.chat.id,
                    message_id=self.id,
                    text="",
                    rich_text=rich_message,
                    reply_markup=reply_markup,
                )
            except Exception:
                pass
        html_text = (
            getattr(rich_message, "html", None)
            or getattr(rich_message, "markdown", None)
            or str(rich_message)
        )
        parse_mode = getattr(enums, "ParseMode", None) if enums else None
        return await client.edit_message_text(
            chat_id=self.chat.id,
            message_id=self.id,
            text=html_text,
            reply_markup=reply_markup,
            parse_mode=parse_mode.HTML if parse_mode else None,
        )
    if _orig_message_edit:
        return await _orig_message_edit(self, text, *args, **kwargs)
    return await self.edit_text(text, *args, **kwargs)


Message.edit = _message_edit


async def send_message(message, text, buttons=None, block=True):
    try:
        return await message.reply(
            text=text,
            disable_notification=True,
            reply_markup=buttons,
        )
    except FloodWait as f:
        LOGGER.warning(str(f))
        if not block:
            return str(f)
        await sleep(f.value * 1.2)
        return await send_message(message, text, buttons, block)
    except Exception as e:
        LOGGER.error(str(e))
        return str(e)


async def send_rich_message(message, rich_input, buttons=None, block=True):
    try:
        client = getattr(message, "_client", None) or TgClient.bot
        chat_id = message.chat.id
        msg_id = message.id
        thread_id = getattr(message, "message_thread_id", None)

        reply_params = None
        if ReplyParameters is not None:
            try:
                reply_params = ReplyParameters(message_id=msg_id)
            except Exception:
                pass

        if hasattr(client, "send_rich_message"):
            try:
                return await client.send_rich_message(
                    chat_id=chat_id,
                    rich_text=rich_input,
                    reply_parameters=reply_params,
                    disable_notification=True,
                    reply_markup=buttons,
                    message_thread_id=thread_id,
                )
            except Exception as err:
                if reply_params is not None and ("REPLY" in str(err) or "MESSAGE_ID" in str(err)):
                    return await client.send_rich_message(
                        chat_id=chat_id,
                        rich_text=rich_input,
                        disable_notification=True,
                        reply_markup=buttons,
                        message_thread_id=thread_id,
                    )
                raise err

        html_text = (
            getattr(rich_input, "html", None)
            or getattr(rich_input, "markdown", None)
            or str(rich_input)
        )
        parse_mode = getattr(enums, "ParseMode", None) if enums else None
        return await client.send_message(
            chat_id=chat_id,
            text=html_text,
            reply_parameters=reply_params,
            disable_notification=True,
            reply_markup=buttons,
            message_thread_id=thread_id,
            parse_mode=parse_mode.HTML if parse_mode else None,
        )
    except FloodWait as f:
        LOGGER.warning(str(f))
        if not block:
            return str(f)
        await sleep(f.value * 1.2)
        return await send_rich_message(message, rich_input, buttons, block)
    except Exception as e:
        LOGGER.error(str(e))
        return str(e)


async def edit_message(message, text=None, buttons=None, block=True, rich_message=None):
    try:
        client = getattr(message, "_client", None) or TgClient.bot
        chat_id = message.chat.id
        msg_id = message.id

        if rich_message is not None:
            if hasattr(client, "edit_message_text"):
                try:
                    return await client.edit_message_text(
                        chat_id=chat_id,
                        message_id=msg_id,
                        text="",
                        rich_text=rich_message,
                        reply_markup=buttons,
                    )
                except Exception as err:
                    LOGGER.debug(f"edit_message rich_text error: {err}")
            html_text = (
                getattr(rich_message, "html", None)
                or getattr(rich_message, "markdown", None)
                or str(rich_message)
            )
            parse_mode = getattr(enums, "ParseMode", None) if enums else None
            return await client.edit_message_text(
                chat_id=chat_id,
                message_id=msg_id,
                text=html_text,
                reply_markup=buttons,
                parse_mode=parse_mode.HTML if parse_mode else None,
            )

        if text is not None:
            return await message.edit_text(
                text=text,
                reply_markup=buttons,
            )
        elif buttons is not None:
            return await message.edit_reply_markup(
                reply_markup=buttons,
            )
        return message
    except FloodWait as f:
        LOGGER.warning(str(f))
        if not block:
            return str(f)
        await sleep(f.value * 1.2)
        return await edit_message(message, text, buttons, block, rich_message)
    except Exception as e:
        LOGGER.error(str(e))
        return str(e)


async def send_file(message, file, caption=""):
    try:
        return await message.reply_document(
            document=file, caption=caption, disable_notification=True
        )
    except FloodWait as f:
        LOGGER.warning(str(f))
        await sleep(f.value * 1.2)
        return await send_file(message, file, caption)
    except Exception as e:
        LOGGER.error(str(e))
        return str(e)


async def send_rss(text, chat_id, thread_id):
    try:
        return await TgClient.bot.send_message(
            chat_id=chat_id,
            text=text,
            message_thread_id=thread_id,
            disable_notification=True,
        )
    except (FloodWait, FloodPremiumWait) as f:
        LOGGER.warning(str(f))
        await sleep(f.value * 1.2)
        return await send_rss(text, chat_id, thread_id)
    except Exception as e:
        LOGGER.error(str(e))
        return str(e)


async def delete_message(message):
    try:
        await message.delete()
    except Exception as e:
        LOGGER.error(str(e))


async def auto_delete_message(cmd_message=None, bot_message=None):
    await sleep(60)
    if cmd_message is not None:
        await delete_message(cmd_message)
    if bot_message is not None:
        await delete_message(bot_message)


async def delete_status():
    async with task_dict_lock:
        for key, data in list(status_dict.items()):
            try:
                await delete_message(data["message"])
                del status_dict[key]
            except Exception as e:
                LOGGER.error(str(e))


async def get_tg_link_message(link):
    message = None
    links = []
    if link.startswith("https://t.me/"):
        private = False
        msg = re_match(
            r"https:\/\/t\.me\/(?:c\/)?([^\/]+)\/(?:\d+\/)*([0-9-]+)",
            link,
        )
    else:
        private = True
        msg = re_match(
            r"tg:\/\/openmessage\?user_id=([0-9]+)&message_id=([0-9-]+)", link
        )
        if not TgClient.user:
            raise TgLinkException("USER_SESSION_STRING required for this private link!")
    if not msg:
        raise TgLinkException("Wrong link format!")
    chat = msg[1]
    msg_id = msg[2]
    if "-" in msg_id:
        start_id, end_id = msg_id.split("-")
        msg_id = start_id = int(start_id)
        end_id = int(end_id)
        btw = end_id - start_id
        if private:
            link = link.split("&message_id=")[0]
            links.append(f"{link}&message_id={start_id}")
            for _ in range(btw):
                start_id += 1
                links.append(f"{link}&message_id={start_id}")
        else:
            link = link.rsplit("/", 1)[0]
            links.append(f"{link}/{start_id}")
            for _ in range(btw):
                start_id += 1
                links.append(f"{link}/{start_id}")
    else:
        msg_id = int(msg_id)

    if chat.isdigit():
        chat = int(chat) if private else int(f"-100{chat}")

    if not private:
        try:
            message = await TgClient.bot.get_messages(chat_id=chat, message_ids=msg_id)
            if message.empty:
                private = True
        except Exception as e:
            private = True
            if not TgClient.user:
                raise e

    if not private:
        return (links, "bot") if links else (message, "bot")
    elif TgClient.user:
        try:
            user_message = await TgClient.user.get_messages(
                chat_id=chat, message_ids=msg_id
            )
        except Exception as e:
            raise TgLinkException(
                f"You don't have access to this chat!. ERROR: {e}"
            ) from e
        if not user_message.empty:
            return (links, "user") if links else (user_message, "user")
        else:
            raise TgLinkException("Private: Can't get this message!")
    else:
        raise TgLinkException("Private: Can't get this message!")


async def temp_download(msg):
    path = f"{DOWNLOAD_DIR}temp"
    return await msg.download(file_name=f"{path}/")


async def update_status_message(sid, force=False):
    if intervals["stopAll"]:
        return
    async with task_dict_lock:
        if not status_dict.get(sid):
            if obj := intervals["status"].get(sid):
                obj.cancel()
                del intervals["status"][sid]
            return
        if not force and time() - status_dict[sid]["time"] < 3:
            return
        status_dict[sid]["time"] = time()
        page_no = status_dict[sid]["page_no"]
        status = status_dict[sid]["status"]
        is_user = status_dict[sid]["is_user"]
        page_step = status_dict[sid]["page_step"]
        text, buttons = await get_readable_message(
            sid, is_user, page_no, status, page_step
        )
        if text is None:
            del status_dict[sid]
            if obj := intervals["status"].get(sid):
                obj.cancel()
                del intervals["status"][sid]
            return
        if text != status_dict[sid]["message"].text:
            message = await edit_message(
                status_dict[sid]["message"],
                None,
                buttons,
                block=False,
                rich_message=text,
            )
            if isinstance(message, str):
                if message.startswith("Telegram says: [40"):
                    del status_dict[sid]
                    if obj := intervals["status"].get(sid):
                        obj.cancel()
                        del intervals["status"][sid]
                else:
                    LOGGER.error(
                        f"Status with id: {sid} haven't been updated. Error: {message}"
                    )
                return
            status_dict[sid]["message"].text = text
            status_dict[sid]["time"] = time()


async def send_status_message(msg, user_id=0):
    if intervals["stopAll"]:
        return
    sid = user_id or msg.chat.id
    is_user = bool(user_id)
    async with task_dict_lock:
        if sid in status_dict:
            page_no = status_dict[sid]["page_no"]
            status = status_dict[sid]["status"]
            page_step = status_dict[sid]["page_step"]
            text, buttons = await get_readable_message(
                sid, is_user, page_no, status, page_step
            )
            if text is None:
                del status_dict[sid]
                if obj := intervals["status"].get(sid):
                    obj.cancel()
                    del intervals["status"][sid]
                return
            old_message = status_dict[sid]["message"]
            message = await send_rich_message(msg, text, buttons, block=False)
            if isinstance(message, str):
                LOGGER.error(
                    f"Status with id: {sid} haven't been sent. Error: {message}"
                )
                return
            await delete_message(old_message)
            message.text = text
            status_dict[sid].update({"message": message, "time": time()})
        else:
            text, buttons = await get_readable_message(sid, is_user)
            if text is None:
                return
            message = await send_rich_message(msg, text, buttons, block=False)
            if isinstance(message, str):
                LOGGER.error(
                    f"Status with id: {sid} haven't been sent. Error: {message}"
                )
                return
            message.text = text
            status_dict[sid] = {
                "message": message,
                "time": time(),
                "page_no": 1,
                "page_step": 1,
                "status": "All",
                "is_user": is_user,
            }
        if not intervals["status"].get(sid) and not is_user:
            intervals["status"][sid] = SetInterval(
                Config.STATUS_UPDATE_INTERVAL, update_status_message, sid
            )
