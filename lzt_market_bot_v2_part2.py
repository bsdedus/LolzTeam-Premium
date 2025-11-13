# Продолжение lzt_market_bot_v2.py
# Этот файл нужно объединить с первой частью

async def select_upload_duration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Выбор длительности для загрузки"""
    user_id = update.effective_user.id
    text = update.message.text
    
    if text == config_manager.get_translation(str(user_id), "back"):
        return await start(update, context)
    
    # Определяем длительность
    duration_days = None
    duration_text = text
    
    if text == config_manager.get_translation(str(user_id), "3_months"):
        duration_days = 90
    elif text == config_manager.get_translation(str(user_id), "6_months"):
        duration_days = 180
    elif text == config_manager.get_translation(str(user_id), "12_months"):
        duration_days = 360
    
    if not duration_days:
        await update.message.reply_text(
            config_manager.get_translation(str(user_id), "invalid_duration")
        )
        return SELECT_UPLOAD_DURATION
    
    context.user_data["upload_duration"] = duration_days
    context.user_data["upload_duration_text"] = duration_text
    
    await update.message.reply_text(
        config_manager.get_translation(str(user_id), "duration_selected", duration=duration_text),
        reply_markup=ReplyKeyboardRemove()
    )
    return UPLOAD_LINKS


async def upload_links(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение ссылок от пользователя"""
    global bot_instance
    user_id = update.effective_user.id
    
    text = update.message.text
    links = bot_instance.extract_links(text)
    
    if not links:
        await update.message.reply_text(
            config_manager.get_translation(str(user_id), "links_not_found")
        )
        return UPLOAD_LINKS
    
    context.user_data["links"] = links
    
    await update.message.reply_text(
        config_manager.get_translation(str(user_id), "links_found", count=len(links))
    )
    return UPLOAD_PRICE


async def upload_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение цены и загрузка аккаунтов"""
    global bot_instance
    user_id = update.effective_user.id
    
    try:
        price = int(update.message.text)
    except ValueError:
        await update.message.reply_text(
            config_manager.get_translation(str(user_id), "invalid_number")
        )
        return UPLOAD_PRICE
    
    links = context.user_data.get("links", [])
    duration_days = context.user_data.get("upload_duration", 90)
    duration_text = context.user_data.get("upload_duration_text", "3 months")
    
    context.user_data["upload_price"] = price
    
    await update.message.reply_text(
        config_manager.get_translation(str(user_id), "upload_started", 
                                      count=len(links), price=price, duration=duration_text)
    )
    
    import time
    start_time = time.time()
    
    results = await bot_instance.upload_accounts_batch(links, price, duration_days, batch_size=5)
    
    end_time = time.time()
    elapsed_time = round(end_time - start_time, 2)
    
    uploaded_urls = []
    failed_uploads = []
    skipped_count = 0
    
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
            failed_uploads.append({
                "index": idx,
                "login": login,
                "error": error_msg
            })
            
            detailed = result.get('detailed_error', '')
            if detailed:
                logger.error(f"Детальная ошибка аккаунта {idx}: {detailed}")
    
    context.user_data["failed_uploads"] = failed_uploads
    
    speed = round(len(links)/elapsed_time, 2) if elapsed_time > 0 else 0
    summary = config_manager.get_translation(str(user_id), "upload_completed",
                                            time=elapsed_time, success=len(uploaded_urls),
                                            errors=len(failed_uploads), skipped=skipped_count,
                                            speed=speed)
    
    if uploaded_urls:
        message = summary + config_manager.get_translation(str(user_id), "accounts_uploaded", count=len(uploaded_urls))
        
        chunk_size = 50
        for i in range(0, len(uploaded_urls), chunk_size):
            chunk = uploaded_urls[i:i + chunk_size]
            if i == 0:
                await update.message.reply_text(message + "\n".join(chunk))
            else:
                await update.message.reply_text("\n".join(chunk))
    else:
        await update.message.reply_text(summary + config_manager.get_translation(str(user_id), "no_accounts_uploaded"))
    
    if failed_uploads:
        error_message = config_manager.get_translation(str(user_id), "failed_to_upload")
        
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
        
        keyboard = [
            [InlineKeyboardButton(config_manager.get_translation(str(user_id), "retry_upload"), 
                                 callback_data="retry_upload")],
            [InlineKeyboardButton(config_manager.get_translation(str(user_id), "main_menu"), 
                                 callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            config_manager.get_translation(str(user_id), "retry_prompt"),
            reply_markup=reply_markup
        )
        return MAIN_MENU
    
    return await start(update, context)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка inline кнопок"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if query.data.startswith("lang_"):
        return await set_language(update, context)
    
    if query.data == "main_menu":
        await query.edit_message_reply_markup(reply_markup=None)
        return await start_from_callback(update, context)
    
    elif query.data == "retry_upload":
        await query.edit_message_reply_markup(reply_markup=None)
        return await retry_upload_callback(update, context)
    
    return MAIN_MENU


async def start_from_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало работы из callback"""
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
        config_manager.get_translation(str(user_id), "select_action"),
        reply_markup=reply_markup
    )
    return MAIN_MENU


async def retry_upload_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Повторная попытка загрузки из callback"""
    global bot_instance
    user_id = update.effective_user.id
    query = update.callback_query
    
    failed_uploads = context.user_data.get("failed_uploads", [])
    
    if not failed_uploads:
        await query.message.reply_text(
            config_manager.get_translation(str(user_id), "no_retry_uploads")
        )
        return await start_from_callback(update, context)
    
    retry_links = [fail["login"] for fail in failed_uploads]
    price = context.user_data.get("upload_price", 0)
    duration_days = context.user_data.get("upload_duration", 90)
    duration_text = context.user_data.get("upload_duration_text", "3 months")
    
    await query.message.reply_text(
        config_manager.get_translation(str(user_id), "retry_upload_started",
                                      count=len(retry_links), price=price, duration=duration_text)
    )
    
    import time
    start_time = time.time()
    
    results = await bot_instance.upload_accounts_batch(retry_links, price, duration_days, batch_size=5)
    
    end_time = time.time()
    elapsed_time = round(end_time - start_time, 2)
    
    uploaded_urls = []
    new_failed_uploads = []
    skipped_count = 0
    
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
    
    context.user_data["failed_uploads"] = new_failed_uploads
    
    summary = config_manager.get_translation(str(user_id), "retry_completed",
                                            time=elapsed_time, success=len(uploaded_urls),
                                            errors=len(new_failed_uploads), skipped=skipped_count)
    
    await query.message.reply_text(summary)
    
    if uploaded_urls:
        message = config_manager.get_translation(str(user_id), "uploaded_count", count=len(uploaded_urls))
        chunk_size = 50
        for i in range(0, len(uploaded_urls), chunk_size):
            chunk = uploaded_urls[i:i + chunk_size]
            if i == 0:
                await query.message.reply_text(message + "\n".join(chunk))
            else:
                await query.message.reply_text("\n".join(chunk))
    
    if new_failed_uploads:
        error_message = config_manager.get_translation(str(user_id), "still_failed")
        
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
        
        keyboard = [
            [InlineKeyboardButton(config_manager.get_translation(str(user_id), "retry_upload"), 
                                 callback_data="retry_upload")],
            [InlineKeyboardButton(config_manager.get_translation(str(user_id), "main_menu"), 
                                 callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            config_manager.get_translation(str(user_id), "retry_again"),
            reply_markup=reply_markup
        )
        return MAIN_MENU
    
    return await start_from_callback(update, context)


async def check_items(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Проверка доступных товаров"""
    global bot_instance
    user_id = update.effective_user.id
    
    await update.message.reply_text(
        config_manager.get_translation(str(user_id), "checking_items")
    )
    
    result = bot_instance.get_user_items()
    
    if not result["success"]:
        await update.message.reply_text(
            config_manager.get_translation(str(user_id), "error_getting_items", error=result['error'])
        )
        return MAIN_MENU
    
    items = result["data"].get("items", [])
    duration_counts = {90: 0, 180: 0, 360: 0}
    
    for item in items:
        gifts_duration = item.get("gifts_duration")
        if gifts_duration in duration_counts:
            duration_counts[gifts_duration] += 1
    
    context.user_data["items"] = items
    context.user_data["duration_counts"] = duration_counts
    
    await update.message.reply_text(
        config_manager.get_translation(str(user_id), "available_items",
                                      m3=duration_counts[90], m6=duration_counts[180],
                                      m12=duration_counts[360], total=len(items))
    )
    return MAIN_MENU


async def select_duration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Выбор длительности подписки для выдачи"""
    global bot_instance
    user_id = update.effective_user.id
    
    result = bot_instance.get_user_items()
    
    if not result["success"]:
        await update.message.reply_text(
            config_manager.get_translation(str(user_id), "error_getting_items", error=result['error'])
        )
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
        [f"{config_manager.get_translation(str(user_id), '3_months')} ({duration_counts[90]} шт)"],
        [f"{config_manager.get_translation(str(user_id), '6_months')} ({duration_counts[180]} шт)"],
        [f"{config_manager.get_translation(str(user_id), '12_months')} ({duration_counts[360]} шт)"],
        [config_manager.get_translation(str(user_id), "back")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        config_manager.get_translation(str(user_id), "select_duration_issue"),
        reply_markup=reply_markup
    )
    return SELECT_DURATION


async def select_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Выбор количества товаров для выдачи"""
    user_id = update.effective_user.id
    text = update.message.text
    
    if text == config_manager.get_translation(str(user_id), "back"):
        return await start(update, context)
    
    # Извлекаем длительность
    duration_text = text.split("(")[0].strip()
    duration_days = None
    
    if duration_text == config_manager.get_translation(str(user_id), "3_months"):
        duration_days = 90
    elif duration_text == config_manager.get_translation(str(user_id), "6_months"):
        duration_days = 180
    elif duration_text == config_manager.get_translation(str(user_id), "12_months"):
        duration_days = 360
    
    if not duration_days:
        await update.message.reply_text(
            config_manager.get_translation(str(user_id), "invalid_duration")
        )
        return SELECT_DURATION
    
    context.user_data["selected_duration"] = duration_days
    context.user_data["selected_duration_text"] = duration_text
    
    available = context.user_data["duration_counts"].get(duration_days, 0)
    
    await update.message.reply_text(
        config_manager.get_translation(str(user_id), "available_count", count=available),
        reply_markup=ReplyKeyboardRemove()
    )
    return SELECT_COUNT


async def issue_items(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Выдача товаров"""
    global bot_instance
    user_id = update.effective_user.id
    
    text = update.message.text.lower()
    
    if text == config_manager.get_translation(str(user_id), "cancel").lower():
        return await start(update, context)
    
    try:
        requested_count = int(text)
    except ValueError:
        await update.message.reply_text(
            config_manager.get_translation(str(user_id), "enter_number")
        )
        return SELECT_COUNT
    
    duration_days = context.user_data["selected_duration"]
    duration_text = context.user_data["selected_duration_text"]
    available = context.user_data["duration_counts"].get(duration_days, 0)
    
    if requested_count > available:
        await update.message.reply_text(
            config_manager.get_translation(str(user_id), "requested_more",
                                          requested=requested_count, available=available)
        )
        return SELECT_COUNT
    
    await update.message.reply_text(
        config_manager.get_translation(str(user_id), "issuing_items", count=requested_count)
    )
    
    items = context.user_data["items"]
    filtered_items = [item for item in items if item.get("gifts_duration") == duration_days]
    items_to_issue = filtered_items[:requested_count]
    
    issued_message = f"📋 Months: {duration_text.split()[0]} | Count: {requested_count}\n\n"
    items_to_delete = []
    
    for item in items_to_issue:
        item_id = item.get("item_id")
        login = item.get("login", "")
        
        if login and not login.startswith("https://t.me/giftcode/"):
            login = f"https://t.me/giftcode/{login}"
        
        issued_message += f"{login} | https://lzt.market/{item_id}/\n"
        items_to_delete.append(item_id)
    
    if len(issued_message) > 4000:
        parts = [issued_message[i:i+4000] for i in range(0, len(issued_message), 4000)]
        for part in parts:
            await update.message.reply_text(part)
    else:
        await update.message.reply_text(issued_message)
    
    await update.message.reply_text("⚡ Начинаю турбо-удаление выданных товаров с автоповтором...")
    
    import time
    start_time = time.time()
    
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
            
            detailed = result.get('detailed_error', '')
            if detailed:
                logger.error(f"Детальная ошибка удаления {result['item_id']}: {detailed}")
    
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
    user_id = update.effective_user.id
    await update.message.reply_text(
        config_manager.get_translation(str(user_id), "operation_cancelled"),
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def main():
    """Главная функция запуска бота"""
    global config_manager, bot_instance
    
    # Инициализация менеджера конфигурации
    config_manager = ConfigManager()
    
    # Получение токенов
    telegram_token = config_manager.config["api_tokens"]["telegram_token"]
    
    # Инициализация бота
    bot_instance = LZTMarketBot(config_manager)
    
    logger.info("✅ Конфигурация успешно загружена")
    
    # Создание приложения
    application = Application.builder().token(telegram_token).build()
    
    # Настройка обработчика разговора
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", language_selection)],
        states={
            LANGUAGE_SELECT: [CallbackQueryHandler(set_language)],
            MAIN_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu),
                CallbackQueryHandler(handle_callback)
            ],
            SELECT_UPLOAD_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_upload_duration)],
            UPLOAD_LINKS: [MessageHandler(filters.TEXT & ~filters.COMMAND, upload_links)],
            UPLOAD_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, upload_price)],
            SELECT_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_count)],
            SELECT_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, issue_items)],
            SETTINGS_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_settings)],
            CHANGE_CURRENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_currency)],
            CHANGE_ORIGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_origin)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    application.add_handler(conv_handler)
    
    # Запуск бота
    logger.info("🚀 Мультиязычный турбо-бот с настройками запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()