import requests
import re
import logging
import asyncio
import aiohttp
import json
from pathlib import Path
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler,
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Константы для состояний разговора
(LANGUAGE_SELECT, MAIN_MENU, UPLOAD_LINKS, UPLOAD_PRICE, CHECK_ITEMS, 
 SELECT_DURATION, SELECT_COUNT, SELECT_UPLOAD_DURATION, SETTINGS_MENU,
 CHANGE_CURRENCY, CHANGE_ORIGIN) = range(11)

# Маппинг месяцев на дни
DURATION_MAPPING = {
    "3_months": 90,
    "6_months": 180,
    "12_months": 360
}


class ConfigManager:
    """Менеджер конфигурации"""
    
    def __init__(self):
        self.config_file = Path('bot_config.json')
        self.translations_file = Path('translations.json')
        self.user_data_file = Path('user_data.json')
        self.config = self.load_config()
        self.translations = self.load_translations()
        self.user_data = self.load_user_data()
    
    def load_config(self):
        """Загрузка конфигурации"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file {self.config_file} not found!")
            return {}
    
    def load_translations(self):
        """Загрузка переводов"""
        try:
            with open(self.translations_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Translations file {self.translations_file} not found!")
            return {}
    
    def load_user_data(self):
        """Загрузка данных пользователей"""
        try:
            with open(self.user_data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"users": {}}
    
    def save_user_data(self):
        """Сохранение данных пользователей"""
        with open(self.user_data_file, 'w', encoding='utf-8') as f:
            json.dump(self.user_data, f, ensure_ascii=False, indent=4)
    
    def save_config(self):
        """Сохранение конфигурации"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)
    
    def get_user_language(self, user_id: str) -> str:
        """Получить язык пользователя"""
        return self.user_data.get("users", {}).get(str(user_id), {}).get("language", "ru")
    
    def set_user_language(self, user_id: str, language: str):
        """Установить язык пользователя"""
        if "users" not in self.user_data:
            self.user_data["users"] = {}
        if str(user_id) not in self.user_data["users"]:
            self.user_data["users"][str(user_id)] = {}
        self.user_data["users"][str(user_id)]["language"] = language
        self.save_user_data()
    
    def get_translation(self, user_id: str, key: str, **kwargs) -> str:
        """Получить перевод для пользователя"""
        lang = self.get_user_language(user_id)
        text = self.translations.get(lang, {}).get(key, self.translations.get("ru", {}).get(key, key))
        return text.format(**kwargs) if kwargs else text
    
    def get_currency(self) -> str:
        """Получить текущую валюту"""
        return self.config.get("product_settings", {}).get("currency", "rub")
    
    def set_currency(self, currency: str):
        """Установить валюту"""
        if "product_settings" not in self.config:
            self.config["product_settings"] = {}
        self.config["product_settings"]["currency"] = currency
        self.save_config()
    
    def get_origin(self) -> str:
        """Получить текущее происхождение"""
        return self.config.get("product_settings", {}).get("item_origin", "personal")
    
    def set_origin(self, origin: str):
        """Установить происхождение"""
        if "product_settings" not in self.config:
            self.config["product_settings"] = {}
        self.config["product_settings"]["item_origin"] = origin
        self.save_config()


class LZTMarketBot:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        config = config_manager.config
        
        self.lzt_token = config["api_tokens"]["lzt_token"]
        self.user_id = config["api_tokens"]["user_id"]
        self.base_url = "https://prod-api.lzt.market"
        
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {self.lzt_token}"
        }
    
    def get_payload_template(self):
        """Получить шаблон payload с текущими настройками"""
        settings = self.config_manager.config.get("product_settings", {})
        return {
            "category_id": settings.get("category_id", 30),
            "currency": settings.get("currency", "rub"),
            "item_origin": settings.get("item_origin", "personal"),
            "title": "",
            "title_en": "",
            "price": 0,
            "allow_ask_discount": settings.get("allow_ask_discount", False),
            "description": settings.get("description", ""),
            "login": "0",
            "extra": settings.get("extra", {"service": "telegram"})
        }
    
    def normalize_link(self, link: str) -> str:
        """Нормализация ссылки к формату https://t.me/giftcode/..."""
        match = re.search(r't\.me/giftcode/([a-zA-Z0-9_-]+)', link)
        if match:
            code = match.group(1)
            return f"https://t.me/giftcode/{code}"
        return link
    
    def extract_links(self, text: str) -> list:
        """Извлечение всех ссылок из текста"""
        links = re.findall(r'(?:https?://)?t\.me/giftcode/[a-zA-Z0-9_-]+', text)
        return [self.normalize_link(link) for link in links]
    
    async def check_if_account_exists(self, session: aiohttp.ClientSession, login: str) -> bool:
        """Проверка существует ли аккаунт уже на маркете"""
        try:
            normalized_login = login.replace("https://t.me/giftcode/", "")
            url = f"{self.base_url}/user/items"
            params = {
                "user_id": self.user_id,
                "category_id": 30
            }
            
            async with session.get(url, params=params, headers=self.headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    items = data.get("items", [])
                    
                    for item in items:
                        item_login = item.get("login", "")
                        if normalized_login in item_login or item_login in normalized_login:
                            return True
            return False
        except Exception as e:
            logger.error(f"Ошибка проверки существования аккаунта: {e}")
            return False
    
    async def upload_account_async(self, session: aiohttp.ClientSession, login: str, price: int, duration_days: int, index: int, max_retries: int = 5) -> dict:
        """Асинхронная загрузка одного аккаунта на LZT Market с повторными попытками"""
        url = f"{self.base_url}/item/fast-sell"
        
        payload = self.get_payload_template()
        payload["login"] = login
        payload["price"] = price
        
        # Получаем заголовки из конфигурации
        title_mapping = self.config_manager.config.get("title_mapping", {})
        titles = title_mapping.get(str(duration_days), {})
        payload["title"] = titles.get("ru", "")
        payload["title_en"] = titles.get("en", "")
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    delay = min(2 ** attempt, 30)
                    logger.info(f"Аккаунт {index}: попытка {attempt + 1}/{max_retries}, задержка {delay}с")
                    await asyncio.sleep(delay)
                
                async with session.post(url, json=payload, headers=self.headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    response_text = await response.text()
                    
                    if response.status in [200, 201]:
                        try:
                            data = await response.json()
                            logger.info(f"Аккаунт {index}: успешно загружен")
                            return {"success": True, "data": data, "status_code": response.status, "index": index, "login": login}
                        except:
                            logger.info(f"Аккаунт {index}: загружен (нет JSON в ответе)")
                            return {"success": True, "data": {"item": {}}, "status_code": response.status, "index": index, "login": login}
                    
                    elif response.status == 429:
                        logger.warning(f"Аккаунт {index}: 429 Too Many Requests, попытка {attempt + 1}/{max_retries}")
                        if attempt == max_retries - 1:
                            return {"success": False, "error": "429 Too Many Requests", "index": index, "detailed_error": response_text, "login": login}
                        continue
                    
                    else:
                        error_message = f"Status {response.status}"
                        try:
                            error_data = await response.json()
                            if "errors" in error_data:
                                errors = error_data["errors"]
                                if isinstance(errors, dict):
                                    error_messages = []
                                    for field, messages in errors.items():
                                        if isinstance(messages, list):
                                            error_messages.extend(messages)
                                        else:
                                            error_messages.append(str(messages))
                                    error_message = "; ".join(error_messages)
                                elif isinstance(errors, list):
                                    error_message = "; ".join(errors)
                                else:
                                    error_message = str(errors)
                            elif "error" in error_data:
                                error_message = error_data["error"]
                            
                            if "уже продается" in error_message.lower() or "already" in error_message.lower():
                                exists = await self.check_if_account_exists(session, login)
                                if exists:
                                    logger.info(f"Аккаунт {index}: пропускаем, уже продается на маркете")
                                    return {"success": False, "error": error_message, "index": index, "login": login, "skip_error": True}
                        except:
                            pass
                        
                        logger.error(f"Аккаунт {index}: Ошибка {response.status} - {error_message}")
                        return {"success": False, "error": error_message, "index": index, "detailed_error": response_text, "login": login}
                        
            except asyncio.TimeoutError:
                logger.error(f"Аккаунт {index}: Таймаут запроса, попытка {attempt + 1}/{max_retries}")
                if attempt == max_retries - 1:
                    return {"success": False, "error": "Таймаут запроса", "index": index, "login": login}
            except Exception as e:
                logger.error(f"Аккаунт {index}: Исключение {str(e)}, попытка {attempt + 1}/{max_retries}")
                if attempt == max_retries - 1:
                    return {"success": False, "error": str(e), "index": index, "login": login}
        
        return {"success": False, "error": "Превышено количество попыток", "index": index, "login": login}
    
    async def upload_accounts_batch(self, links: list, price: int, duration_days: int, batch_size: int = 5) -> list:
        """Загрузка аккаунтов пачками с увеличенными задержками"""
        results = []
        
        async with aiohttp.ClientSession() as session:
            for i in range(0, len(links), batch_size):
                batch = links[i:i + batch_size]
                logger.info(f"Обработка пачки {i//batch_size + 1}: аккаунты {i+1}-{min(i+batch_size, len(links))}")
                
                tasks = [
                    self.upload_account_async(session, link, price, duration_days, i + idx + 1)
                    for idx, link in enumerate(batch)
                ]
                batch_results = await asyncio.gather(*tasks)
                results.extend(batch_results)
                
                if i + batch_size < len(links):
                    delay = 2
                    logger.info(f"Задержка {delay}с перед следующей пачкой")
                    await asyncio.sleep(delay)
        
        return results
    
    def get_user_items(self) -> dict:
        """Получение списка товаров пользователя"""
        url = f"{self.base_url}/user/items"
        params = {
            "user_id": self.user_id,
            "category_id": 30
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers, timeout=30)
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка получения товаров: {e}")
            return {"success": False, "error": str(e)}
    
    async def delete_item_async(self, session: aiohttp.ClientSession, item_id: int, retry_count: int = 5) -> dict:
        """Асинхронное удаление товара с повторными попытками"""
        url = f"{self.base_url}/{item_id}"
        payload = {"reason": "Выдача в телеграм"}
        
        for attempt in range(retry_count):
            try:
                if attempt > 0:
                    delay = min(2 ** attempt, 30)
                    logger.info(f"Удаление {item_id}: попытка {attempt + 1}/{retry_count}, задержка {delay}с")
                    await asyncio.sleep(delay)
                
                async with session.delete(url, json=payload, headers=self.headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status in [200, 204]:
                        logger.info(f"Товар {item_id}: успешно удален")
                        return {"success": True, "item_id": item_id}
                    else:
                        error_text = await response.text()
                        logger.warning(f"Товар {item_id}: статус {response.status}, попытка {attempt + 1}/{retry_count}")
                        
                        if response.status == 429 and attempt < retry_count - 1:
                            continue
                        
                        if attempt == retry_count - 1:
                            return {"success": False, "item_id": item_id, "error": f"Status {response.status}", "detailed_error": error_text}
                            
            except Exception as e:
                logger.warning(f"Товар {item_id}: исключение {str(e)}, попытка {attempt + 1}/{retry_count}")
                if attempt == retry_count - 1:
                    return {"success": False, "item_id": item_id, "error": str(e)}
        
        return {"success": False, "item_id": item_id, "error": "Превышено количество попыток"}
    
    async def delete_items_batch(self, item_ids: list, batch_size: int = 3) -> list:
        """Удаление товаров пачками с задержками"""
        results = []
        
        async with aiohttp.ClientSession() as session:
            for i in range(0, len(item_ids), batch_size):
                batch = item_ids[i:i + batch_size]
                logger.info(f"Удаление пачки {i//batch_size + 1}: товары {i+1}-{min(i+batch_size, len(item_ids))}")
                
                tasks = [
                    self.delete_item_async(session, item_id)
                    for item_id in batch
                ]
                batch_results = await asyncio.gather(*tasks)
                results.extend(batch_results)
                
                if i + batch_size < len(item_ids):
                    delay = 1.5
                    logger.info(f"Задержка {delay}с перед следующей пачкой удаления")
                    await asyncio.sleep(delay)
        
        return results


# Глобальные экземпляры
config_manager = None
bot_instance = None


async def language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Выбор языка при первом запуске"""
    user_id = update.effective_user.id
    
    # Проверяем есть ли уже язык у пользователя
    if config_manager.get_user_language(str(user_id)) != "ru":
        return await start(update, context)
    
    # Если это первый запуск, показываем выбор языка
    keyboard = [
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
         InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇩🇪 Deutsch", callback_data="lang_de"),
         InlineKeyboardButton("🇰🇿 Қазақша", callback_data="lang_kk")],
        [InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_uk"),
         InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh")],
        [InlineKeyboardButton("🇰🇷 한국어", callback_data="lang_ko")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🌐 Select your language / Выберите язык:",
        reply_markup=reply_markup
    )
    return LANGUAGE_SELECT


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Установка языка пользователя"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang_code = query.data.replace("lang_", "")
    
    config_manager.set_user_language(str(user_id), lang_code)
    
    await query.edit_message_text(
        config_manager.get_translation(str(user_id), "language_changed")
    )
    
    return await start_after_language(update, context)


async def start_after_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало работы после выбора языка"""
    user_id = update.effective_user.id
    
    keyboard = [
        [config_manager.get_translation(str(user_id), "upload_accounts")],
        [config_manager.get_translation(str(user_id), "check_items")],
        [config_manager.get_translation(str(user_id), "issue_items")],
        [config_manager.get_translation(str(user_id), "settings")],
        [config_manager.get_translation(str(user_id), "cancel")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.callback_query.message.reply_text(
        config_manager.get_translation(str(user_id), "welcome"),
        reply_markup=reply_markup
    )
    return MAIN_MENU


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало работы с ботом"""
    user_id = update.effective_user.id
    
    # Проверяем установлен ли язык
    if str(user_id) not in config_manager.user_data.get("users", {}):
        return await language_selection(update, context)
    
    keyboard = [
        [config_manager.get_translation(str(user_id), "upload_accounts")],
        [config_manager.get_translation(str(user_id), "check_items")],
        [config_manager.get_translation(str(user_id), "issue_items")],
        [config_manager.get_translation(str(user_id), "settings")],
        [config_manager.get_translation(str(user_id), "cancel")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        config_manager.get_translation(str(user_id), "welcome"),
        reply_markup=reply_markup
    )
    return MAIN_MENU


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка главного меню"""
    user_id = update.effective_user.id
    text = update.message.text
    
    t_upload = config_manager.get_translation(str(user_id), "upload_accounts")
    t_check = config_manager.get_translation(str(user_id), "check_items")
    t_issue = config_manager.get_translation(str(user_id), "issue_items")
    t_settings = config_manager.get_translation(str(user_id), "settings")
    t_cancel = config_manager.get_translation(str(user_id), "cancel")
    
    if text == t_upload:
        keyboard = [
            [config_manager.get_translation(str(user_id), "3_months")],
            [config_manager.get_translation(str(user_id), "6_months")],
            [config_manager.get_translation(str(user_id), "12_months")],
            [config_manager.get_translation(str(user_id), "back")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            config_manager.get_translation(str(user_id), "select_duration"),
            reply_markup=reply_markup
        )
        return SELECT_UPLOAD_DURATION
    
    elif text == t_check:
        return await check_items(update, context)
    
    elif text == t_issue:
        return await select_duration(update, context)
    
    elif text == t_settings:
        return await settings_menu(update, context)
    
    elif text == t_cancel:
        await update.message.reply_text(
            config_manager.get_translation(str(user_id), "goodbye"),
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    return MAIN_MENU


async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Меню настроек"""
    user_id = update.effective_user.id
    
    currency = config_manager.get_currency()
    origin = config_manager.get_origin()
    
    keyboard = [
        [config_manager.get_translation(str(user_id), "change_currency")],
        [config_manager.get_translation(str(user_id), "change_origin")],
        [config_manager.get_translation(str(user_id), "back")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        config_manager.get_translation(str(user_id), "settings_menu", 
                                      currency=currency, origin=origin),
        reply_markup=reply_markup
    )
    return SETTINGS_MENU


async def handle_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка выбора в настройках"""
    user_id = update.effective_user.id
    text = update.message.text
    
    t_currency = config_manager.get_translation(str(user_id), "change_currency")
    t_origin = config_manager.get_translation(str(user_id), "change_origin")
    t_back = config_manager.get_translation(str(user_id), "back")
    
    if text == t_currency:
        currencies = config_manager.config.get("available_currencies", {})
        keyboard = [[curr.upper()] for curr in currencies.keys()]
        keyboard.append([t_back])
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            config_manager.get_translation(str(user_id), "select_currency"),
            reply_markup=reply_markup
        )
        return CHANGE_CURRENCY
    
    elif text == t_origin:
        origins = config_manager.config.get("available_origins", {})
        keyboard = [[value] for value in origins.values()]
        keyboard.append([t_back])
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            config_manager.get_translation(str(user_id), "select_origin"),
            reply_markup=reply_markup
        )
        return CHANGE_ORIGIN
    
    elif text == t_back:
        return await start(update, context)
    
    return SETTINGS_MENU


async def change_currency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Изменение валюты"""
    user_id = update.effective_user.id
    text = update.message.text.lower()
    
    if text == config_manager.get_translation(str(user_id), "back").lower():
        return await settings_menu(update, context)
    
    currencies = config_manager.config.get("available_currencies", {})
    if text in currencies:
        config_manager.set_currency(text)
        await update.message.reply_text(
            config_manager.get_translation(str(user_id), "currency_changed", currency=text.upper())
        )
        return await settings_menu(update, context)
    
    return CHANGE_CURRENCY


async def change_origin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Изменение происхождения"""
    user_id = update.effective_user.id
    text = update.message.text
    
    if text == config_manager.get_translation(str(user_id), "back"):
        return await settings_menu(update, context)
    
    origins = config_manager.config.get("available_origins", {})
    # Находим ключ по значению
    origin_key = None
    for key, value in origins.items():
        if value == text:
            origin_key = key
            break
    
    if origin_key:
        config_manager.set_origin(origin_key)
        await update.message.reply_text(
            config_manager.get_translation(str(user_id), "origin_changed", origin=text)
        )
        return await settings_menu(update, context)
    
    return CHANGE_ORIGIN


# Продолжение следует в следующем сообщении из-за ограничения размера...