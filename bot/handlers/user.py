from io import BytesIO
import urllib.parse

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from fsm import FSMUser
from keyboards import ToMainMenu
from models import SongTempo, SongType, User
from service import GenreService, SongService, UserService

router = Router()

TypeRus = {
    SongType.universal.value: "Универсальная",
    SongType.male.value: "Мужская",
    SongType.female.value: "Женская",
    SongType.duet.value: "Дуэт",
    SongType.children.value: "Детская",
    "Универсальная": SongType.universal.value,
    "Мужская": SongType.male.value,
    "Женская": SongType.female.value,
    "Дуэт": SongType.duet.value,
    "Детская": SongType.children.value,
}

TempoRus = {
    SongTempo.dance.value: "Танцевальная",
    SongTempo.mid_tempo.value: "Среднетемповая",
    SongTempo.slow.value: "Медленная",
    "Танцевальная": SongTempo.dance.value,
    "Среднетемповая": SongTempo.mid_tempo.value,
    "Медленная": SongTempo.slow.value,
}


@router.message(F.text == "🎵 Каталог песен")
@router.message(Command("catalog"))
async def cmd_catalog(message: Message, state: FSMContext, song_service: SongService, bot: Bot):
    await state.clear()
    await state.set_state(FSMUser.music_list)

    await message.answer(
        "<b>🎵Добро пожаловать в каталог песен!</b>\n\n<i>Желаю, чтобы среди моих песен вы нашли ту единственную, "
        "что станет отражением вашей души и вашим главным хитом! ✨</i>",
        reply_markup=ToMainMenu()(),
    )

    song_count_by_type: list[tuple[SongType, int]] = []
    for song_type in SongType:
        songs = await song_service.get_by_filter(type_str=song_type.value, tempo_str=None, genre_titles=None)
        song_count_by_type.append((song_type, len(songs)))

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{TypeRus[t.value]} ({count} шт.)",  # Добавляем количество песен
                    callback_data=f"type:{t.value}",
                ),
            ]
            for t, count in song_count_by_type
        ],
    )
    text = (
        "Каждая из этих композиций это готовая история, которая ждёт своего исполнителя. Вам осталось лишь выбрать, "
        "кто её расскажет.\n\n"
        "<b>Выберите категорию:</b>\n\n"
        "· 👨‍🎤 <b>Для мужского исполнения</b>\n"
        "· 👩‍🎤 <b>Для женского исполнения</b>\n"
        "· 👥 <b>Дуэтные композиции</b> - для яркого вокального диалога\n"
        "· 🔄 <b>Универсальные песни</b> - подходят для любого вокалиста\n"
        "· 👶 <b>Детские композиции</b>\n\n"
        "Найдите свою идеальную песню - ту, что станет саундтреком вашего успеха! Пусть в ней бьётся сердце нашего "
        "совместного творчества и зазвучит ваш уникальный голос. 🎵\n\n"
        "🎵 <b>Ваша песня ждёт вас! Сделайте свой выбор и дайте ей прозвучать!</b>"
    )
    await bot.send_message(message.chat.id, text, reply_markup=keyboard)


@router.callback_query(FSMUser.music_list, F.data.startswith("type:"))
async def on_type(callback: CallbackQuery, state: FSMContext):
    type_str = str(callback.data).split(":", 1)[1]
    await state.update_data(type_str=type_str)
    # Дальше: слушать все или фильтровать
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Послушать все", callback_data="action:all")],
            [InlineKeyboardButton(text="🎧 Выбрать темп и жанр", callback_data="action:filter")],
            [InlineKeyboardButton(text="↩️ Изменить тип", callback_data="nav:type")],
        ],
    )
    type_to_text = {
        SongType.universal.value: (
            "Теперь вы можете:\n\n"
            "🎵 <b>Прослушать все универсальные песни</b>\n"
            "- Чтобы сразу познакомиться со всей коллекцией\n\n"
            "⚙ Или настроить поиск точнее\n"
            "- Перейти к выбору темпа и жанра песни, чтобы найти идеальное сочетание\n\n"
            "<b>Выбирайте способ, который вам удобен и пусть ваша идеальная песня найдётся быстрее! 🚀</b>"
        ),
        SongType.male.value: (
            "Теперь вы можете:\n\n"
            "🎵 <b>Прослушать все мужские песни</b>\n"
            "- Чтобы сразу познакомиться с полной коллекцией\n\n"
            "⚙ Или настроить поиск точнее\n"
            "- Перейти к выбору темпа и жанра для идеального результата\n\n"
            "<b>Выбирайте подходящий вариант и пусть поиск будет быстрым, а результат - идельным! 🎶</b>"
        ),
        SongType.female.value: (
            "Теперь вы можете:\n\n"
            "🎵 <b>Прослушать все женские песни</b>\n"
            "- Чтобы сразу познакомиться с полной коллекцией\n\n"
            "⚙ Или настроить поиск точнее\n"
            "- Перейти к выбору темпа и жанра для идеального результата\n\n"
            "<b>Выбирайте удобный способ и пусть ваша идеальная песня найдётся легко и быстро! ✨</b>"
        ),
        SongType.duet.value: (
            "Теперь вы можете:\n\n"
            "🎵 <b>Прослушать все дуэты</b>\n"
            "- Чтобы сразу познакомиться с полной коллекцией\n\n"
            "⚙ Или настроить поиск точнее\n"
            "- Перейти к выбору темпа и жанра для идеального результата\n\n"
            "<b>Выбирайте удобный способ и найдите ту самую композицию, которая раскроет всю мощь дуэта!🎤✨</b>"
        ),
        SongType.children.value: (
            "Теперь вы можете:\n\n"
            "🎵 <b>Прослушать все детские песни</b>\n"
            "- Чтобы окунуться в мир добрых мелодий и искренних историй\n\n"
            "⚙ Или настроить поиск бережнее\n"
            "- Подобрать идеальный темп и жанр для юного исполнителя\n\n"
            "<b>Выбирайте с душой и помогите детскому таланту найти своё первое большое звучание!🌟</b>"
        ),
    }

    await callback.message.edit_text(type_to_text[type_str], reply_markup=keyboard)  # type: ignore
    await callback.answer()


@router.callback_query(FSMUser.music_list, F.data == "action:all")
async def on_all(
    callback: CallbackQuery,
    state: FSMContext,
    song_service: SongService,
    user_service: UserService,
    current_user: User,
):
    data = await state.get_data()
    songs = await song_service.get_by_filter(data["type_str"], None, None)
    if not songs:
        await callback.message.edit_text("😔 Песен данного типа не найдено.")  # type: ignore
        await cmd_catalog(callback.message, state, song_service)
        return
    ids = list(dict.fromkeys(s.id for s in songs))
    await state.update_data(songs_list=ids, index=0)
    await send_current(callback.message, state, song_service, user_service, current_user)
    await callback.answer()
    await callback.message.delete()  # type: ignore


@router.callback_query(FSMUser.music_list, F.data == "action:filter")
async def on_filter(callback: CallbackQuery, state: FSMContext, song_service: SongService):
    data = await state.get_data()
    type_str = data.get("type_str")

    if not type_str:
        await callback.answer("Сначала выберите тип песни", show_alert=True)
        return

    await state.update_data(tempo_str=None, genre=None, genre_list=[])
    # Выбор темпа
    buttons = []
    for t in SongTempo:
        songs = await song_service.get_by_filter(type_str=type_str, tempo_str=t.value, genre_titles=None)
        buttons.append(
            [InlineKeyboardButton(text=f"{TempoRus[t.value]} ({len(songs)} шт.)", callback_data=f"tempo:{t.value}")],
        )
    buttons.append([InlineKeyboardButton(text="↩️ Назад", callback_data=f"type:{type_str}")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text("Определись в каком темпе нужна песня", reply_markup=keyboard)  # type: ignore
    await callback.answer()


@router.callback_query(FSMUser.music_list, F.data.startswith("tempo:"))
async def on_tempo(callback: CallbackQuery, state: FSMContext, genre_service: GenreService, song_service: SongService):
    tempo_str = str(callback.data).split(":", 1)[1]
    await state.update_data(tempo_str=tempo_str)
    data = await state.get_data()
    selected: list[str] = data.get("genre_list", [])

    genres = await genre_service.get_by_type_and_tempo(type_str=data["type_str"], tempo_str=tempo_str)
    if not genres:
        await callback.message.edit_text("😔 Жанров под данный темп и тип не найдено.")  # type: ignore
        await cmd_catalog(callback.message, state, song_service)
        return

    buttons = []
    for g in genres:
        songs = await song_service.get_by_filter(type_str=data["type_str"], tempo_str=tempo_str, genre_titles=[g.title])
        text = ("✅ " if g.title in selected else "") + f"{g.title} ({len(songs)} шт.)"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"genre:{g.title}")])
    if selected:
        buttons.append([InlineKeyboardButton(text="✅ Готово", callback_data="genre:done")])
    buttons.append([InlineKeyboardButton(text="↩️ Изменить темп", callback_data="action:filter")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    text = (
        "Отлично остался последний шаг- выбери жанр песни и нажми ГОТОВО ✅  Слушай подборку из демо треков. "
        "Те что тебе понравятся - добавляй в список желаемого, что бы не потерять или сразу жми «Хочу эту песню»"
    )
    await callback.message.edit_text(text, reply_markup=keyboard)  # type: ignore
    await callback.answer()


@router.callback_query(FSMUser.music_list, F.data == "genre:done")
async def on_genre_done(
    callback: CallbackQuery,
    state: FSMContext,
    song_service: SongService,
    user_service: UserService,
    current_user: User,
):
    data = await state.get_data()
    genres: list[str] = data.get("genre_list", [])
    if not genres:
        await callback.answer("Сначала выберите хотя бы один жанр", show_alert=True)
        return

    songs = await song_service.get_by_filter(data["type_str"], data["tempo_str"], [g.lower() for g in genres])
    if not songs:
        await callback.message.edit_text("😔 Песен по данному фильтру не найдено.")  # type: ignore
        await cmd_catalog(callback.message, state, song_service)
        return

    ids = list(dict.fromkeys(s.id for s in songs))
    await state.update_data(songs_list=ids, index=0)
    await send_current(callback.message, state, song_service, user_service, current_user)
    await callback.answer()
    await callback.message.delete()  # type: ignore


@router.callback_query(FSMUser.music_list, F.data.startswith("genre:"))
async def on_genre_toggle(
    callback: CallbackQuery,
    state: FSMContext,
    genre_service: GenreService,
    song_service: SongService,
):
    genre_title = str(callback.data).split(":", 1)[1]
    data = await state.get_data()
    selected: list[str] = data.get("genre_list", [])

    if genre_title in selected:
        selected.remove(genre_title)
    elif len(selected) < 3:
        selected.append(genre_title)
    else:
        await callback.answer("Можно выбрать не более 3 жанров.")
        return

    await state.update_data(genre_list=selected)

    genres = await genre_service.get_by_type_and_tempo(type_str=data["type_str"], tempo_str=data["tempo_str"])
    if not genres:
        await callback.message.edit_text("😔 Жанров под данный темп и тип не найдено.")  # type: ignore
        await cmd_catalog(callback.message, state, song_service)
        return

    buttons = []
    for g in genres:
        songs = await song_service.get_by_filter(
            type_str=data["type_str"],
            tempo_str=data["tempo_str"],
            genre_titles=[g.title],
        )
        text = ("✅ " if g.title in selected else "") + f"{g.title} ({len(songs)} шт.)"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"genre:{g.title}")])
    if selected:
        buttons.append([InlineKeyboardButton(text="✅ Готово", callback_data="genre:done")])
    buttons.append([InlineKeyboardButton(text="↩️ Изменить темп", callback_data="action:filter")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_reply_markup(reply_markup=keyboard)  # type: ignore
    await callback.answer(f"Выбрано: {len(selected)} из 3")


@router.callback_query(FSMUser.music_list, F.data == "nav:prev")
async def nav_prev(
    callback: CallbackQuery,
    state: FSMContext,
    song_service: SongService,
    user_service: UserService,
    current_user: User,
):
    data = await state.get_data()
    idx = (data["index"] - 1) % len(data["songs_list"])
    await state.update_data(index=idx)
    await send_current(callback.message, state, song_service, user_service, current_user)
    await callback.answer()
    await callback.message.delete()  # type: ignore


@router.callback_query(FSMUser.music_list, F.data == "nav:next")
async def nav_next(
    callback: CallbackQuery,
    state: FSMContext,
    song_service: SongService,
    user_service: UserService,
    current_user: User,
):
    data = await state.get_data()
    idx = (data["index"] + 1) % len(data["songs_list"])
    await state.update_data(index=idx)
    await send_current(callback.message, state, song_service, user_service, current_user)
    await callback.answer()
    await callback.message.delete()  # type: ignore


@router.callback_query(FSMUser.music_list, F.data == "nav:type")
async def nav_type(callback: CallbackQuery, state: FSMContext, song_service: SongService):
    await state.update_data(type_str=None, tempo_str=None, genre=None, genre_list=[])

    song_count_by_type = []
    for song_type in SongType:
        songs = await song_service.get_by_filter(type_str=song_type.value, tempo_str=None, genre_titles=None)
        song_count_by_type.append((song_type, len(songs)))

    buttons = [
        [
            InlineKeyboardButton(
                text=f"{TypeRus[t.value]} ({count} шт.)",  # Добавляем количество песен
                callback_data=f"type:{t.value}",
            ),
        ]
        for t, count in song_count_by_type
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.answer(  # type: ignore
        "Выбери для кого нужна песня.\n\n"
        "Универсальные предназначены по тексту и для женского и для мужского исполнения ‼",
        reply_markup=keyboard,
    )
    await callback.answer()
    await callback.message.delete()  # type: ignore


@router.callback_query(FSMUser.music_list, F.data == "nav:tempo")
async def nav_tempo(callback: CallbackQuery, state: FSMContext, song_service: SongService):
    data = await state.get_data()
    type_str = data.get("type_str")
    if not type_str:
        await callback.answer("Сначала выберите тип песни", show_alert=True)
        return

    await state.update_data(tempo_str=None, genre=None, genre_list=[])

    buttons = []
    for t in SongTempo:
        songs = await song_service.get_by_filter(type_str=type_str, tempo_str=t.value, genre_titles=None)
        buttons.append(
            [InlineKeyboardButton(text=f"{TempoRus[t.value]} ({len(songs)} шт.)", callback_data=f"tempo:{t.value}")],
        )
    buttons.append([InlineKeyboardButton(text="↩️ Назад", callback_data=f"type:{type_str}")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer("Определись в каком темпе нужна песня", reply_markup=keyboard)  # type: ignore
    await callback.answer()
    await callback.message.delete()  # type: ignore


@router.callback_query(FSMUser.music_list, F.data == "nav:genre")
async def nav_genre(callback: CallbackQuery, state: FSMContext, genre_service: GenreService, song_service: SongService):
    data = await state.get_data()
    if not data.get("tempo_str"):
        await callback.answer("Сначала выберите темп песни", show_alert=True)
        return
    selected: list[str] = data.get("genre_list", [])

    genres = await genre_service.get_by_type_and_tempo(type_str=data["type_str"], tempo_str=data["tempo_str"])
    if not genres:
        await callback.message.edit_text("😔 Жанров под данный темп и тип не найдено.")  # type: ignore
        await cmd_catalog(callback.message, state, song_service)
        return

    buttons = []
    for g in genres:
        songs = await song_service.get_by_filter(
            type_str=data["type_str"],
            tempo_str=data["tempo_str"],
            genre_titles=[g.title],
        )
        text = ("✅ " if g.title in selected else "") + f"{g.title} ({len(songs)} шт.)"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"genre:{g.title}")])
    if selected:
        buttons.append([InlineKeyboardButton(text="✅ Готово", callback_data="genre:done")])
    buttons.append([InlineKeyboardButton(text="↩️ Изменить темп", callback_data="action:filter")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    text = (
        "Отлично остался последний шаг- выбери жанр песни и нажми ГОТОВО ✅  Слушай подборку из демо треков. "
        "Те что тебе понравятся - добавляй в список желаемого, что бы не потерять или сразу жми «Хочу эту песню»"
    )
    await callback.message.answer(text, reply_markup=keyboard)  # type: ignore
    await callback.answer()
    await callback.message.delete()  # type: ignore


@router.callback_query(FSMUser.music_list, F.data == "nav:like")
async def nav_like(
    callback: CallbackQuery,
    state: FSMContext,
    song_service: SongService,
    user_service: UserService,
    current_user: User,
):
    data = await state.get_data()
    song_id = data["songs_list"][data["index"]]
    song = await song_service.get_one(song_id)
    if not song:
        await callback.message.answer("🔎 Песня не найдена")  # type: ignore
        await cmd_catalog(callback.message, state, song_service)
        return
    await user_service.add_to_wishlist(current_user.id, song_id)
    await user_service.log_view(
        current_user.id,
        song.title,
        "like",
    )
    await callback.answer("🛒 Добавлено в список желаемого")


async def send_current(
    msg_obj,
    state: FSMContext,
    song_service: SongService,
    user_service: UserService,
    current_user: User,
):
    data = await state.get_data()
    song_id = data["songs_list"][data["index"]]
    song = await song_service.get_one(song_id)
    if not song:
        await msg_obj.answer("🔎 Песня не найдена")
        await cmd_catalog(msg_obj, state, song_service)
        return

    await user_service.log_view(current_user.id, song.title)

    current_pos = data["index"] + 1
    total_songs = len(data["songs_list"])
    position_info = f"📌 {current_pos} из {total_songs}\n\n"

    text = (
        f"🎵 <b>{song.title}</b>\n\n"
        f"<b>Тип:</b> {TypeRus[song.type.value].capitalize()}\n"
        f"<b>Темп:</b> {TempoRus[song.tempo.value].replace('_', ' ').capitalize()}\n"
        f"<b>Жанры:</b> " + ", ".join(f"<i>#{g.title}</i>" for g in song.genres) + "\n\n"
        f"{position_info}"
    )

    support_text = (
        f"Здравствуйте! Я хочу приобрести песню:\n\n"
        f'🎵 "{song.title}"\n'
        f"Тип: {TypeRus[song.type.value]}\n"
        f"Темп: {TempoRus[song.tempo.value].replace('_', ' ')}\n"
        f"Жанры: " + ", ".join(f"#{g.title}" for g in song.genres)
    )

    # Кодируем текст для URL

    encoded_text = urllib.parse.quote(support_text)
    support_url = f"https://t.me/MusicCompanyIraEuphoria?text={encoded_text}"

    btns = [InlineKeyboardButton(text="🛒 В список желаемого", callback_data="nav:like")]
    if song.lyrics:
        btns.insert(0, InlineKeyboardButton(text="📄 Читать текст", callback_data="download:lyrics"))

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️ Предыдущая", callback_data="nav:prev"),
                InlineKeyboardButton(text="➡️ Следующая", callback_data="nav:next"),
            ],
            [
                InlineKeyboardButton(text="🎧 Темп", callback_data="nav:tempo"),
                InlineKeyboardButton(text="🎭 Жанр", callback_data="nav:genre"),
                InlineKeyboardButton(text="🎤 Тип", callback_data="nav:type"),
            ],
            btns,
            [InlineKeyboardButton(text="💬 Хочу эту песню!", url=support_url)],
            [InlineKeyboardButton(text="🏠 На главную", callback_data="to_main")],
        ],
    )

    if song.file_id:
        await msg_obj.answer_video(song.file_id, caption=text, reply_markup=keyboard)
    else:
        await msg_obj.answer(text, reply_markup=keyboard)


@router.callback_query(lambda c: c.data == "download:lyrics")
async def handle_download_lyrics(callback: CallbackQuery, state: FSMContext, song_service: SongService):
    data = await state.get_data()
    index = data.get("index")
    song_id = data["songs_list"][index]
    song = await song_service.get_one(song_id)

    if not song or not song.lyrics:
        await callback.message.answer("🔇 Текст отсутствует")  # type: ignore
        await callback.answer()
        return

    # Создание временного файла
    file_content = song.lyrics
    file_name = f"{song.title}.txt"

    byte_stream = BytesIO(file_content.encode("utf-8"))
    file = BufferedInputFile(byte_stream.read(), filename=file_name)

    await callback.message.answer_document(document=file, caption=f"📄 Текст песни: <b>{song.title}</b>")  # type: ignore
    await callback.answer()


"""Wishlist handlers"""


@router.message(F.text == "🛒 Желаемые песни")
@router.message(Command("wishlist"))
async def cmd_wishlist(
    message: Message,
    state: FSMContext,
    song_service: SongService,
    user_service: UserService,
    current_user: User,
):
    await state.clear()
    await state.set_state(FSMUser.music_list)

    songs = await user_service.get_wishlist(current_user.id)
    if not songs:
        return await message.answer("🧺 Ваш список желаемого пуст.", reply_markup=ToMainMenu()())

    await message.answer("🧺 Ваш список желаемого:", reply_markup=ToMainMenu()())
    ids = list(dict.fromkeys(s.id for s in songs))
    await state.update_data(songs_list=ids, index=0, in_wishlist=True)
    return await send_wishlist_current(
        message,
        state,
        song_service=song_service,
    )


# Навигация по Wishlist
@router.callback_query(FSMUser.music_list, F.data == "wish:prev")
async def wish_prev(callback: CallbackQuery, state: FSMContext, song_service: SongService):
    data = await state.get_data()
    idx = (data["index"] - 1) % len(data["songs_list"])
    await state.update_data(index=idx)
    await send_wishlist_current(
        callback.message,
        state,
        song_service=song_service,
    )
    await callback.answer()
    await callback.message.delete()  # type: ignore


@router.callback_query(FSMUser.music_list, F.data == "wish:next")
async def wish_next(callback: CallbackQuery, state: FSMContext, song_service: SongService):
    data = await state.get_data()
    idx = (data["index"] + 1) % len(data["songs_list"])
    await state.update_data(index=idx)
    await send_wishlist_current(
        callback.message,
        state,
        song_service=song_service,
    )
    await callback.answer()
    await callback.message.delete()  # type: ignore


@router.callback_query(FSMUser.music_list, F.data == "wish:remove")
async def wish_remove(
    callback: CallbackQuery,
    state: FSMContext,
    song_service: SongService,
    user_service: UserService,
    current_user: User,
):
    data = await state.get_data()

    idx = data["index"]
    song_id = data["songs_list"][idx]
    await user_service.remove_from_wishlist(current_user.id, song_id)
    song = await song_service.get_one(song_id)
    if not song:
        await callback.message.answer("🔎 Песня не найдена")  # type: ignore
        await cmd_wishlist(callback.message, state)
        return
    await user_service.log_view(
        current_user.id,
        song.title,
        "remove",
    )

    songs_list = data["songs_list"]
    songs_list.pop(idx)
    if not songs_list:
        await state.clear()
        await callback.message.answer("🧺 Ваш список желаемого пуст.", reply_markup=ToMainMenu()())  # type: ignore
        await callback.answer()
        await callback.message.delete()  # type: ignore
        return

    new_idx = idx % len(songs_list)
    await state.update_data(songs_list=songs_list, index=new_idx)
    await send_wishlist_current(
        callback.message,
        state,
        song_service=song_service,
    )
    await callback.answer("🗑 Удалено из списка желаемого")
    await callback.message.delete()  # type: ignore


async def send_wishlist_current(msg_obj, state: FSMContext, song_service: SongService):
    data = await state.get_data()
    idx = data["index"]
    song_id = data["songs_list"][idx]
    song = await song_service.get_one(song_id)
    if not song:
        await msg_obj.answer("🔎 Песня не найдена")
        return

    current_pos = idx + 1
    total_songs = len(data["songs_list"])
    position_info = f"🛒 {current_pos} из {total_songs} в желаемом\n\n"

    text = (
        f"🎵 <b>{song.title}</b>\n\n"
        f"<b>Тип:</b> {TypeRus[song.type.value]}\n"
        f"<b>Темп:</b> {TempoRus[song.tempo.value].replace('_', ' ')}\n"
        f"<b>Жанры:</b> " + ", ".join(f"<i>#{g.title}</i>" for g in song.genres) + "\n\n"
        f"{position_info}"
    )

    support_text = (
        f"Здравствуйте! Я хочу приобрести песню:\n\n"
        f'🎵 "{song.title}"\n'
        f"Тип: {TypeRus[song.type.value]}\n"
        f"Темп: {TempoRus[song.tempo.value].replace('_', ' ')}\n"
        f"Жанры: " + ", ".join(f"#{g.title}" for g in song.genres)
    )

    # Кодируем текст для URL

    encoded_text = urllib.parse.quote(support_text)
    support_url = f"https://t.me/MusicCompanyIraEuphoria?text={encoded_text}"

    btns = [InlineKeyboardButton(text="🗑 Удалить", callback_data="wish:remove")]
    if song.lyrics:
        btns.insert(0, InlineKeyboardButton(text="📄 Читать текст", callback_data="download:lyrics"))

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️ Предыдущая", callback_data="wish:prev"),
                InlineKeyboardButton(text="➡️ Следующая", callback_data="wish:next"),
            ],
            btns,
            [InlineKeyboardButton(text="💬 Хочу эту песню!", url=support_url)],
            [InlineKeyboardButton(text="🏠 На главную", callback_data="to_main")],
        ],
    )

    if song.file_id:
        await msg_obj.answer_video(song.file_id, caption=text, reply_markup=keyboard)
    else:
        await msg_obj.answer(text, reply_markup=keyboard)


__all__ = ["router"]
