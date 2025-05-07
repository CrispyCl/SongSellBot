from typing import cast

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, Video

from filters import IsAdminFilter
from fsm import FSMAdmin
from keyboards import AcceptCancelKeyboard, AdminPanelKeyboard, CancelKeyboard
from models import SongTempo, SongType, User
from service import GenreService, SongService

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


@router.message(F.text == "🎵 Добавить песню")
async def start_create_song(message: Message, state: FSMContext):
    await state.set_state(FSMAdmin.enter_title)
    await message.answer("🎶 Введите название песни:", reply_markup=CancelKeyboard()())


@router.message(FSMAdmin.enter_title)
async def process_title(message: Message, state: FSMContext):
    if len(str(message.text)) > 150:
        await message.answer("❌ Слишком длинное название (макс. 150 символов)")
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
        "🎥 Загрузите видеофайл песни (MP4/MPEG4):\n" "Или нажмите 'Пропустить' чтобы добавить позже",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="⏭ Пропустить", callback_data="skip_video")]],
        ),
    )


# Добавляем обработчик для видео
@router.message(FSMAdmin.upload_video, F.video)
async def process_video(message: Message, state: FSMContext):
    video = cast(Video, message.video)

    await state.update_data(video_id=video.file_id)
    await handle_confirmation(message, state)


@router.callback_query(FSMAdmin.upload_video, F.data == "skip_video")
async def skip_video(callback: CallbackQuery, state: FSMContext):
    await state.update_data(video_id=None)
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
        f"🎥 Видео: {'добавлено' if data.get('video_id') else 'отсутствует'}"
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
        file_id=data.get("video_id"),
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


__all__ = ["router"]
