import csv
import io
import math
from typing import cast, List

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Audio,
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    Video,
)

from filters import IsAdminFilter
from fsm import FSMAdmin
from keyboards import AcceptCancelKeyboard, AdminPanelKeyboard, CancelKeyboard, EditionCancelKeyboart
from models import Genre, SongTempo, SongType, User
from service import GenreService, SongService, UserService

router = Router()
router.message.filter(IsAdminFilter())

TypeRus = {
    SongType.universal.value: "Универсальная",
    SongType.male.value: "Мужская",
    SongType.female.value: "Женская",
    SongType.duet.value: "Дуэт",
    "Универсальная": SongType.universal.value,
    "Мужская": SongType.male.value,
    "Женская": SongType.female.value,
    "Дуэт": SongType.duet.value,
}

TempoRus = {
    SongTempo.dance.value: "Танцевальная",
    SongTempo.mid_tempo.value: "Среднетемповая",
    SongTempo.slow.value: "Медленная",
    "Танцевальная": SongTempo.dance.value,
    "Среднетемповая": SongTempo.mid_tempo.value,
    "Медленная": SongTempo.slow.value,
}


@router.message(F.text == "🔐 Панель администратора")
async def handle_admin_panel(message: Message, state: FSMContext) -> None:
    await state.clear()

    text = (
        "🔐 <b>Добро пожаловать в панель администратора!</b>\n\n"
        "🛠 Здесь вы можете управлять контентом и пользователями.\n"
        "👇 Выберите действие:"
    )

    keyboard = AdminPanelKeyboard()()
    await message.answer(text, reply_markup=keyboard)


"""Song creation handlers"""


@router.message(F.text == "❌ Отменить", FSMAdmin.confirm_data)
async def process_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🚫 Создание песни отменено", reply_markup=AdminPanelKeyboard()())

    await handle_admin_panel(message, state)


@router.message(Command("cancel"), ~StateFilter(None))
@router.message(F.text == "❌ Отменить", ~StateFilter(None))
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🚫 Действие отменено", reply_markup=AdminPanelKeyboard()())

    await handle_admin_panel(message, state)


@router.message(F.text == "🎵 Добавить песню")
async def start_create_song(message: Message, state: FSMContext):
    await state.set_state(FSMAdmin.enter_title)
    await message.answer("🎶 Введите название песни:", reply_markup=CancelKeyboard()())


@router.message(FSMAdmin.enter_title)
async def process_title(message: Message, state: FSMContext, song_service: SongService):
    if len(str(message.text)) > 150:
        await message.answer("❌ Слишком длинное название (макс. 150 символов)")
        return
    if await song_service.get_by_title(str(message.text)):
        await message.answer("❌ Песня с таким названием уже существует! ")
        return

    await state.update_data(title=message.text)
    await state.set_state(FSMAdmin.select_type)

    buttons = [[InlineKeyboardButton(text=TypeRus[t.value], callback_data=t.value)] for t in SongType]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer("🎚 Выберите тип песни:", reply_markup=keyboard)


@router.callback_query(FSMAdmin.select_type)
async def process_type(callback: CallbackQuery, state: FSMContext):
    song_type = callback.data
    await state.update_data(type_str=song_type)
    await state.set_state(FSMAdmin.select_tempo)

    buttons = [[InlineKeyboardButton(text=TempoRus[t.value], callback_data=t.value)] for t in SongTempo]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text("🎛 Выберите темп песни:", reply_markup=keyboard)  # type: ignore


@router.callback_query(FSMAdmin.select_tempo)
async def process_tempo(callback: CallbackQuery, state: FSMContext):
    tempo = callback.data
    await state.update_data(tempo_str=tempo)
    await state.set_state(FSMAdmin.enter_genres)

    await callback.message.answer(  # type: ignore
        "🎭 Введите до 3 жанров через запятую:\n"
        "Пример: Рок, Поп, Электроника\n\n"
        "⚠️ Если жанра нет в системе - он будет создан автоматически",
        reply_markup=CancelKeyboard()(),
    )
    await callback.answer()
    await callback.message.delete()  # type: ignore


@router.message(FSMAdmin.enter_genres)
async def process_genres_input(message: Message, genre_service: GenreService, state: FSMContext):
    genres_input = str(message.text).strip()

    # Разделяем жанры по запятым и очищаем от пробелов
    genre_titles = [g.strip().lower() for g in genres_input.split(",") if g.strip()]

    # Валидация
    if not genre_titles:
        await message.answer("❌ Нужно указать хотя бы один жанр!")
        return

    if len(genre_titles) > 3:
        await message.answer("❌ Можно указать не более 3 жанров!")
        return

    valid_genres = []
    for title in genre_titles:
        if len(title) > 150:
            await message.answer(f"❌ Название жанра слишком длинное: {title}")
            return

        genre = await genre_service.get_or_create(title)
        if not genre:
            await message.answer(f"❌ Ошибка обработки жанра {title}")
            return
        valid_genres.append(genre.title)

    await state.update_data(genre_ids=valid_genres)
    await state.set_state(FSMAdmin.enter_lyrics)

    await message.answer(
        "📝 Теперь введите текст песни (или отправьте '-' чтобы пропустить):",
        reply_markup=CancelKeyboard()(),
    )


@router.message(FSMAdmin.enter_lyrics)
async def process_lyrics(message: Message, state: FSMContext):
    lyrics = message.text if message.text != "-" else None
    await state.update_data(lyrics=lyrics)
    await state.set_state(FSMAdmin.upload_video)

    await message.answer(
        "🎵 <b>Загрузите аудио или видео файл песни</b>\n"
        "▸ Форматы: <code>MP3</code>, <code>MP4</code>\n"
        "▸ Макс. размер: <code>50MB</code>\n\n"
        "Или нажмите <b>«Пропустить»</b>, чтобы добавить позже",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="⏭ Пропустить", callback_data="skip_video")]],
        ),
        parse_mode="HTML",
    )


@router.message(FSMAdmin.upload_video, F.video)
async def process_video(message: Message, state: FSMContext):
    video = cast(Video, message.video)

    await state.update_data(file_id=video.file_id, file_type="video")
    await handle_confirmation(message, state)


@router.message(FSMAdmin.upload_video, F.audio)
async def process_audio(message: Message, state: FSMContext):
    audio = cast(Audio, message.audio)

    await state.update_data(file_id=audio.file_id, file_type="audio")
    await handle_confirmation(message, state)


@router.callback_query(FSMAdmin.upload_video, F.data == "skip_video")
async def skip_video(callback: CallbackQuery, state: FSMContext):
    await state.update_data(file_id=None)
    await handle_confirmation(callback.message, state)  # type: ignore
    await callback.answer()


async def handle_confirmation(message: Message, state: FSMContext):
    data = await state.get_data()

    confirmation_text = (
        "📋 Проверьте данные:\n\n"
        f"🎶 Название: {data['title']}\n"
        f"🎚 Тип: {TypeRus[data['type_str']].capitalize()}\n"
        f"🎛 Темп: {TempoRus[data['tempo_str']].capitalize()}\n"
        f"🎭 Жанры: {', '.join(s.capitalize() for s in data['genre_ids'])}\n"
        f"📝 Текст: {'указан' if data['lyrics'] else 'не указан'}\n"
        f"🎵 Медиа: {'добавлено' if data.get('file_id') else 'отсутствует'}"
    )

    await state.set_state(FSMAdmin.confirm_data)
    await message.answer(confirmation_text, reply_markup=AcceptCancelKeyboard()())


@router.message(F.text == "✅ Подтвердить", FSMAdmin.confirm_data)
async def process_confirm(message: Message, state: FSMContext, song_service: SongService, current_user: User):
    data = await state.get_data()

    song = await song_service.create_with_genres(
        author_id=str(current_user.id),
        title=data["title"],
        genre_ids=data["genre_ids"],
        lyrics=data.get("lyrics"),
        type_str=data["type_str"],
        tempo_str=data["tempo_str"],
        file_id=data.get("file_id"),
        file_type_str=data.get("file_type", None),
    )
    if not song:
        await message.answer("❌ Ошибка создания песни")
        return

    await state.clear()
    await message.answer(
        "✅ Песня успешно создана!",
        reply_markup=AdminPanelKeyboard()(),
    )

    await handle_admin_panel(message, state)


@router.message(F.text == "🗑 Удалить песню")
async def admin_start_delete(message: Message, state: FSMContext):
    await state.set_state(FSMAdmin.enter_delete_title)
    await message.answer(
        "🗑 Введите точное название песни для удаления:",
        reply_markup=CancelKeyboard()(),
    )


"""Song deletion handlers"""


@router.message(FSMAdmin.enter_delete_title)
async def admin_process_delete(
    message: Message,
    state: FSMContext,
    song_service: SongService,
    user_service: UserService,
):
    title = str(message.text).strip()
    song = await song_service.get_by_title(title)

    if not song:
        await message.answer(f"❌ Песня «{title}» не найдена.")
        await state.clear()
        await handle_admin_panel(message, state)
        return

    for customer in await song_service.get_customers(song.id):
        await user_service.log_view(customer.id, song.title, "delete")
    await song_service.delete(song.id)
    await state.clear()
    await message.answer(
        f"✅ Песня с названием «{title}» удалена",
        reply_markup=AdminPanelKeyboard()(),
    )
    await handle_admin_panel(message, state)


@router.message(F.text == "✏️ Изменить песню")
async def start_edit_song(message: Message, state: FSMContext):
    await state.set_state(FSMAdmin.edit_song_enter_title)
    await message.answer(
        "✏️ Введите точное название песни для изменения:",
        reply_markup=CancelKeyboard()(),
    )


@router.message(FSMAdmin.edit_song_enter_title)
async def process_edit_song_title(message: Message, state: FSMContext, song_service: SongService):
    title = str(message.text).strip()
    song = await song_service.get_by_title(title)

    if not song:
        await message.answer(f"❌ Песня «{title}» не найдена")
        await state.clear()
        await handle_admin_panel(message, state)
        return

    await state.update_data(
        song_id=str(song.id),
        current_title=song.title,
    )
    await state.set_state(FSMAdmin.edit_song_select_field)
    await show_edit_menu(message, state, song_service)


async def show_edit_menu(message: Message, state: FSMContext, song_service: SongService):
    data = await state.get_data()
    song_id = int(data["song_id"])
    song = await song_service.get_one(song_id)

    if not song:
        await message.answer("❌ Песня больше не существует!")
        await state.clear()
        return

    genres = [g.title for g in song.genres]

    text = (
        "✏️ <b>Редактирование песни:</b>\n"
        f"🎶 Название: {song.title}\n"
        f"🎚 Тип: {TypeRus[song.type.value]}\n"
        f"🎛 Темп: {TempoRus[song.tempo.value]}\n"
        f"🎭 Жанры: {', '.join(genres) if genres else 'не указаны'}\n"
        f"📝 Текст: {'указан' if song.lyrics else 'не указан'}\n"
        f"🎵 Медиа: {'добавлено' if song.file_id else 'отсутствует'}\n\n"
        "👇 Выберите поле для изменения:"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Название", callback_data="edit_title")],
            [InlineKeyboardButton(text="✏️ Тип", callback_data="edit_type")],
            [InlineKeyboardButton(text="✏️ Темп", callback_data="edit_tempo")],
            [InlineKeyboardButton(text="✏️ Жанры", callback_data="edit_genres")],
            [InlineKeyboardButton(text="✏️ Текст", callback_data="edit_lyrics")],
            [InlineKeyboardButton(text="✏️ Медиафайл", callback_data="edit_media")],
            [InlineKeyboardButton(text="🏠 Выйти", callback_data="edit_exit")],
        ],
    )

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(FSMAdmin.edit_song_select_field, F.data == "edit_title")
async def edit_song_title(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FSMAdmin.edit_song_title)
    await callback.message.edit_text(  # type: ignore
        "✏️ Введите новое название песни:",
        reply_markup=EditionCancelKeyboart()(),
    )
    await callback.answer()


@router.message(FSMAdmin.edit_song_title)
async def process_edit_title(message: Message, state: FSMContext, song_service: SongService):
    new_title = str(message.text).strip()
    data = await state.get_data()
    song_id = int(data["song_id"])

    existing = await song_service.get_by_title(new_title)
    if existing and existing.id != song_id:
        await message.answer("❌ Песня с таким названием уже существует!")
        return

    if len(new_title) > 150:
        await message.answer("❌ Слишком длинное название (макс. 150 символов)")
        return

    updated = await song_service.update(song_id=song_id, title=new_title)

    if not updated:
        await message.answer("❌ Ошибка при обновлении названия")
        return

    await state.update_data(current_title=new_title)
    await state.set_state(FSMAdmin.edit_song_select_field)
    await show_edit_menu(message, state, song_service)


@router.callback_query(FSMAdmin.edit_song_select_field, F.data == "edit_type")
async def edit_song_type(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FSMAdmin.edit_song_type)

    buttons = [[InlineKeyboardButton(text=TypeRus[t.value], callback_data=t.value)] for t in SongType]

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(  # type: ignore
        "✏️ Выберите новый тип песни:",
        reply_markup=keyboard,
    )
    await callback.answer()


@router.callback_query(FSMAdmin.edit_song_type)
async def process_edit_type(callback: CallbackQuery, state: FSMContext, song_service: SongService):
    new_type = callback.data
    data = await state.get_data()
    song_id = int(data["song_id"])

    updated = await song_service.update(song_id=song_id, type_str=new_type)

    if not updated:
        await callback.message.answer("❌ Ошибка при обновлении типа песни")  # type: ignore
    else:
        await callback.answer("✅ Тип песни обновлен")

    await state.set_state(FSMAdmin.edit_song_select_field)
    await show_edit_menu(callback.message, state, song_service)  # pyright: ignore[reportArgumentType]
    await callback.message.delete()  # type: ignore


@router.callback_query(FSMAdmin.edit_song_select_field, F.data == "edit_tempo")
async def edit_song_tempo(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FSMAdmin.edit_song_tempo)

    buttons = [[InlineKeyboardButton(text=TempoRus[t.value], callback_data=t.value)] for t in SongTempo]

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(  # type: ignore
        "✏️ Выберите новый темп песни:",
        reply_markup=keyboard,
    )
    await callback.answer()


@router.callback_query(FSMAdmin.edit_song_tempo)
async def process_edit_tempo(callback: CallbackQuery, state: FSMContext, song_service: SongService):
    new_tempo = callback.data
    data = await state.get_data()
    song_id = int(data["song_id"])

    updated = await song_service.update(song_id=song_id, tempo_str=new_tempo)

    if not updated:
        await callback.message.answer("❌ Ошибка при обновлении темпа песни")  # type: ignore
    else:
        await callback.answer("✅ Темп песни обновлен")

    await state.set_state(FSMAdmin.edit_song_select_field)
    await show_edit_menu(callback.message, state, song_service)  # type: ignore
    await callback.message.delete()  # type: ignore


@router.callback_query(FSMAdmin.edit_song_select_field, F.data == "edit_genres")
async def edit_song_genres(callback: CallbackQuery, state: FSMContext, song_service: SongService):
    data = await state.get_data()
    song_id = int(data["song_id"])
    song = await song_service.get_one(song_id)

    if song:
        current_genres = ", ".join([g.title for g in song.genres])
        await callback.message.answer(  # type: ignore
            "✏️ Введите новые жанры через запятую:\n"
            f"Текущие: {current_genres}\n\n"
            "Отправьте 'удалить' чтобы очистить жанры",
            reply_markup=EditionCancelKeyboart()(),
        )
        await state.set_state(FSMAdmin.edit_song_genres)
    await callback.answer()
    await callback.message.delete()  # type: ignore


@router.message(FSMAdmin.edit_song_genres)
async def process_edit_genres(
    message: Message,
    state: FSMContext,
    song_service: SongService,
    genre_service: GenreService,
):
    input_text = str(message.text).strip().lower()
    data = await state.get_data()
    song_id = int(data["song_id"])

    if input_text == "удалить":
        updated = await song_service.update_genres(song_id, [])
        if not updated:
            await message.answer("❌ Ошибка при удалении жанров")
    else:
        # Обработка новых жанров
        genre_titles = [g.strip() for g in input_text.split(",") if g.strip()]

        if len(genre_titles) > 3:
            await message.answer("❌ Можно указать не более 3 жанров!")
            return

        # Получаем или создаем жанры
        valid_genres: List[Genre] = []
        for title in genre_titles:
            if len(title) > 150:
                await message.answer(f"❌ Название жанра слишком длинное: {title}")
                return

            genre = await genre_service.get_or_create(title)
            if genre:
                valid_genres.append(genre)

        # Обновляем жанры песни
        updated = await song_service.update_genres(song_id, [g.id for g in valid_genres])
        if not updated:
            await message.answer("❌ Ошибка при обновлении жанров")

    await state.set_state(FSMAdmin.edit_song_select_field)
    await show_edit_menu(message, state, song_service)


@router.callback_query(FSMAdmin.edit_song_select_field, F.data == "edit_lyrics")
async def edit_song_lyrics(callback: CallbackQuery, state: FSMContext, song_service: SongService):
    await state.set_state(FSMAdmin.edit_song_lyrics)

    data = await state.get_data()
    song_id = int(data["song_id"])
    song = await song_service.get_one(song_id)

    if song and song.lyrics:
        text = (
            "✏️ Текущий текст песни:\n"
            f"{song.lyrics[:300] + '...' if len(song.lyrics) > 300 else song.lyrics}\n\n"
            "Введите новый текст или отправьте 'удалить' для удаления:"
        )
    else:
        text = "✏️ Введите текст песни:"

    await callback.message.edit_text(  # type: ignore
        text,
        reply_markup=EditionCancelKeyboart()(),
    )
    await callback.answer()


@router.message(FSMAdmin.edit_song_lyrics)
async def process_edit_lyrics(message: Message, state: FSMContext, song_service: SongService):
    input_text = str(message.text).strip()
    data = await state.get_data()
    song_id = int(data["song_id"])

    if input_text.lower() == "удалить":
        new_lyrics = ""
    else:
        new_lyrics = input_text

    updated = await song_service.update(song_id=song_id, lyrics=new_lyrics)

    if not updated:
        await message.answer("❌ Ошибка при обновлении текста")

    await state.set_state(FSMAdmin.edit_song_select_field)
    await show_edit_menu(message, state, song_service)


@router.callback_query(FSMAdmin.edit_song_select_field, F.data == "edit_media")
async def edit_song_media(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FSMAdmin.edit_song_media)

    text = "✏️ Загрузите новое аудио/видео или отправьте 'удалить':\n\n" "▸ Форматы: MP3, MP4\n" "▸ Макс. размер: 50MB"

    await callback.message.edit_text(  # type: ignore
        text,
        reply_markup=EditionCancelKeyboart()(),
    )
    await callback.answer()


@router.message(FSMAdmin.edit_song_media, F.text)
async def process_edit_media_text(message: Message, state: FSMContext, song_service: SongService):
    input_text = str(message.text).strip().lower()
    data = await state.get_data()
    song_id = int(data["song_id"])

    if input_text == "удалить":
        updated = await song_service.update(song_id=song_id, file_id="", file_type_str="video")

        if not updated:
            await message.answer("❌ Ошибка при удалении медиафайла")

    await state.set_state(FSMAdmin.edit_song_select_field)
    await show_edit_menu(message, state, song_service)


@router.message(FSMAdmin.edit_song_media, F.video)
async def process_edit_media_video(message: Message, state: FSMContext, song_service: SongService):
    video = cast(Video, message.video)
    data = await state.get_data()
    song_id = int(data["song_id"])

    updated = await song_service.update(song_id=song_id, file_id=video.file_id, file_type_str="video")

    if not updated:
        await message.answer("❌ Ошибка при обновлении видео")

    await state.set_state(FSMAdmin.edit_song_select_field)
    await show_edit_menu(message, state, song_service)


@router.message(FSMAdmin.edit_song_media, F.audio)
async def process_edit_media_audio(message: Message, state: FSMContext, song_service: SongService):
    audio = cast(Audio, message.audio)
    data = await state.get_data()
    song_id = int(data["song_id"])

    updated = await song_service.update(song_id=song_id, file_id=audio.file_id, file_type_str="audio")

    if not updated:
        await message.answer("❌ Ошибка при обновлении аудио")

    await state.set_state(FSMAdmin.edit_song_select_field)
    await show_edit_menu(message, state, song_service)


@router.callback_query(FSMAdmin.edit_song_select_field, F.data == "edit_exit")
async def exit_editing(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    title = data.get("current_title", "песни")

    await state.clear()
    await callback.message.answer(  # type: ignore
        f"✅ Редактирование «{title}» завершено",
    )
    await handle_admin_panel(callback.message, state)
    await callback.answer()


@router.callback_query(F.data == "edit_cancel")
async def cancel_editing(callback: CallbackQuery, state: FSMContext, song_service: SongService):
    await state.set_state(FSMAdmin.edit_song_select_field)
    await show_edit_menu(callback.message, state, song_service)  # type: ignore
    await callback.answer("🚫 Редактирование отменено")
    await callback.message.delete()  # type: ignore


"""User history handlers"""

PAGE_SIZE = 20


@router.message(F.text == "📜 История пользователя")
async def admin_request_history(message: Message, state: FSMContext, user_service: UserService):
    await state.clear()
    await state.set_state(FSMAdmin.enter_username)

    users = await user_service.get()
    users_text = "\n".join([f"👤 @{u.username} (ID: {u.id})" for u in users])

    await message.answer(
        f"📜 Введите ID пользователя или его username, чтобы получить историю просмотров:\n\n"
        f"<b>Список пользователей:</b>\n{users_text}",
        reply_markup=CancelKeyboard()(),
        parse_mode="HTML",
    )


@router.message(FSMAdmin.enter_username)
async def admin_process_username(
    message: Message,
    state: FSMContext,
    user_service: UserService,
):
    identifier = str(message.text).strip().lstrip("@")
    user = await user_service.get_by_username(identifier)
    if not user:
        user = await user_service.get_one(identifier)
    if not user:
        await message.answer("❌ Пользователь не найден. Попробуйте ещё раз или /cancel.")
        return

    await state.update_data(
        target_user_id=str(user.id),
        target_username=user.username,
        history_page=0,
    )
    await show_history_page(message, state, user_service)


async def show_history_page(msg: Message | CallbackQuery, state: FSMContext, user_service: UserService):
    data = await state.get_data()
    user_id = data["target_user_id"]
    username = data["target_username"]
    page = data["history_page"]

    history = await user_service.get_history(user_id)
    total = len(history)
    pages = math.ceil(total / PAGE_SIZE)

    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    chunk = history[::-1][start:end]

    lines = []
    for rec in chunk:
        action_fixed = f"{rec.action:<6}"
        ts_str = rec.viewed_at.strftime("%d.%m.%Y %H:%M")
        lines.append(f"{ts_str} — <i>{action_fixed}</i> — <b>{rec.song_title}</b>")

    header = f"📜 <b>История @{username}</b> " f"({start+1}–{min(end, total)} из {total}):\n\n"
    text = header + "\n".join(lines)

    cart_items = await user_service.get_wishlist(user_id)

    if cart_items:
        cart_text = "\n".join([f"🛒 {item.title}" for item in cart_items])
        text += f"\n\n<b>Корзина:</b>\n{cart_text}"
    else:
        text += "\n\n<b>Корзина пуста.</b>"

    # Кнопки навигации
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data="history:prev"))
    if page < pages - 1:
        nav_row.append(InlineKeyboardButton(text="➡️ Далее", callback_data="history:next"))
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            nav_row,
            [InlineKeyboardButton(text="📥 Экспорт CSV", callback_data="history:export")],
            [InlineKeyboardButton(text="🏠 В админ-панель", callback_data="admin:panel")],
        ],
    )

    if isinstance(msg, CallbackQuery):
        await msg.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")  # type: ignore
        await msg.answer()
    else:
        await msg.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "history:export")
async def history_export(callback: CallbackQuery, state: FSMContext, user_service: UserService):
    data = await state.get_data()
    user_id = data["target_user_id"]
    username = data["target_username"]

    history = (await user_service.get_history(user_id))[::-1]

    # Создаём CSV в памяти
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Timestamp", "Action", "Song Title"])
    for rec in history:
        ts = rec.viewed_at.strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([ts, rec.action, rec.song_title])
    csv_text = buffer.getvalue().encode("utf-8")  # bytes

    file = BufferedInputFile(csv_text, filename=f"history_{username}.csv")

    await callback.message.answer_document(  # type: ignore
        document=file,
        caption=f"Экспорт истории @{username}",
    )
    await callback.answer("Файл CSV отправлен")


@router.callback_query(F.data == "history:prev")
async def history_prev(callback: CallbackQuery, state: FSMContext, user_service: UserService):
    data = await state.get_data()
    await state.update_data(history_page=data["history_page"] - 1)
    await show_history_page(callback, state, user_service)


@router.callback_query(F.data == "history:next")
async def history_next(callback: CallbackQuery, state: FSMContext, user_service: UserService):
    data = await state.get_data()
    await state.update_data(history_page=data["history_page"] + 1)
    await show_history_page(callback, state, user_service)


@router.callback_query(F.data == "admin:panel")
async def history_back(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    await handle_admin_panel(callback.message, state)
    await callback.message.delete()  # type: ignore


__all__ = ["router"]
