import requests
import re
import logging
import asyncio
import aiohttp
import json
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
MAIN_MENU, UPLOAD_LINKS, UPLOAD_PRICE, CHECK_ITEMS, SELECT_DURATION, SELECT_COUNT, SELECT_UPLOAD_DURATION, RETRY_UPLOAD = range(8)

# Маппинг месяцев на дни
DURATION_MAPPING = {
    "3 месяца": 90,
    "6 месяцев": 180,
    "12 месяцев": 360
}

# Маппинг для заголовков
TITLE_MAPPING = {
    90: {
        "ru": "Постоянникам СКИДКИ | Telegram Premium 3 месяца | Ссылкой | Оставьте отзыв",
        "en": "DISCOUNTS for regulars | Telegram Premium 3 months | Link | Leave a review"
    },
    180: {
        "ru": "Постоянникам СКИДКИ | Telegram Premium 6 месяцев | Ссылкой | Оставьте отзыв",
        "en": "DISCOUNTS for regulars | Telegram Premium 6 months | Link | Leave a review"
    },
    360: {
        "ru": "Постоянникам СКИДКИ | Telegram Premium 12 месяцев | Ссылкой | Оставьте отзыв",
        "en": "DISCOUNTS for regulars | Telegram Premium 12 months | Link | Leave a review"
    }
}

class LZTMarketBot:
    def __init__(self, lzt_token: str, user_id: str):
        self.lzt_token = lzt_token
        self.user_id = user_id
        self.base_url = "https://prod-api.lzt.market"
        
        # Оригинальный payload из вашего кода
        self.payload_template = {
            "category_id": 30,
            "currency": "rub",
            "item_origin": "personal",
            "title": "Постоянникам СКИДКИ | Telegram Premium 3 месяца | Ссылкой | Оставьте отзыв",
            "title_en": "DISCOUNTS for regulars | Telegram Premium 3 months | Link | Leave a review",
            "price": 0,
            "allow_ask_discount": False,
            "description": "с розыгрыша  ===== DESCRIPTION ===== After purchase, you will receive a gift link to activate your premium subscription. The subscription was won in a giveaway in one of the Telegram channels. Market automatically checks valid before purchase. The link is 100% valid if you were able to buy it. If you have any difficulties, write to me in private messages on market.  ===== ОПИСАНИЕ ===== После покупки вы получите подарочную ссылку для активации премиум подписки. Подписка была выиграна в розыгрыше в одном из Telegram каналов. Товар автоматически проверяется маркетом на валидность при покупке. Ссылка 100% валидна, если вы смогли её купить. В случае затруднений пишите мне в личные сообщения на маркете.  ЕСЛИ У ВАС ТАКОЕ ОКНО   [url=https://postimg.cc/vDkqbsbC][img]https://i.postimg.cc/wTTS5qPx/image.png[/img][/url]  ИСПОЛЬЗУЙТЕ ЭТОГО БОТА  https://t.me/gifts_activate_echo_bot",
            "login": "0",
            "extra": { "service": "telegram" }
        }
        
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {self.lzt_token}"
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
            # Нормализуем ссылку для поиска
            normalized_login = login.replace("https://t.me/giftcode/", "")
            
            # Получаем список товаров пользователя
            url = f"{self.base_url}/user/items"
            params = {
                "user_id": self.user_id,
                "category_id": 30
            }
            
            async with session.get(url, params=params, headers=self.headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    items = data.get("items", [])
                    
                    # Проверяем есть ли такой login среди товаров
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
        
        # Копируем шаблон и обновляем login, price и заголовки
        payload = self.payload_template.copy()
        payload["login"] = login
        payload["price"] = price
        payload["title"] = TITLE_MAPPING[duration_days]["ru"]
        payload["title_en"] = TITLE_MAPPING[duration_days]["en"]
        
        for attempt in range(max_retries):
            try:
                # Увеличивающаяся задержка перед повторной попыткой
                if attempt > 0:
                    delay = min(2 ** attempt, 30)  # Экспоненциальная задержка, максимум 30 секунд
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
                        # Извлекаем детальную ошибку из JSON
                        error_message = f"Status {response.status}"
                        try:
                            error_data = await response.json()
                            if "errors" in error_data:
                                errors = error_data["errors"]
                                if isinstance(errors, dict):
                                    # Собираем все ошибки из словаря
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
                            
                            # Проверяем специфическую ошибку "уже продается"
                            if "уже продается" in error_message.lower() or "already" in error_message.lower():
                                # Проверяем действительно ли аккаунт существует
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
                    return {"success": False, "error": "Таймаут запроса", "index": index}
            except Exception as e:
                logger.error(f"Аккаунт {index}: Исключение {str(e)}, попытка {attempt + 1}/{max_retries}")
                if attempt == max_retries - 1:
                    return {"success": False, "error": str(e), "index": index}
        
        return {"success": False, "error": "Превышено количество попыток", "index": index}
    
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
                
                # Задержка между пачками для избежания 429
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
                
                # Задержка между пачками
                if i + batch_size < len(item_ids):
                    delay = 1.5
                    logger.info(f"Задержка {delay}с перед следующей пачкой удаления")
                    await asyncio.sleep(delay)
        
        return results


# Глобальный экземпляр бота
bot_instance = None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало работы с ботом"""
    keyboard = [
        ["📤 Загрузить аккаунты"],
        ["📊 Проверить товары"],
        ["📋 Выдать товары"],
        ["❌ Отмена"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "👋 Добро пожаловать в LZT Market Bot!\n\n"
        "⚡ Бот работает в турбо-режиме с автоматическими повторными попытками!\n\n"
        "Выберите действие:",
        reply_markup=reply_markup
    )
    return MAIN_MENU


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка главного меню"""
    text = update.message.text
    
    if text == "📤 Загрузить аккаунты":
        keyboard = [
            ["3 месяца"],
            ["6 месяцев"],
            ["12 месяцев"],
            ["◀️ Назад"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "📅 Выберите длительность подписки для загрузки:",
            reply_markup=reply_markup
        )
        return SELECT_UPLOAD_DURATION
    
    elif text == "📊 Проверить товары":
        return await check_items(update, context)
    
    elif text == "📋 Выдать товары":
        return await select_duration(update, context)
    
    elif text == "❌ Отмена":
        await update.message.reply_text(
            "👋 До свидания!",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    return MAIN_MENU


async def select_upload_duration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Выбор длительности для загрузки"""
    text = update.message.text
    
    if text == "◀️ Назад":
        return await start(update, context)
    
    # Проверяем выбранную длительность
    duration_days = DURATION_MAPPING.get(text)
    
    if not duration_days:
        await update.message.reply_text("❌ Неверная длительность")
        return SELECT_UPLOAD_DURATION
    
    # Сохраняем выбранную длительность
    context.user_data["upload_duration"] = duration_days
    context.user_data["upload_duration_text"] = text
    
    await update.message.reply_text(
        f"✅ Выбрано: {text}\n\n"
        "📝 Отправьте ссылки на аккаунты.\n\n"
        "Вы можете:\n"
        "• Вставить несколько ссылок через пробел\n"
        "• Вставить каждую ссылку с новой строки\n"
        "• Просто скопировать весь текст со ссылками\n\n"
        "Примеры:\n"
        "t.me/giftcode/abc123\n"
        "https://t.me/giftcode/xyz789\n"
        "t.me/giftcode/def456",
        reply_markup=ReplyKeyboardRemove()
    )
    return UPLOAD_LINKS


async def upload_links(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение ссылок от пользователя"""
    global bot_instance
    
    text = update.message.text
    
    # Извлекаем все ссылки из текста
    links = bot_instance.extract_links(text)
    
    if not links:
        await update.message.reply_text(
            "❌ Ссылки не найдены!\n\n"
            "Убедитесь, что ссылки в формате:\n"
            "t.me/giftcode/... или https://t.me/giftcode/..."
        )
        return UPLOAD_LINKS
    
    # Сохраняем ссылки в контекст
    context.user_data["links"] = links
    
    await update.message.reply_text(
        f"📝 Найдено ссылок: {len(links)}\n\n"
        f"Введите цену для всех аккаунтов (в рублях):"
    )
    return UPLOAD_PRICE


async def upload_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение цены и загрузка аккаунтов"""
    global bot_instance
    
    try:
        price = int(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ Введите корректное число")
        return UPLOAD_PRICE
    
    links = context.user_data.get("links", [])
    duration_days = context.user_data.get("upload_duration", 90)
    duration_text = context.user_data.get("upload_duration_text", "3 месяца")
    
    # Сохраняем цену для возможного повтора
    context.user_data["upload_price"] = price
    
    await update.message.reply_text(
        f"⚡ Начинаю турбо-загрузку {len(links)} аккаунтов\n"
        f"💰 Цена: {price} ₽\n"
        f"📅 Длительность: {duration_text}\n"
        f"🔄 С автоматическими повторными попытками при ошибках 429!"
    )
    
    import time
    start_time = time.time()
    
    # Асинхронная загрузка всех аккаунтов
    results = await bot_instance.upload_accounts_batch(links, price, duration_days, batch_size=5)
    
    end_time = time.time()
    elapsed_time = round(end_time - start_time, 2)
    
    uploaded_urls = []
    failed_uploads = []
    skipped_count = 0
    
    # Обрабатываем результаты
    for result in results:
        idx = result.get("index", 0)
        login = result.get("login", "")
        
        if result["success"]:
            item_id = result["data"].get("item", {}).get("item_id")
            if item_id:
                uploaded_urls.append(f"https://lzt.market/{item_id}/")
            else:
                uploaded_urls.append("Загружен (ID не найден)")
        else:
            # Проверяем нужно ли пропустить эту ошибку
            if result.get("skip_error", False):
                skipped_count += 1
                continue
            
            # Красивое отображение ошибки с ссылкой
            error_msg = result.get('error', 'Неизвестная ошибка')
            failed_uploads.append({
                "index": idx,
                "login": login,
                "error": error_msg
            })
            
            # Детальное логирование в файл
            detailed = result.get('detailed_error', '')
            if detailed:
                logger.error(f"Детальная ошибка аккаунта {idx}: {detailed}")
    
    # Сохраняем неудачные загрузки для повтора
    context.user_data["failed_uploads"] = failed_uploads
    
    # Итоговое сообщение
    summary = f"⚡ Загрузка завершена за {elapsed_time} сек!\n"
    summary += f"✅ Успешно: {len(uploaded_urls)}\n"
    summary += f"❌ Ошибок: {len(failed_uploads)}\n"
    if skipped_count > 0:
        summary += f"⏭️ Пропущено (уже продается): {skipped_count}\n"
    summary += f"📊 Скорость: {round(len(links)/elapsed_time, 2)} акк/сек\n\n"
    
    if uploaded_urls:
        message = summary + f"✅ Ваши аккаунты ({len(uploaded_urls)}) успешно загружены:\n\n"
        
        # Разбиваем на части если слишком много
        chunk_size = 50
        for i in range(0, len(uploaded_urls), chunk_size):
            chunk = uploaded_urls[i:i + chunk_size]
            if i == 0:
                await update.message.reply_text(message + "\n".join(chunk))
            else:
                await update.message.reply_text("\n".join(chunk))
    else:
        await update.message.reply_text(summary + "❌ Ни один аккаунт не был загружен")
    
    if failed_uploads:
        error_message = "❌ Не удалось загрузить:\n\n"
        
        # Форматируем ошибки с ссылками
        formatted_errors = []
        for fail in failed_uploads:
            formatted_errors.append(f"Аккаунт {fail['index']} ({fail['login']}) - {fail['error']}")
        
        chunk_size = 20
        for i in range(0, len(formatted_errors), chunk_size):
            chunk = formatted_errors[i:i + chunk_size]
            if i == 0:
                await update.message.reply_text(error_message + "\n\n".join(chunk))
            else:
                await update.message.reply_text("\n\n".join(chunk))
        
        # Добавляем inline кнопки
        keyboard = [
            [InlineKeyboardButton("🔄 Попробовать еще раз", callback_data="retry_upload")],
            [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Вы можете попробовать загрузить неудачные аккаунты еще раз:",
            reply_markup=reply_markup
        )
        return MAIN_MENU
    
    return await start(update, context)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка inline кнопок"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "main_menu":
        await query.edit_message_reply_markup(reply_markup=None)
        keyboard = [
            ["📤 Загрузить аккаунты"],
            ["📊 Проверить товары"],
            ["📋 Выдать товары"],
            ["❌ Отмена"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await query.message.reply_text(
            "👋 Главное меню\n\n"
            "Выберите действие:",
            reply_markup=reply_markup
        )
        return MAIN_MENU
    
    elif query.data == "retry_upload":
        await query.edit_message_reply_markup(reply_markup=None)
        return await retry_upload_callback(update, context)
    
    return MAIN_MENU


async def retry_upload_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Повторная попытка загрузки неудачных аккаунтов из callback"""
    global bot_instance
    
    query = update.callback_query
    failed_uploads = context.user_data.get("failed_uploads", [])
    
    if not failed_uploads:
        await query.message.reply_text("Нет неудачных загрузок для повтора")
        keyboard = [
            ["📤 Загрузить аккаунты"],
            ["📊 Проверить товары"],
            ["📋 Выдать товары"],
            ["❌ Отмена"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await query.message.reply_text("Выберите действие:", reply_markup=reply_markup)
        return MAIN_MENU
    
    # Извлекаем ссылки из неудачных загрузок
    retry_links = [fail["login"] for fail in failed_uploads]
    price = context.user_data.get("upload_price", 0)
    duration_days = context.user_data.get("upload_duration", 90)
    duration_text = context.user_data.get("upload_duration_text", "3 месяца")
    
    await query.message.reply_text(
        f"⚡ Повторная загрузка {len(retry_links)} аккаунтов\n"
        f"💰 Цена: {price} ₽\n"
        f"📅 Длительность: {duration_text}\n"
        f"🔄 С автоматическими повторными попытками!"
    )
    
    import time
    start_time = time.time()
    
    # Асинхронная загрузка
    results = await bot_instance.upload_accounts_batch(retry_links, price, duration_days, batch_size=5)
    
    end_time = time.time()
    elapsed_time = round(end_time - start_time, 2)
    
    uploaded_urls = []
    new_failed_uploads = []
    skipped_count = 0
    
    # Обрабатываем результаты
    for result in results:
        idx = result.get("index", 0)
        login = result.get("login", "")
        
        if result["success"]:
            item_id = result["data"].get("item", {}).get("item_id")
            if item_id:
                uploaded_urls.append(f"https://lzt.market/{item_id}/")
            else:
                uploaded_urls.append("Загружен (ID не найден)")
        else:
            if result.get("skip_error", False):
                skipped_count += 1
                continue
            
            error_msg = result.get('error', 'Неизвестная ошибка')
            new_failed_uploads.append({
                "index": idx,
                "login": login,
                "error": error_msg
            })
    
    # Обновляем список неудачных загрузок
    context.user_data["failed_uploads"] = new_failed_uploads
    
    # Итоговое сообщение
    summary = f"⚡ Повторная загрузка завершена за {elapsed_time} сек!\n"
    summary += f"✅ Успешно: {len(uploaded_urls)}\n"
    summary += f"❌ Ошибок: {len(new_failed_uploads)}\n"
    if skipped_count > 0:
        summary += f"⏭️ Пропущено (уже продается): {skipped_count}\n"
    
    await query.message.reply_text(summary)
    
    if uploaded_urls:
        message = f"✅ Загружено ({len(uploaded_urls)}):\n\n"
        chunk_size = 50
        for i in range(0, len(uploaded_urls), chunk_size):
            chunk = uploaded_urls[i:i + chunk_size]
            if i == 0:
                await query.message.reply_text(message + "\n".join(chunk))
            else:
                await query.message.reply_text("\n".join(chunk))
    
    if new_failed_uploads:
        error_message = "❌ Все еще не удалось загрузить:\n\n"
        
        formatted_errors = []
        for fail in new_failed_uploads:
            formatted_errors.append(f"Аккаунт {fail['index']} ({fail['login']}) - {fail['error']}")
        
        chunk_size = 20
        for i in range(0, len(formatted_errors), chunk_size):
            chunk = formatted_errors[i:i + chunk_size]
            if i == 0:
                await query.message.reply_text(error_message + "\n\n".join(chunk))
            else:
                await query.message.reply_text("\n\n".join(chunk))
        
        # Снова показываем inline кнопки
        keyboard = [
            [InlineKeyboardButton("🔄 Попробовать еще раз", callback_data="retry_upload")],
            [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            "Вы можете попробовать еще раз:",
            reply_markup=reply_markup
        )
        return MAIN_MENU
    
    # Возвращаемся в главное меню
    keyboard = [
        ["📤 Загрузить аккаунты"],
        ["📊 Проверить товары"],
        ["📋 Выдать товары"],
        ["❌ Отмена"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await query.message.reply_text("Выберите действие:", reply_markup=reply_markup)
    return MAIN_MENU


async def check_items(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Проверка доступных товаров"""
    global bot_instance
    
    await update.message.reply_text("⏳ Проверяю доступные товары...")
    
    result = bot_instance.get_user_items()
    
    if not result["success"]:
        await update.message.reply_text(f"❌ Ошибка получения товаров: {result['error']}")
        return MAIN_MENU
    
    items = result["data"].get("items", [])
    
    # Подсчет по длительности
    duration_counts = {90: 0, 180: 0, 360: 0}
    
    for item in items:
        gifts_duration = item.get("gifts_duration")
        if gifts_duration in duration_counts:
            duration_counts[gifts_duration] += 1
    
    message = "📊 Доступные товары:\n\n"
    message += f"3 месяца - {duration_counts[90]} штук\n"
    message += f"6 месяцев - {duration_counts[180]} штук\n"
    message += f"12 месяцев - {duration_counts[360]} штук\n"
    message += f"\nВсего: {len(items)} товаров"
    
    # Сохраняем данные для последующего использования
    context.user_data["items"] = items
    context.user_data["duration_counts"] = duration_counts
    
    await update.message.reply_text(message)
    return MAIN_MENU


async def select_duration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Выбор длительности подписки"""
    global bot_instance
    
    # Сначала получаем актуальные данные
    result = bot_instance.get_user_items()
    
    if not result["success"]:
        await update.message.reply_text(f"❌ Ошибка получения товаров: {result['error']}")
        return MAIN_MENU
    
    items = result["data"].get("items", [])
    duration_counts = {90: 0, 180: 0, 360: 0}
    
    for item in items:
        gifts_duration = item.get("gifts_duration")
        if gifts_duration in duration_counts:
            duration_counts[gifts_duration] += 1
    
    context.user_data["items"] = items
    context.user_data["duration_counts"] = duration_counts
    
    keyboard = [
        [f"3 месяца ({duration_counts[90]} шт)"],
        [f"6 месяцев ({duration_counts[180]} шт)"],
        [f"12 месяцев ({duration_counts[360]} шт)"],
        ["◀️ Назад"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "📅 Выберите длительность подписки:",
        reply_markup=reply_markup
    )
    return SELECT_DURATION


async def select_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Выбор количества товаров для выдачи"""
    text = update.message.text
    
    if text == "◀️ Назад":
        return await start(update, context)
    
    # Извлекаем длительность
    duration_text = text.split("(")[0].strip()
    duration_days = DURATION_MAPPING.get(duration_text)
    
    if not duration_days:
        await update.message.reply_text("❌ Неверная длительность")
        return SELECT_DURATION
    
    context.user_data["selected_duration"] = duration_days
    context.user_data["selected_duration_text"] = duration_text
    
    available = context.user_data["duration_counts"].get(duration_days, 0)
    
    await update.message.reply_text(
        f"Доступно: {available} штук\n\n"
        f"Введите количество для выдачи (или 'отмена'):",
        reply_markup=ReplyKeyboardRemove()
    )
    return SELECT_COUNT


async def issue_items(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Выдача товаров"""
    global bot_instance
    
    text = update.message.text.lower()
    
    if text == "отмена":
        return await start(update, context)
    
    try:
        requested_count = int(text)
    except ValueError:
        await update.message.reply_text("❌ Введите число")
        return SELECT_COUNT
    
    duration_days = context.user_data["selected_duration"]
    duration_text = context.user_data["selected_duration_text"]
    available = context.user_data["duration_counts"].get(duration_days, 0)
    
    if requested_count > available:
        await update.message.reply_text(
            f"❌ Запрошено: {requested_count}, а доступно: {available}.\n"
            f"Пожалуйста, уменьшите количество."
        )
        return SELECT_COUNT
    
    await update.message.reply_text(f"⏳ Начинаю выдачу {requested_count} товаров...")
    
    # Фильтруем товары по длительности
    items = context.user_data["items"]
    filtered_items = [item for item in items if item.get("gifts_duration") == duration_days]
    
    # Берем нужное количество
    items_to_issue = filtered_items[:requested_count]
    
    # Формируем сообщение с выданными товарами
    issued_message = f"📋 Months: {duration_text.split()[0]} | Count: {requested_count}\n\n"
    items_to_delete = []
    
    for item in items_to_issue:
        item_id = item.get("item_id")
        login = item.get("login", "")
        
        # Добавляем префикс если нужно
        if login and not login.startswith("https://t.me/giftcode/"):
            login = f"https://t.me/giftcode/{login}"
        
        issued_message += f"{login} | https://lzt.market/{item_id}/\n"
        items_to_delete.append(item_id)
    
    # Разбиваем на части если сообщение слишком длинное
    if len(issued_message) > 4000:
        parts = [issued_message[i:i+4000] for i in range(0, len(issued_message), 4000)]
        for part in parts:
            await update.message.reply_text(part)
    else:
        await update.message.reply_text(issued_message)
    
    # Удаление товаров
    await update.message.reply_text("⚡ Начинаю турбо-удаление выданных товаров с автоповтором...")
    
    import time
    start_time = time.time()
    
    # Асинхронное удаление
    results = await bot_instance.delete_items_batch(items_to_delete, batch_size=3)
    
    end_time = time.time()
    elapsed_time = round(end_time - start_time, 2)
    
    deleted_urls = []
    failed_deletes = []
    
    for result in results:
        if result["success"]:
            deleted_urls.append(f"https://lzt.market/{result['item_id']}/")
        else:
            error_msg = result.get('error', 'Неизвестная ошибка')
            failed_deletes.append(f"https://lzt.market/{result['item_id']}/ | {error_msg}")
            
            # Детальное логирование
            detailed = result.get('detailed_error', '')
            if detailed:
                logger.error(f"Детальная ошибка удаления {result['item_id']}: {detailed}")
    
    # Итоговое сообщение об удалении
    summary = f"⚡ Удаление завершено за {elapsed_time} сек!\n"
    summary += f"✅ Удалено: {len(deleted_urls)}\n"
    summary += f"❌ Ошибок: {len(failed_deletes)}\n\n"
    
    if deleted_urls:
        delete_message = summary + "✅ Удалено:\n\n"
        chunk_size = 50
        for i in range(0, len(deleted_urls), chunk_size):
            chunk = deleted_urls[i:i + chunk_size]
            if i == 0:
                await update.message.reply_text(delete_message + "\n".join(chunk))
            else:
                await update.message.reply_text("\n".join(chunk))
    else:
        await update.message.reply_text(summary)
    
    if failed_deletes:
        error_message = "❌ Не удалось удалить:\n\n"
        chunk_size = 30
        for i in range(0, len(failed_deletes), chunk_size):
            chunk = failed_deletes[i:i + chunk_size]
            if i == 0:
                await update.message.reply_text(error_message + "\n".join(chunk))
            else:
                await update.message.reply_text("\n".join(chunk))
    
    return await start(update, context)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена операции"""
    await update.message.reply_text(
        "❌ Операция отменена",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def main():
    """Главная функция запуска бота"""
    # Загрузка конфигурации из файла
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        TELEGRAM_TOKEN = config['TELEGRAM_TOKEN']
        LZT_TOKEN = config['LZT_TOKEN']
        USER_ID = config['USER_ID']
        
        logger.info("✅ Конфигурация успешно загружена из config.json")
    except FileNotFoundError:
        logger.error("❌ Файл config.json не найден!")
        logger.error("Создайте файл config.json со следующей структурой:")
        logger.error('''{
    "TELEGRAM_TOKEN": "ваш_telegram_токен",
    "LZT_TOKEN": "ваш_lzt_токен",
    "USER_ID": "ваш_user_id"
}''')
        return
    except KeyError as e:
        logger.error(f"❌ В config.json отсутствует ключ: {e}")
        return
    except json.JSONDecodeError:
        logger.error("❌ Ошибка чтения config.json - проверьте формат JSON")
        return
    
    global bot_instance
    bot_instance = LZTMarketBot(LZT_TOKEN, USER_ID)
    
    # Создание приложения
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Настройка обработчика разговора
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu),
                CallbackQueryHandler(handle_callback)
            ],
            SELECT_UPLOAD_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_upload_duration)],
            UPLOAD_LINKS: [MessageHandler(filters.TEXT & ~filters.COMMAND, upload_links)],
            UPLOAD_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, upload_price)],
            SELECT_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_count)],
            SELECT_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, issue_items)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    application.add_handler(conv_handler)
    
    # Запуск бота
    logger.info("🚀 Турбо-бот с автоповтором запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()