from logging import Logger
from typing import Optional

from sqlalchemy.exc import IntegrityError, NoResultFound

from models import Song, SongHistory, User
from repository import SongHistoryRepository, UserRepository, WishlistRepository


class UserService:
    """User Service class"""

    def __init__(
        self,
        repository: UserRepository,
        wish_repo: WishlistRepository,
        history_repo: SongHistoryRepository,
        logger: Logger,
    ):
        self.repo = repository
        self.wish_repo = wish_repo
        self.history_repo = history_repo
        self.log = logger

    async def create(self, id: str, username: str, is_staff: bool = False) -> str:
        try:
            return await self.repo.create(user_id=id, username=username, is_staff=is_staff)
        except IntegrityError as e:
            self.log.warning("UserRepository: %s" % e)
        except Exception as e:
            self.log.error("UserRepository: %s" % e)
        return "-1"

    async def get_one(self, id: str) -> Optional[User]:
        try:
            return await self.repo.get_one(id)
        except NoResultFound as e:
            self.log.warning("UserRepository: %s" % e)
        except Exception as e:
            self.log.error("UserRepository: %s" % e)
        return None

    async def get_or_create(self, id: str, username: str) -> Optional[User]:
        try:
            try:
                return await self.repo.get_one(id)
            except NoResultFound:
                try:
                    id = await self.create(id, username)
                    return await self.repo.get_one(id)
                except Exception as e:
                    self.log.error("UserRepository: %s" % e)
            return None

        except IntegrityError as e:
            self.log.warning("UserRepository: %s" % e)
        except Exception as e:
            self.log.error("UserRepository: %s" % e)
        return None

    async def get_by_username(self, username: str) -> Optional[User]:
        try:
            return await self.repo.get_by_username(username)
        except NoResultFound as e:
            self.log.warning("UserRepository: %s" % e)
        except Exception as e:
            self.log.error("UserRepository: %s" % e)
        return None

    async def get(self) -> list[User]:
        try:
            return await self.repo.get()
        except Exception as e:
            self.log.error("UserRepository: %s" % e)
        return []

    async def update_username(self, id: str, username: str) -> Optional[User]:
        try:
            return await self.repo.update_username(id, username)
        except NoResultFound as e:
            self.log.warning("UserRepository: %s" % e)
        except Exception as e:
            self.log.error("UserRepository: %s" % e)
        return None

    async def update_role(self, id: str, is_staff: bool) -> Optional[User]:
        try:
            return await self.repo.update_role(id, is_staff)
        except NoResultFound as e:
            self.log.warning("UserRepository: %s" % e)
        except Exception as e:
            self.log.error("UserRepository: %s" % e)
        return None

    async def is_admin(self, id: str) -> bool:
        try:
            user = await self.repo.get_one(id)
            if not user:
                raise NoResultFound(f"User with id={id} does not exist")
            return user.is_staff
        except NoResultFound as e:
            self.log.warning("UserRepository: %s" % e)
        except Exception as e:
            self.log.error("UserRepository: %s" % e)
        return False

    async def is_super_admin(self, id: str) -> bool:
        try:
            user = await self.repo.get_one(id)
            if not user:
                raise NoResultFound(f"User with id={id} does not exist")
            return user.is_superuser
        except NoResultFound as e:
            self.log.warning("UserRepository: %s" % e)
        except Exception as e:
            self.log.error("UserRepository: %s" % e)
        return False

    async def add_to_wishlist(self, user_id: str, song_id: int) -> bool:
        try:
            await self.wish_repo.add(user_id, song_id)
            return True
        except IntegrityError as e:
            self.log.warning("WishlistRepository: %s", e)
        except Exception as e:
            self.log.error("WishlistRepository: %s", e)
        return False

    async def get_wishlist(self, user_id: str) -> list[Song]:
        try:
            return await self.repo.get_wishlist(user_id)
        except Exception as e:
            self.log.error("WishlistRepository: %s", e)
        return []

    async def remove_from_wishlist(self, user_id: str, song_id: int) -> bool:
        try:
            await self.wish_repo.remove(user_id, song_id)
            return True
        except Exception as e:
            self.log.error("WishlistRepository: %s", e)
        return False

    async def log_view(self, user_id: str, song_title: str, action: str = "view") -> Optional[int]:
        try:
            return await self.history_repo.log(user_id, song_title, action)
        except Exception as e:
            self.log.error("SongHistoryRepository: %s", e)
            return None

    async def get_history(self, user_id: str) -> list[SongHistory]:
        try:
            return await self.repo.get_history(user_id)
        except Exception as e:
            self.log.error("SongHistoryRepository: %s", e)
        return []


__all__ = ["UserService"]
