from typing import Any, Sequence

from sqlalchemy import select, delete
from sqlalchemy.orm import load_only, noload

from core.schemas import PaginationResultModel
from database.mixins import PaginationMixin, CRUDMixin
from database.models import (
    Profile,
    Channel,
    ProfileChannelAssociation,
    Video,
    Stream,
)
from database.tps import Status


class ProfileDatabase(PaginationMixin):
    __table__ = Profile

    async def get_by_tg_id(
        self, tg_id: int, options: list | None = None
    ) -> Profile | None:
        if options is None:
            options = []

        where = [Profile.tg_id == tg_id]

        options.extend(
            [
                load_only(
                    Profile.id,
                    Profile.tg_id,
                    Profile.first_name,
                    Profile.username,
                    Profile.status,
                ),
                noload(Profile.channel_associations),
            ],
        )

        stmt = select(Profile).options(*options).where(*where).limit(1)
        result = await self.async_session.scalar(stmt)
        await self.async_session.commit()
        return result

    async def get(
        self,
        where: Any | None = None,
        options: list | None = None,
        page: int = 1,
        limit: int | None = None,
        order_by: Any | None = None,
    ) -> PaginationResultModel:
        if where is None:
            where = []

        if order_by is None:
            order_by = Profile.auth_timestamp.desc()

        if options is None:
            options = [
                load_only(
                    Profile.id,
                    Profile.first_name,
                    Profile.status,
                ),
                noload(Profile.channel_associations),
            ]

        stmt = select(self.__table__).options(*options).where(*where)
        return await self.paginated_result(
            stmt, page=page, limit=limit, order_by=order_by
        )


class ChannelsDatabase(PaginationMixin):
    __table__ = Channel

    async def get_user_channels(self, tg_id: int) -> Sequence[Channel]:
        where = [Profile.tg_id == tg_id]

        options = [
            load_only(Channel.id, Channel.name, Channel.url)
            .selectinload(Channel.profile_associations)
            .joinedload(ProfileChannelAssociation.profile)
            .load_only(Profile.id, Profile.tg_id)
            .noload(Profile.channel_associations)
        ]

        stmt = (
            select(Channel)
            .join(ProfileChannelAssociation)
            .join(Profile)
            .options(*options)
            .where(*where)
            .order_by(Channel.name)
        )
        result = await self.async_session.scalars(stmt)
        await self.async_session.commit()
        return result.all()

    async def get_by_url(self, url: str) -> Channel | None:
        where = [Channel.url == url or Channel.canonical_url == url]

        options = [
            load_only(Channel.id, Channel.name, Channel.url, Channel.canonical_url),
            noload(Channel.profile_associations),
        ]
        stmt = (
            select(Channel)
            .options(*options)
            .where(*where)
            .order_by(Channel.name)
            .limit(1)
        )
        result = await self.async_session.scalar(stmt)
        await self.async_session.commit()
        return result

    async def get(
        self,
        where: Any | None = None,
        options: list | None = None,
        page: int = 1,
        limit: int | None = None,
    ) -> PaginationResultModel:
        if where is None:
            where = []

        if options is None:
            options = [
                load_only(
                    Channel.id,
                    Channel.url,
                    Channel.canonical_url,
                    Channel.name,
                )
                .selectinload(Channel.profile_associations)
                .joinedload(ProfileChannelAssociation.profile)
                .load_only(Profile.id, Profile.tg_id, Profile.status)
                .noload(Profile.channel_associations),
            ]

        where.append(Profile.status == Status.active)

        stmt = (
            select(Channel)
            .join(ProfileChannelAssociation)
            .join(Profile)
            .options(*options)
            .where(*where)
        )

        return await self.paginated_result(stmt, page=page, limit=limit)


class VideoDatabase(PaginationMixin):
    __table__ = Video

    async def get(
        self,
        channel_id: int,
        page: int = 1,
        limit: int | None = None,
    ) -> PaginationResultModel:
        where = [Video.channel_id == channel_id]

        options = [
            load_only(Video.id, Video.url, Video.channel_id),
            noload(Video.channel),
        ]
        stmt = (
            select(Video)
            .options(*options)
            .where(*where)
            .order_by(Video.id.desc())
            .limit(limit)
        )
        return await self.paginated_result(stmt, page=page, limit=limit)


class StreamDatabase(PaginationMixin):
    __table__ = Stream

    async def get(
        self,
        channel_id: int,
        page: int = 1,
        limit: int | None = None,
    ) -> PaginationResultModel:
        where = [Stream.channel_id == channel_id]

        options = [
            load_only(Stream.id, Stream.url, Stream.channel_id),
            noload(Stream.channel),
        ]
        stmt = (
            select(Stream)
            .options(*options)
            .where(*where)
            .order_by(Stream.id.desc())
            .limit(limit)
        )
        return await self.paginated_result(stmt, page=page, limit=limit)


class ProfileChannelAssociationDatabase(CRUDMixin):
    __table__ = ProfileChannelAssociation

    async def delete(
        self,
        association_id: int | None = None,
        profile_id: int | None = None,
        channel_id: int | None = None,
    ) -> bool:
        if association_id:
            where = [ProfileChannelAssociation.id == association_id]
        elif profile_id and channel_id:
            where = [
                ProfileChannelAssociation.profile_id == profile_id,
                ProfileChannelAssociation.channel_id == channel_id,
            ]
        else:
            raise ValueError("Must be 'association_id' or 'profile_id' + 'channel_id'")

        stmt = delete(ProfileChannelAssociation).where(*where)
        result = await self.async_session.execute(stmt)
        await self.async_session.commit()
        return bool(result.rowcount)
