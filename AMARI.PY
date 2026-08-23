import asyncio
import os
import json
from datetime import datetime
from splusthon import SoroushClient, events
from splusthon.sessions import StringSession
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import pyfiglet
from colorama import init, Fore, Style

# ========== Rah Andazi ==========
init(autoreset=True)
console = Console()

# ========== Settings ==========
TEAM_NAME = "AMARI"
BOT_VERSION = "VIP SELF"

# ========== Banner ==========
def show_banner():
    os.system('clear')
    banner = pyfiglet.figlet_format("AMARI", font="slant", width=100)
    console.print(Panel(banner, border_style="bright_blue", title=f"[bold yellow]🔥 {TEAM_NAME} 🔥", width=80))
    console.print(f"[bold green]✔[/] [bold white]{BOT_VERSION} - Robot Professional Spam, Reply, Forward and Clean[/]", justify="center")
    console.print("[bold yellow]" + "="*56 + "[/]")

# ========== Settings ==========
PHONE_NUMBER = "989********"
SESSION_FILE = "session.txt"
TEXTS_FILE = "texts_config.json"
ALLOWED_GROUPS = []

# ========== Text Manager ==========
def load_texts():
    default = {
        "spam": [],
        "reply": [],
        "delete_reply": "🚨 Message deleted!\n👤 Name: {user_name}\n🆔 ID: {user_id}\n👤 Username: {username}\n📝 Msg ID: {msg_id}\n📄 Text: {text}",
        "edit_reply": "✏️ Message edited!\n👤 Name: {user_name}\n🆔 ID: {user_id}\n👤 Username: {username}\n📝 Msg ID: {msg_id}\n📄 New Text: {text}"
    }
    if os.path.exists(TEXTS_FILE):
        try:
            with open(TEXTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for key in default:
                    if key not in data:
                        data[key] = default[key]
                return data
        except:
            return default
    return default

def save_texts(data):
    with open(TEXTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===================================
if os.path.exists(SESSION_FILE):
    try:
        with open(SESSION_FILE, "r") as f:
            session_string = f.read().strip()
        if session_string:
            session = StringSession(session_string)
            console.print("[bold green]✅ Session found![/]")
        else:
            session = StringSession()
            console.print("[bold yellow]🆕 New session created![/]")
    except:
        session = StringSession()
        console.print("[bold yellow]🆕 New session created![/]")
else:
    session = StringSession()
    console.print("[bold yellow]🆕 New session created![/]")

client = SoroushClient(session)

saved_message = None
forward_tasks = {}
spam_tasks = {}
spam_configs = {}
reply_tasks = {}
reply_configs = {}
texts = load_texts()

stats = {
    'spam': 0,
    'forward': 0,
    'reply': 0,
    'total': 0
}

sent_messages = []
user_cache = {}

def is_group_allowed(chat_id):
    if not ALLOWED_GROUPS:
        return True
    return chat_id in ALLOWED_GROUPS

@client.on(events.NewMessage)
async def cache_user_info(event):
    try:
        if event.sender_id and event.sender_id not in user_cache:
            try:
                user = await client.get_entity(event.sender_id)
                username = f"@{user.username}" if user.username else "nadarad"
                user_cache[event.sender_id] = {
                    'name': user.first_name or str(event.sender_id),
                    'id': event.sender_id,
                    'username': username
                }
            except:
                user_cache[event.sender_id] = {
                    'name': str(event.sender_id),
                    'id': event.sender_id,
                    'username': "nadarad"
                }
    except:
        pass

# ========== Message Deleted ==========
@client.on(events.MessageDeleted)
async def on_delete(event):
    try:
        if not is_group_allowed(event.chat_id):
            return
        if event.deleted_id and event.chat_id:
            deleted_msg = None
            try:
                deleted_msg = await client.get_messages(event.chat_id, ids=event.deleted_id)
            except:
                pass
            if not deleted_msg:
                try:
                    history = await client.get_messages(event.chat_id, limit=100)
                    for msg in history:
                        if msg.id == event.deleted_id:
                            deleted_msg = msg
                            break
                except:
                    pass
            if deleted_msg:
                me = await client.get_me()
                if deleted_msg.sender_id == me.id:
                    return
                sender_id = deleted_msg.sender_id
                if sender_id in user_cache:
                    info = user_cache[sender_id]
                else:
                    try:
                        user = await client.get_entity(sender_id)
                        username = f"@{user.username}" if user.username else "nadarad"
                        info = {
                            'name': user.first_name or str(sender_id),
                            'id': sender_id,
                            'username': username
                        }
                        user_cache[sender_id] = info
                    except:
                        info = {
                            'name': str(sender_id),
                            'id': sender_id,
                            'username': "nadarad"
                        }
                        user_cache[sender_id] = info
                reply_text = texts.get("delete_reply").format(
                    user_id=info['id'],
                    user_name=info['name'],
                    username=info['username'],
                    msg_id=deleted_msg.id,
                    text=deleted_msg.text or "Message without text"
                )
                await client.send_message(event.chat_id, reply_text, reply_to=event.deleted_id)
                await client.send_message("me", f"🗑️ Deleted in group {event.chat_id}:\n{reply_text}")
                console.print(f"[bold red]🗑️[/] Reply to delete for [bold cyan]{info['name']}[/]")
    except Exception as e:
        console.print(f"[bold red]❌ Error in on_delete: {e}[/]")

# ========== Message Edited ==========
@client.on(events.MessageEdited)
async def on_edit(event):
    try:
        if not is_group_allowed(event.chat_id):
            return
        me = await client.get_me()
        if event.sender_id == me.id:
            return
        sender_id = event.sender_id
        if sender_id in user_cache:
            info = user_cache[sender_id]
        else:
            try:
                user = await client.get_entity(sender_id)
                username = f"@{user.username}" if user.username else "nadarad"
                info = {
                    'name': user.first_name or str(sender_id),
                    'id': sender_id,
                    'username': username
                }
                user_cache[sender_id] = info
            except:
                info = {
                    'name': str(sender_id),
                    'id': sender_id,
                    'username': "nadarad"
                }
                user_cache[sender_id] = info
        reply_text = texts.get("edit_reply").format(
            user_id=info['id'],
            user_name=info['name'],
            username=info['username'],
            msg_id=event.id,
            text=event.message.text or "Message without text"
        )
        await client.send_message(event.chat_id, reply_text, reply_to=event.id)
        await client.send_message("me", f"✏️ Edited in group {event.chat_id}:\n{reply_text}")
        console.print(f"[bold yellow]✏️[/] Reply to edit for [bold cyan]{info['name']}[/]")
    except Exception as e:
        console.print(f"[bold red]❌ Error in on_edit: {e}[/]")

# ========== Commands ==========
@client.on(events.NewMessage)
async def handler(event):
    global saved_message, stats, sent_messages, texts, ALLOWED_GROUPS
    
    chat_id = event.chat_id
    text = event.message.text or ""
    
    try:
        me = await client.get_me()
        if event.sender_id != me.id:
            return
    except:
        pass
    
    console.print(f"[bold blue]📩[/] [bold white]{text}[/]")
    
    if text == "/help":
        await event.reply("""
🔥 AMARI PANEL - VIP SELF

📝 Set Texts:
/setspam [text1] | [text2] - Spam Text
/setreply [text1] | [text2] - Reply Text
/showtexts - Show Current Texts

🚀 Main Operations:
/start [count] [time] - Start Spam
/reply [count] [time] - Start Reply (Reply to a message)
/setfor - Save message for forward (Reply to a message)
/for [count] [time] - Start Forward

🛑 Control Operations:
/stop - Stop All
/stopspam - Stop Spam
/stopreply - Stop Reply
/stopfor - Stop Forward

🗑️ Message Management:
/deletetex - Delete Bot Messages
/deletetex all - Delete All Messages

📊 Stats and Info:
/stats - Show Stats
/showgroups - Show Allowed Groups

⚙️ Group Settings:
/setgroup - Set Current Group as Allowed

💡 Important Tips:
• For /reply and /setfor, reply to a message.
• Time is in seconds (e.g., 0.5 or 1).
• Count 0 means Unlimited.
• Use | for multiple texts.

🔥 AMARI PANEL
    """)
        return
    
    elif text == "/setgroup":
        group_id = chat_id
        if group_id not in ALLOWED_GROUPS:
            ALLOWED_GROUPS.append(group_id)
            await event.reply(f"✅ Group added!\n📌 ID: {group_id}")
            console.print(f"[bold green]✅[/] Group [bold cyan]{group_id}[/] added!")
        else:
            await event.reply(f"⚠️ Group already added!")
        return
    
    elif text == "/showgroups":
        if ALLOWED_GROUPS:
            await event.reply(f"📋 Allowed Groups:\n{ALLOWED_GROUPS}")
        else:
            await event.reply("📋 No groups set!")
        return
    
    elif text.startswith("/setspam"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await event.reply("❌ /setspam [text1] | [text2]")
            return
        try:
            new_texts = [t.strip() for t in parts[1].split("|") if t.strip()]
            if not new_texts:
                await event.reply("❌ At least 1 text")
                return
            texts['spam'] = new_texts
            save_texts(texts)
            await event.reply(f"✅ {len(new_texts)} Spam texts")
        except Exception as e:
            await event.reply(f"❌ {e}")
        return
    
    elif text.startswith("/setreply"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await event.reply("❌ /setreply [text1] | [text2]")
            return
        try:
            new_texts = [t.strip() for t in parts[1].split("|") if t.strip()]
            if not new_texts:
                await event.reply("❌ At least 1 text")
                return
            texts['reply'] = new_texts
            save_texts(texts)
            await event.reply(f"✅ {len(new_texts)} Reply texts")
        except Exception as e:
            await event.reply(f"❌ {e}")
        return
    
    elif text == "/showtexts":
        msg = "📋 Texts:\n"
        msg += f"🔹 Spam: {', '.join(texts['spam']) if texts['spam'] else 'Not set'}\n"
        msg += f"🔹 Reply: {', '.join(texts['reply']) if texts['reply'] else 'Not set'}"
        await event.reply(msg)
        return
    
    elif text == "/stats":
        await event.reply(f"""
📊 Stats:
📨 Spam: {stats['spam']}
🔄 Forward: {stats['forward']}
💬 Reply: {stats['reply']}
━━━━━━━━━━━━━━━
📌 Total: {stats['total']}
        """)
        return
    
    elif text.startswith("/deletetex"):
        if not sent_messages:
            await event.reply("❌ No messages!")
            return
        parts = text.split()
        all_mode = len(parts) > 1 and parts[1].lower() == "all"
        total = len(sent_messages)
        msg = await event.reply(f"🗑️ Deleting {total} messages..." + (" ⚡" if all_mode else ""))
        deleted_count = 0
        if all_mode:
            chunk_size = 10
            for i in range(0, len(sent_messages), chunk_size):
                chunk = sent_messages[i:i+chunk_size]
                try:
                    await client.delete_messages(chat_id, chunk)
                    deleted_count += len(chunk)
                except:
                    for mid in chunk:
                        try:
                            await client.delete_messages(chat_id, mid)
                            deleted_count += 1
                        except:
                            pass
        else:
            for mid in sent_messages:
                try:
                    await client.delete_messages(chat_id, mid)
                    deleted_count += 1
                except:
                    pass
        sent_messages = []
        stats = {'spam': 0, 'forward': 0, 'reply': 0, 'total': 0}
        await msg.edit(f"✅ {deleted_count} messages deleted!")
        return
    
    elif text == "/setfor":
        if not event.message.reply_to_msg_id:
            await event.reply("❌ Reply to a message!")
            return
        try:
            msg_id = event.message.reply_to_msg_id
            replied = await client.get_messages(chat_id, ids=msg_id)
            if replied:
                saved_message = {'chat_id': chat_id, 'msg_id': msg_id}
                await event.reply(f"✅ Message saved!")
        except Exception as e:
            await event.reply(f"❌ {e}")
        return
    
    elif text.startswith("/reply"):
        if not event.message.reply_to_msg_id:
            await event.reply("❌ Reply to a message!")
            return
        if not texts['reply']:
            await event.reply("❌ No texts set!")
            return
        parts = text.split()
        count, delay = 5, 0.5
        try:
            if len(parts) >= 2:
                count = int(parts[1])
            if len(parts) >= 3:
                delay = float(parts[2])
        except:
            await event.reply("❌ /reply [count] [time]")
            return
        target = event.message.reply_to_msg_id
        reply_configs[chat_id] = {
            'target_msg_id': target,
            'texts': texts['reply'],
            'count': count,
            'delay': delay if delay > 0 else 0.1
        }
        if chat_id in reply_tasks:
            reply_tasks[chat_id].cancel()
        reply_tasks[chat_id] = asyncio.create_task(reply_loop(chat_id))
        await event.reply(f"✅ Reply started! {count} {delay}")
        return
    
    elif text.startswith("/start"):
        if not texts['spam']:
            await event.reply("❌ No texts set!")
            return
        parts = text.split()
        count, delay = 10, 0.01
        try:
            if len(parts) >= 2:
                count = int(parts[1])
            if len(parts) >= 3:
                delay = float(parts[2])
        except:
            await event.reply("❌ /start [count] [time]")
            return
        spam_configs[chat_id] = {
            'texts': texts['spam'],
            'count': count,
            'delay': delay if delay > 0 else 0.01
        }
        if chat_id in spam_tasks:
            spam_tasks[chat_id].cancel()
        spam_tasks[chat_id] = asyncio.create_task(spam_loop(chat_id))
        await event.reply(f"✅ Spam started! {count} {delay}")
        return
    
    elif text.startswith("/for"):
        if saved_message is None:
            await event.reply("❌ First use /setfor!")
            return
        parts = text.split()
        try:
            count = int(parts[1]) if len(parts) > 1 else 5
            delay = float(parts[2]) if len(parts) > 2 else 0.01
        except:
            await event.reply("❌ /for [count] [time]")
            return
        if chat_id in forward_tasks:
            forward_tasks[chat_id].cancel()
        forward_tasks[chat_id] = asyncio.create_task(forward_loop(chat_id, count, delay))
        await event.reply(f"✅ Forward started! {count} {delay}")
        return
    
    elif text == "/stop":
        stopped = False
        if chat_id in spam_tasks and not spam_tasks[chat_id].done():
            spam_tasks[chat_id].cancel(); stopped = True
        if chat_id in forward_tasks and not forward_tasks[chat_id].done():
            forward_tasks[chat_id].cancel(); stopped = True
        if chat_id in reply_tasks and not reply_tasks[chat_id].done():
            reply_tasks[chat_id].cancel(); stopped = True
        await event.reply("⛔ Stopped!" if stopped else "⚠️ Nothing running!")
        return
    
    elif text == "/stopspam":
        if chat_id in spam_tasks and not spam_tasks[chat_id].done():
            spam_tasks[chat_id].cancel()
            await event.reply("⛔ Spam stopped!")
        else:
            await event.reply("⚠️ Not running!")
        return
    
    elif text == "/stopreply":
        if chat_id in reply_tasks and not reply_tasks[chat_id].done():
            reply_tasks[chat_id].cancel()
            await event.reply("⛔ Reply stopped!")
        else:
            await event.reply("⚠️ Not running!")
        return
    
    elif text == "/stopfor":
        if chat_id in forward_tasks and not forward_tasks[chat_id].done():
            forward_tasks[chat_id].cancel()
            await event.reply("⛔ Forward stopped!")
        else:
            await event.reply("⚠️ Not running!")
        return

async def spam_loop(chat_id):
    global stats, sent_messages
    config = spam_configs.get(chat_id)
    if not config: return
    count, texts_list, delay = config['count'], config['texts'], config['delay']
    i = 0
    while True:
        try:
            i += 1
            msg = await client.send_message(chat_id, texts_list[i % len(texts_list)])
            sent_messages.append(msg.id)
            stats['spam'] += 1
            stats['total'] += 1
            await asyncio.sleep(delay)
            if count > 0 and i >= count:
                break
        except asyncio.CancelledError:
            break
        except Exception as e:
            console.print(f"[bold red]❌ {e}[/]")
            await asyncio.sleep(1)
    if chat_id in spam_tasks:
        del spam_tasks[chat_id]

async def reply_loop(chat_id):
    global stats, sent_messages
    config = reply_configs.get(chat_id)
    if not config: return
    count, target, texts_list, delay = config['count'], config['target_msg_id'], config['texts'], config['delay']
    i = 0
    while True:
        try:
            i += 1
            msg = await client.send_message(chat_id, texts_list[i % len(texts_list)], reply_to=target)
            sent_messages.append(msg.id)
            stats['reply'] += 1
            stats['total'] += 1
            await asyncio.sleep(delay)
            if count > 0 and i >= count:
                break
        except asyncio.CancelledError:
            break
        except Exception as e:
            console.print(f"[bold red]❌ {e}[/]")
            await asyncio.sleep(1)
    if chat_id in reply_tasks:
        del reply_tasks[chat_id]

async def forward_loop(chat_id, count, delay):
    global stats, sent_messages, saved_message
    i = 0
    while True:
        try:
            i += 1
            msg = await client.forward_messages(chat_id, saved_message['msg_id'], saved_message['chat_id'])
            if hasattr(msg, 'id'):
                sent_messages.append(msg.id)
            stats['forward'] += 1
            stats['total'] += 1
            await asyncio.sleep(delay)
            if count > 0 and i >= count:
                break
        except asyncio.CancelledError:
            break
        except Exception as e:
            console.print(f"[bold red]❌ {e}[/]")
            await asyncio.sleep(1)
    if chat_id in forward_tasks:
        del forward_tasks[chat_id]

async def keep_alive():
    while True:
        try:
            await asyncio.sleep(30)
            await client.send_message(PHONE_NUMBER, "🔄")
        except:
            await asyncio.sleep(10)

async def main():
    show_banner()
    console.print("[bold green]🚀 Connecting...[/]")
    try:
        await client.start(phone=PHONE_NUMBER)
        with open(SESSION_FILE, "w") as f:
            f.write(client.session.save())
        me = await client.get_me()
        console.print(f"[bold green]👤[/] [bold cyan]{me.id}[/]")
        console.print(f"[bold green]📱[/] [bold cyan]{me.phone}[/]")
        console.print("[bold green]✅ Robot Ready![/]")
    except Exception as e:
        console.print(f"[bold red]❌ {e}[/]")
        return
    console.print("[bold yellow]🔥 Online! /help[/]")
    asyncio.create_task(keep_alive())
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold red]⛔ Stopped![/]")